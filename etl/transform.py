import pandas as pd
from sqlalchemy import text


def truncate_all(engine):
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE marts.customer_360 CASCADE"))
        conn.execute(text("TRUNCATE TABLE dwh.fact_returns CASCADE"))
        conn.execute(text("TRUNCATE TABLE dwh.fact_sales CASCADE"))
        conn.execute(text("TRUNCATE TABLE dwh.dim_date CASCADE"))
        conn.execute(text("TRUNCATE TABLE dwh.dim_customer CASCADE"))
        conn.execute(text("TRUNCATE TABLE dwh.dim_product CASCADE"))
        conn.execute(text("TRUNCATE TABLE dwh.dim_store CASCADE"))
        conn.execute(text("TRUNCATE TABLE dwh.dim_offer CASCADE"))
        conn.execute(text("TRUNCATE TABLE dwh.dim_return_reason CASCADE"))
    print("  🧹 Tablas limpiadas")


def load_dim_date(engine, df_sale):
    fechas = pd.to_datetime(df_sale['sale_date']).dt.normalize().unique()
    df = pd.DataFrame({'full_date': pd.DatetimeIndex(fechas)})
    df['year']         = df['full_date'].dt.year
    df['quarter']      = df['full_date'].dt.quarter
    df['month']        = df['full_date'].dt.month
    df['month_name']   = df['full_date'].dt.strftime('%B')
    df['week']         = df['full_date'].dt.isocalendar().week.astype(int)
    df['day_of_month'] = df['full_date'].dt.day
    df['day_of_week']  = df['full_date'].dt.dayofweek
    df['day_name']     = df['full_date'].dt.strftime('%A')
    df['is_weekend']   = df['day_of_week'] >= 5
    df['full_date']    = df['full_date'].dt.date
    df.to_sql('dim_date', engine, schema='dwh', if_exists='append', index=False)
    print(f"  ✅ dim_date: {len(df)} filas")


def load_dim_customer(engine, df_customer):
    df = df_customer.copy()
    df['last_name'] = df['last_name'].astype(str) + ' ' + df['last_name2'].astype(str)
    resultado = pd.DataFrame({
        'customer_id': df['customer_id'],
        'first_name':  df['first_name'],
        'last_name':   df['last_name'],
        'email':       df['email'],
        'phone':       df['phone'],
        'postal_code': None,
        'zone_name':   None,
        'created_at':  df['created_at']
    })
    resultado.to_sql('dim_customer', engine, schema='dwh', if_exists='append', index=False)
    print(f"  ✅ dim_customer: {len(resultado)} filas")


def load_dim_product(engine, df_product, df_central_product, df_brand, df_category):
    df = df_central_product.copy()
    df = df.merge(
        df_brand[['brand_id', 'name']].rename(columns={'name': 'brand_name'}),
        on='brand_id', how='left'
    )
    df = df.merge(
        df_category[['category_id', 'name']].rename(columns={'name': 'category_name'}),
        on='category_id', how='left'
    )
    df['is_cost_imputed'] = df['unit_cost'].isna()
    df.loc[df['is_cost_imputed'], 'unit_cost'] = (
        df.loc[df['is_cost_imputed'], 'unit_price'] * 0.60
    )

    # Productos en sale_item que no están en central_product (ej: producto 29)
    ids_central = set(df['product_id'])
    faltantes = df_product[~df_product['product_id'].isin(ids_central)].copy()

    if len(faltantes) > 0:
        faltantes['brand_name']      = faltantes['manufacturer']
        faltantes['category_name']   = faltantes['category']
        faltantes['unit_price']      = faltantes['price']
        faltantes['unit_cost']       = faltantes['price'] * 0.60
        faltantes['is_cost_imputed'] = True
        print(f"  ⚠️  Productos faltantes añadidos con coste imputado: {list(faltantes['product_id'])}")

        extra = faltantes[['product_id', 'name', 'brand_name', 'category_name',
                            'unit_price', 'unit_cost', 'is_cost_imputed']].copy()
    else:
        extra = pd.DataFrame()

    base = df[['product_id', 'name', 'brand_name', 'category_name',
               'unit_price', 'unit_cost', 'is_cost_imputed']].copy()

    resultado = pd.concat([base, extra], ignore_index=True)
    resultado = resultado.rename(columns={'name': 'product_name'})

    resultado.to_sql('dim_product', engine, schema='dwh', if_exists='append', index=False)
    print(f"  ✅ dim_product: {len(resultado)} filas")


def load_dim_store(engine, df_store, df_city_zone):
    df = df_store.merge(
        df_city_zone[['postal_code', 'district']],
        on='postal_code', how='left'
    )
    resultado = pd.DataFrame({
        'store_id':    df['store_id'],
        'store_name':  df['name'],
        'address':     df['address'],
        'city':        df['city'],
        'postal_code': df['postal_code'],
        'latitude':    df['latitude'],
        'longitude':   df['longitude']
    })
    resultado.to_sql('dim_store', engine, schema='dwh', if_exists='append', index=False)
    print(f"  ✅ dim_store: {len(resultado)} filas")


def load_dim_offer(engine, df_offer):
    resultado = pd.DataFrame({
        'offer_id':     df_offer['offer_id'],
        'offer_name':   df_offer['name'],
        'discount_pct': df_offer['discount_percent']
    })
    resultado.to_sql('dim_offer', engine, schema='dwh', if_exists='append', index=False)
    print(f"  ✅ dim_offer: {len(resultado)} filas")


def load_dim_return_reason(engine, df_return_reason):
    resultado = pd.DataFrame({
        'reason_id':   df_return_reason['reason_id'],
        'reason_desc': df_return_reason['reason']
    })
    resultado.to_sql('dim_return_reason', engine, schema='dwh', if_exists='append', index=False)
    print(f"  ✅ dim_return_reason: {len(resultado)} filas")


def load_fact_sales(engine, df_sale, df_sale_item, df_central_product):
    dim_date     = pd.read_sql("SELECT date_sk, full_date FROM dwh.dim_date", engine)
    dim_customer = pd.read_sql("SELECT customer_sk, customer_id FROM dwh.dim_customer", engine)
    dim_product  = pd.read_sql("SELECT product_sk, product_id FROM dwh.dim_product", engine)
    dim_store    = pd.read_sql("SELECT store_sk, store_id FROM dwh.dim_store", engine)
    dim_offer    = pd.read_sql("SELECT offer_sk, offer_id FROM dwh.dim_offer", engine)

    dim_date['full_date'] = pd.to_datetime(dim_date['full_date']).dt.date

    df_sale = df_sale.copy()
    df_sale['full_date'] = pd.to_datetime(df_sale['sale_date']).dt.date

    # Costes de central_product, renombramos unit_price para evitar conflicto
    costes = df_central_product[['product_id', 'unit_cost', 'unit_price']].rename(
        columns={'unit_price': 'cost_unit_price'}
    )

    df = df_sale_item.merge(
        df_sale[['sale_id', 'customer_id', 'store_id', 'full_date']],
        on='sale_id', how='left'
    )
    df = df.merge(costes, on='product_id', how='left')
    df['unit_cost'] = df['unit_cost'].fillna(df['cost_unit_price'] * 0.60)
    df['gross_margin'] = df['subtotal'] - (df['unit_cost'] * df['quantity'])

    returned_ids = set(pd.read_sql(
        "SELECT sale_item_id FROM public.return_item", engine
    )['sale_item_id'])
    df['is_returned'] = df['sale_item_id'].isin(returned_ids)

    df = df.merge(dim_date, on='full_date', how='left')
    df = df.merge(dim_customer, on='customer_id', how='left')
    df = df.merge(dim_product, on='product_id', how='left')
    df = df.merge(dim_store, on='store_id', how='left')
    df = df.merge(dim_offer, on='offer_id', how='left')

    resultado = pd.DataFrame({
        'date_sk':     df['date_sk'],
        'customer_sk': df['customer_sk'],
        'product_sk':  df['product_sk'],
        'store_sk':    df['store_sk'],
        'offer_sk':    df['offer_sk'],
        'sale_id':     df['sale_id'],
        'sale_item_id':df['sale_item_id'],
        'quantity':    df['quantity'],
        'unit_price':  df['unit_price'],
        'unit_cost':   df['unit_cost'],
        'subtotal':    df['subtotal'],
        'gross_margin':df['gross_margin'],
        'is_returned': df['is_returned']
    })
    resultado.to_sql('fact_sales', engine, schema='dwh', if_exists='append', index=False)
    print(f"  ✅ fact_sales: {len(resultado)} filas")


def load_fact_returns(engine, df_return_item, df_sale, df_sale_item):
    dim_date     = pd.read_sql("SELECT date_sk, full_date FROM dwh.dim_date", engine)
    dim_customer = pd.read_sql("SELECT customer_sk, customer_id FROM dwh.dim_customer", engine)
    dim_product  = pd.read_sql("SELECT product_sk, product_id FROM dwh.dim_product", engine)
    dim_store    = pd.read_sql("SELECT store_sk, store_id FROM dwh.dim_store", engine)
    dim_reason   = pd.read_sql("SELECT reason_sk, reason_id FROM dwh.dim_return_reason", engine)

    dim_date['full_date'] = pd.to_datetime(dim_date['full_date']).dt.date

    # Enriquecer return_item con datos de sale_item y sale
    df = df_return_item.merge(
        df_sale_item[['sale_item_id', 'sale_id', 'product_id', 'unit_price']],
        on='sale_item_id', how='left'
    )
    df = df.merge(
        df_sale[['sale_id', 'customer_id', 'store_id']],
        on='sale_id', how='left'
    )
    df['full_date'] = pd.to_datetime(df['return_date']).dt.date
    df['refund_amount'] = df['quantity'] * df['unit_price']

    # Lookup SKs
    df = df.merge(dim_date, on='full_date', how='left')
    df = df.merge(dim_customer, on='customer_id', how='left')
    df = df.merge(dim_product, on='product_id', how='left')
    df = df.merge(dim_store, on='store_id', how='left')
    df = df.merge(dim_reason, on='reason_id', how='left')

    resultado = pd.DataFrame({
        'date_sk':          df['date_sk'],
        'customer_sk':      df['customer_sk'],
        'product_sk':       df['product_sk'],
        'store_sk':         df['store_sk'],
        'reason_sk':        df['reason_sk'],
        'sale_item_id':     df['sale_item_id'],
        'quantity_returned':df['quantity'],
        'refund_amount':    df['refund_amount']
    })
    resultado.to_sql('fact_returns', engine, schema='dwh', if_exists='append', index=False)
    print(f"  ✅ fact_returns: {len(resultado)} filas")