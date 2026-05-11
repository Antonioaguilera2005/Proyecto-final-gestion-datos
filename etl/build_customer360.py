import pandas as pd
import numpy as np
from sqlalchemy import text

FECHA_REFERENCIA = pd.Timestamp('2025-12-31')

def build_customer_360(engine):
    df_ventas = pd.read_sql("""
        SELECT 
            fs.customer_sk,
            dc.customer_id,
            fs.sale_id,
            fs.sale_item_id,
            fs.subtotal,
            fs.gross_margin,
            fs.is_returned,
            fs.unit_price,
            fs.quantity,
            dd.full_date
        FROM dwh.fact_sales fs
        JOIN dwh.dim_customer dc ON fs.customer_sk = dc.customer_sk
        JOIN dwh.dim_date dd ON fs.date_sk = dd.date_sk
    """, engine)

    df_returns = pd.read_sql("""
        SELECT dc.customer_sk, SUM(fr.refund_amount) AS total_refund,
               COUNT(*) AS n_returns
        FROM dwh.fact_returns fr
        JOIN dwh.fact_sales fs ON fr.sale_item_id = fs.sale_item_id
        JOIN dwh.dim_customer dc ON fs.customer_sk = dc.customer_sk
        GROUP BY dc.customer_sk
    """, engine)

    df_ventas['full_date'] = pd.to_datetime(df_ventas['full_date'])

    resumen = df_ventas.groupby(['customer_sk', 'customer_id']).agg(
        total_revenue  = ('subtotal', 'sum'),
        total_margin   = ('gross_margin', 'sum'),
        num_pedidos    = ('sale_id', 'nunique'),
        primera_compra = ('full_date', 'min'),
        ultima_compra  = ('full_date', 'max'),
        n_items        = ('sale_item_id', 'count'),
        n_returned     = ('is_returned', 'sum')
    ).reset_index()

    resumen = resumen.merge(df_returns, on='customer_sk', how='left')
    resumen['total_refund'] = resumen['total_refund'].fillna(0)
    resumen['n_returns']    = resumen['n_returns'].fillna(0)

    resumen['net_revenue']  = resumen['total_revenue'] - resumen['total_refund']
    resumen['total_cost']   = resumen['total_revenue'] - resumen['total_margin']
    resumen['net_margin']   = (resumen['total_margin'] / resumen['total_revenue']).clip(0, 1)
    resumen['return_rate']  = resumen['n_returned'] / resumen['n_items']

    resumen['lifespan_months'] = (
        (FECHA_REFERENCIA - resumen['primera_compra']).dt.days / 30.44
    ).clip(lower=1)

    resumen['purchase_frequency'] = resumen['num_pedidos'] / resumen['lifespan_months']

    # CLTV correcto: ticket_medio × margen × frecuencia_mensual × lifespan
    # Esto evita inflar multiplicando ingresos totales (que ya incluyen el tiempo)
    resumen['ticket_medio'] = resumen['net_revenue'] / resumen['num_pedidos']
    resumen['cltv'] = (
        resumen['ticket_medio'] *
        resumen['net_margin'] *
        resumen['purchase_frequency'] *
        resumen['lifespan_months']
    ).round(2).clip(lower=0)

    # RFM
    resumen['recency_days'] = (FECHA_REFERENCIA - resumen['ultima_compra']).dt.days
    resumen['frequency']    = resumen['num_pedidos']
    resumen['monetary']     = resumen['net_revenue'].round(2)

    resumen['R'] = pd.qcut(resumen['recency_days'], 5, labels=[5,4,3,2,1]).astype(int)
    resumen['F'] = pd.qcut(resumen['frequency'].rank(method='first'), 5,
                           labels=[1,2,3,4,5]).astype(int)
    resumen['M'] = pd.qcut(resumen['monetary'], 5, labels=[1,2,3,4,5]).astype(int)
    resumen['rfm_score'] = (resumen['R'].astype(str) + resumen['F'].astype(str) +
                            resumen['M'].astype(str))

    def rfm_segment(row):
        r, f, m = row['R'], row['F'], row['M']
        if r >= 4 and f >= 4 and m >= 4:   return 'Champions'
        elif r >= 3 and f >= 3:             return 'Loyal'
        elif r >= 4 and f <= 2:             return 'New Customers'
        elif r <= 2 and f >= 3:             return 'At Risk'
        elif r <= 2 and f <= 2:             return 'Lost'
        else:                               return 'Potential'

    resumen['rfm_segment'] = resumen.apply(rfm_segment, axis=1)

    # Churn
    max_recency = resumen['recency_days'].max()
    max_freq    = resumen['purchase_frequency'].max()

    resumen['churn_score'] = (
        0.40 * (resumen['recency_days'] / max_recency) +
        0.35 * (1 - resumen['purchase_frequency'] / max_freq) +
        0.25 * resumen['return_rate']
    ).clip(0, 1).round(4) * 100

    resumen['churn_label'] = pd.cut(
        resumen['churn_score'],
        bins=[0, 33, 66, 100],
        labels=['Low', 'Medium', 'High'],
        include_lowest=True
    )

    resultado = pd.DataFrame({
        'customer_sk':              resumen['customer_sk'],
        'customer_id':              resumen['customer_id'],
        'total_revenue':            resumen['total_revenue'].round(2),
        'total_cost':               resumen['total_cost'].round(2),
        'net_margin':               resumen['net_margin'].round(4),
        'purchase_frequency':       resumen['purchase_frequency'].round(4),
        'customer_lifespan_months': resumen['lifespan_months'].round(2),
        'cltv':                     resumen['cltv'],
        'recency_days':             resumen['recency_days'],
        'frequency':                resumen['frequency'],
        'monetary':                 resumen['monetary'],
        'rfm_score':                resumen['rfm_score'],
        'rfm_segment':              resumen['rfm_segment'],
        'days_since_last_purchase': resumen['recency_days'],
        'churn_score':              resumen['churn_score'],
        'churn_label':              resumen['churn_label'].astype(str),
        'cluster_id':               None,
        'cluster_label':            None
    })

    resultado.to_sql('customer_360', engine, schema='marts',
                     if_exists='append', index=False)
    print(f"  ✅ customer_360: {len(resultado)} filas")
    print(f"     CLTV medio:   {resultado['cltv'].mean():.2f}€")
    print(f"     CLTV máximo:  {resultado['cltv'].max():.2f}€")
    print(f"     Segmentos:    {resultado['rfm_segment'].value_counts().to_dict()}")
    print(f"     Churn High:   {(resultado['churn_label'] == 'High').sum()} clientes")