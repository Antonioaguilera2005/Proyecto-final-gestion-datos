import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

load_dotenv()

st.set_page_config(
    page_title="Saleshealth Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1, h2, h3 { color: #e6edf3 !important; }
    p, li { color: #8b949e; }
    .kpi-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 8px;
    }
    .kpi-label { font-size: 11px; font-weight: 600; letter-spacing: 1px;
                 text-transform: uppercase; color: #8b949e; margin-bottom: 4px; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #e6edf3; line-height: 1.2; }
    .kpi-sub   { font-size: 12px; color: #8b949e; margin-top: 2px; }
    .section-header {
        border-left: 3px solid #58a6ff;
        padding-left: 12px;
        margin: 24px 0 12px 0;
    }
    .section-header h3 { margin: 0 !important; color: #e6edf3 !important; font-size: 16px !important; }
    .section-header p  { margin: 2px 0 0 0; font-size: 12px; color: #8b949e; }
    .insight-box {
        background: #1c2128;
        border: 1px solid #30363d;
        border-left: 3px solid #f78166;
        border-radius: 6px;
        padding: 14px 18px;
        margin: 12px 0;
        color: #e6edf3 !important;
    }
    .insight-box * { color: #e6edf3 !important; }
    .insight-box b  { color: #f78166 !important; }
    .tag {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        margin: 2px;
    }
    .footer-bar {
        background: #161b22;
        border-top: 1px solid #30363d;
        padding: 8px 16px;
        font-size: 11px;
        color: #8b949e;
        margin-top: 32px;
        border-radius: 6px;
    }
    code { background: #1c2128 !important; color: #79c0ff !important;
           padding: 1px 6px; border-radius: 4px; font-size: 11px; }
    [data-testid="stDataFrame"] tbody tr { background-color: #161b22 !important; }
    [data-testid="stDataFrame"] thead tr { background-color: #1c2128 !important; }
</style>
""", unsafe_allow_html=True)

BG     = '#0d1117'
CARD   = '#161b22'
BORDER = '#30363d'
TEXT   = '#e6edf3'
MUTED  = '#8b949e'

COLORS = {
    'blue':   '#58a6ff', 'green':  '#3fb950', 'orange': '#d29922',
    'red':    '#f85149', 'purple': '#bc8cff', 'cyan':   '#39d353',
    'pink':   '#f778ba', 'yellow': '#e3b341',
}

CLUSTER_COLORS = {
    'Alto Valor':   '#3fb950',
    'Medio-Alto':   '#58a6ff',
    'Medio-Bajo':   '#e3b341',
    'Bajo Valor':   '#f85149',
}

RFM_COLORS = {
    'Champions':          '#3fb950',
    'Loyal':              '#58a6ff',
    'At Risk':            '#f85149',
    'New Customers':      '#39d353',
    'Potential':          '#e3b341',
    'Lost':               '#8b949e',
    'Loyal Customers':    '#58a6ff',
    'Cant Lose Them':     '#bc8cff',
    'Hibernating':        '#d29922',
    'Potential Loyalists':'#79c0ff',
    'Others':             '#6e7681',
}

LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font=dict(color=MUTED, size=11),
    legend=dict(bgcolor=CARD, bordercolor=BORDER, font=dict(size=10, color=TEXT)),
    margin=dict(t=40, b=30, l=10, r=10),
)

AXIS = dict(gridcolor=BORDER, linecolor=BORDER, tickcolor=MUTED, color=MUTED)


def kpi(label, value, sub='', color='#58a6ff'):
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 2px solid {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{color}">{value}</div>
        {"<div class='kpi-sub'>" + sub + "</div>" if sub else ""}
    </div>""", unsafe_allow_html=True)


def section(title, subtitle='', color='#58a6ff'):
    st.markdown(f"""
    <div class="section-header" style="border-left-color:{color}">
        <h3>{title}</h3>
        {"<p>" + subtitle + "</p>" if subtitle else ""}
    </div>""", unsafe_allow_html=True)


def insight(text):
    st.markdown(f'<div class="insight-box">{text}</div>', unsafe_allow_html=True)


def footer(source):
    st.markdown(f'<div class="footer-bar">💾 {source}</div>', unsafe_allow_html=True)


@st.cache_data(ttl=600)
def load_data():
    _engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME_ORIGEN')}"
    )
    c360 = pd.read_sql("SELECT * FROM marts.customer_360", _engine)
    customers = pd.read_sql(
        "SELECT customer_id, first_name, last_name, email, phone FROM dwh.dim_customer",
        _engine
    )
    sales = pd.read_sql("""
        SELECT dd.year, dd.month, dd.full_date,
               fs.sale_id, fs.subtotal, fs.gross_margin,
               fs.is_returned, fs.quantity, fs.customer_sk,
               dp.product_name, dp.category_name, dp.brand_name,
               ds.store_name, ds.city
        FROM dwh.fact_sales fs
        JOIN dwh.dim_date dd     ON fs.date_sk = dd.date_sk
        JOIN dwh.dim_product dp  ON fs.product_sk = dp.product_sk
        JOIN dwh.dim_store ds    ON fs.store_sk = ds.store_sk
    """, _engine)
    c360 = c360.merge(customers, on='customer_id', how='left')
    c360['nombre'] = c360['first_name'] + ' ' + c360['last_name']
    c360['activo'] = c360['recency_days'] <= 365
    sales['full_date'] = pd.to_datetime(sales['full_date'])
    sales['periodo'] = (sales['year'].astype(str) + '-' +
                        sales['month'].astype(str).str.zfill(2))
    return c360, sales


def get_engine():
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME_ORIGEN')}"
    )


c360, sales = load_data()
engine = get_engine()

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='margin-bottom:8px'>
        <div style='font-size:11px;color:{MUTED};letter-spacing:1px;
                    text-transform:uppercase'>Customer Analytics</div>
        <div style='font-size:22px;font-weight:700;color:{TEXT}'>Saleshealth</div>
    </div>""", unsafe_allow_html=True)

    pagina = st.radio("", [
        "Inicio", "KPIs Globales", "Analisis Cliente", "Clustering", "Customer 360"
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f"<div style='font-size:11px;color:{MUTED}'>SNAPSHOT</div>",
                unsafe_allow_html=True)
    snap = {
        "Clientes": f"{len(c360):,}",
        "Ventas":   f"{sales['sale_id'].nunique():,}",
        "Periodo":  f"{sales['year'].min()}–{sales['year'].max()}",
        "Margen":   f"{(sales['gross_margin'].sum()/sales['subtotal'].sum()*100):.0f} %"
    }
    for k, v in snap.items():
        st.markdown(f"""
        <div style='display:flex;justify-content:space-between;
                    padding:3px 0;font-size:12px'>
            <span style='color:{MUTED}'>{k}</span>
            <span style='color:{TEXT};font-weight:600'>{v}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"<div style='font-size:11px;color:{MUTED}'>Proyecto Final</div>",
                unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:12px;color:{TEXT}'>UAX 2025 / 2026</div>",
                unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:12px;color:{TEXT}'>Antonio Aguilera Slavcheva</div>",
                unsafe_allow_html=True)
    st.markdown("<code>marts.customer_360</code>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# INICIO
# ══════════════════════════════════════════════════════════
if pagina == "Inicio":
    st.markdown(f"""
    <div style='margin-bottom:24px'>
        <div style='font-size:11px;font-weight:600;letter-spacing:2px;
                    text-transform:uppercase;color:{COLORS["blue"]};margin-bottom:8px'>
            Customer Analytics · UAX Final Project</div>
        <div style='font-size:42px;font-weight:800;color:{TEXT};line-height:1.1'>
            Saleshealth</div>
        <div style='font-size:16px;color:{MUTED};margin-top:8px'>
            Análisis de Customer Lifetime Value, segmentación RFM y clustering K-Means sobre
            <b style='color:{TEXT}'>{len(c360):,} clientes</b> y
            <b style='color:{TEXT}'>{sales["sale_id"].nunique():,} ventas</b>
            de un retail de productos de salud.
        </div>
    </div>
    <hr style='border-color:{BORDER};margin:20px 0'>
    """, unsafe_allow_html=True)

    section("KEY NUMBERS", color=COLORS['blue'])
    c1, c2, c3, c4 = st.columns(4)
    total_rev       = sales['subtotal'].sum()
    margin_pct      = sales['gross_margin'].sum() / total_rev * 100
    champ_cltv      = c360[c360['rfm_segment'] == 'Champions']['cltv'].sum()
    champ_total_pct = champ_cltv / c360['cltv'].sum() * 100
    churn_high      = (c360['churn_label'] == 'High').sum()

    with c1: kpi("Ingresos Totales", f"{total_rev/1e6:.3f}M €", color=COLORS['green'])
    with c2: kpi("Margen Bruto",     f"{margin_pct:.0f}%",       color=COLORS['blue'])
    with c3: kpi("CLTV Champions",   f"{champ_cltv/1e6:.2f}M €",
                 sub=f"{champ_total_pct:.1f}% del CLTV total",   color=COLORS['purple'])
    with c4: kpi("Churn High",       f"{churn_high:,}",
                 sub="riesgo alto de abandono",                   color=COLORS['red'])

    st.markdown(f"<hr style='border-color:{BORDER};margin:20px 0'>", unsafe_allow_html=True)

    champ_n_pct = len(c360[c360['rfm_segment'] == 'Champions']) / len(c360) * 100
    insight(f"""
    <span style='font-size:11px;font-weight:600;letter-spacing:1px;color:#f78166'>
        HALLAZGO PRINCIPAL
    </span><br><br>
    <span style='color:#e6edf3'>
    El <b style='color:#58a6ff'>{champ_n_pct:.0f}% de la base</b> de clientes (Champions)
    genera el <b style='color:#f85149'>{champ_total_pct:.1f}% del CLTV histórico</b>
    del negocio. El clustering K-Means revela además un segmento de
    <b style='color:#f85149'>clientes con alta tasa de devolución</b>
    invisible al RFM tradicional.
    </span>
    """)

    section("SECCIONES DEL ANÁLISIS", color=COLORS['blue'])
    c1, c2, c3, c4 = st.columns(4)
    secciones = [
        ("KPIs Globales",    COLORS['green'],
         "Ingresos, márgenes, evolución temporal del negocio",
         f"{total_rev/1e6:.2f}M €", "REVENUE 2020-2025"),
        ("Analisis Cliente", COLORS['pink'],
         "Distribución de CLTV, segmentos RFM, top clientes",
         f"{c360['rfm_segment'].nunique()} segmentos", "RFM SCORING"),
        ("Clustering",       COLORS['purple'],
         "Visualización de los 4 clusters K-Means tras PCA",
         "4 perfiles", "K-MEANS + PCA"),
        ("Customer 360",     COLORS['cyan'],
         "Buscador individual con ficha completa por cliente",
         f"{len(c360):,}", "CLIENTES ÚNICOS"),
    ]
    for col, (nombre, color, desc, stat, stat_label) in zip([c1, c2, c3, c4], secciones):
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="border-top:2px solid {color};min-height:160px">
                <div style='font-size:14px;font-weight:700;color:{TEXT};margin-bottom:6px'>
                    {nombre}</div>
                <div style='font-size:12px;color:{MUTED};margin-bottom:12px'>{desc}</div>
                <hr style='border-color:{BORDER};margin:8px 0'>
                <div style='font-size:20px;font-weight:700;color:{color}'>{stat}</div>
                <div style='font-size:10px;color:{MUTED};letter-spacing:1px'>{stat_label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown(f"<hr style='border-color:{BORDER};margin:20px 0'>", unsafe_allow_html=True)
    section("STACK", color=COLORS['blue'])
    tags = ["PostgreSQL 18", "Python · pandas · SQLAlchemy",
            "scikit-learn · K-Means · PCA", "Streamlit · Plotly",
            "Kimball Dimensional Modeling"]
    tags_html = "".join([
        f"<span class='tag' style='background:{CARD};border:1px solid {BORDER};"
        f"color:{TEXT}'>{t}</span>" for t in tags
    ])
    st.markdown(tags_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# KPIs GLOBALES
# ══════════════════════════════════════════════════════════
elif pagina == "KPIs Globales":
    st.markdown(f"""
    <div style='margin-bottom:20px'>
        <div style='font-size:11px;color:{COLORS["blue"]};font-weight:600;
                    letter-spacing:2px;text-transform:uppercase'>Saleshealth Analytics</div>
        <div style='font-size:32px;font-weight:800;color:{TEXT}'>KPIs Globales</div>
        <div style='font-size:13px;color:{MUTED}'>
            Vista ejecutiva del negocio · Ingresos, márgenes y evolución temporal ·
            Periodo {sales["year"].min()}–{sales["year"].max()}</div>
    </div>""", unsafe_allow_html=True)

    section("Resumen del negocio", color=COLORS['green'])
    total_rev  = sales['subtotal'].sum()
    total_mg   = sales['gross_margin'].sum()
    n_ventas   = sales['sale_id'].nunique()
    n_items    = len(sales)
    devol_mg   = sales[sales['is_returned']]['gross_margin'].sum()
    devol_tasa = sales['is_returned'].mean() * 100
    cltv_medio = c360['cltv'].mean()
    churn_pct  = (c360['recency_days'] > 365).mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Ingresos Totales",  f"{total_rev:,.0f} €", color=COLORS['green'])
    with c2: kpi("Margen Bruto",      f"{total_mg:,.0f} €",
                 sub=f"{total_mg/total_rev*100:.1f}% sobre ingresos", color=COLORS['blue'])
    with c3: kpi("Clientes Únicos",   f"{len(c360):,}", color=COLORS['purple'])
    with c4: kpi("Ventas (cabecera)", f"{n_ventas:,}",
                 sub=f"{n_items:,} items", color=COLORS['orange'])

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Devoluciones (margen perdido)", f"{abs(devol_mg):,.0f} €",
                 color=COLORS['red'])
    with c2: kpi("Tasa Devolución Global", f"{devol_tasa:.2f} %", color=COLORS['yellow'])
    with c3: kpi("CLTV Medio", f"{cltv_medio:,.0f} €",
                 sub=f"{(c360['activo'].sum()/len(c360)*100):.1f}% recurrentes",
                 color=COLORS['cyan'])
    with c4: kpi("Clientes en Churn", f"{churn_pct:.1f} %",
                 sub=">365 días sin compra", color=COLORS['pink'])

    section("Evolución mensual", "Ingresos y margen agrupados por mes",
            color=COLORS['green'])
    mes = sales.groupby('periodo').agg(
        ingresos=('subtotal', 'sum'),
        margen=('gross_margin', 'sum')
    ).reset_index().sort_values('periodo')

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.6, 0.4], vertical_spacing=0.06)
    fig.add_trace(go.Bar(
        x=mes['periodo'], y=mes['ingresos'],
        name='Ingresos mensuales',
        marker_color=COLORS['pink'], opacity=0.85
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=mes['periodo'], y=mes['margen'],
        name='Margen bruto mensual (€)',
        line=dict(color=COLORS['green'], width=2),
        mode='lines+markers', marker=dict(size=4)
    ), row=2, col=1)
    fig.update_layout(**LAYOUT, height=400, showlegend=False)
    fig.update_xaxes(gridcolor=BORDER, linecolor=BORDER, tickcolor=MUTED, color=MUTED)
    fig.update_yaxes(gridcolor=BORDER, linecolor=BORDER, tickcolor=MUTED, color=MUTED)
    fig.update_xaxes(title_text='Mes', row=2, col=1)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        section("Margen % mensual", color=COLORS['yellow'])
        mes['mg_pct'] = mes['margen'] / mes['ingresos'] * 100
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=mes['periodo'], y=mes['mg_pct'],
            fill='tozeroy', fillcolor='rgba(210,153,34,0.15)',
            line=dict(color=COLORS['yellow'], width=2),
            mode='lines'
        ))
        fig2.add_hline(y=40, line_dash='dot', line_color=MUTED,
                       annotation_text='Objetivo 40%',
                       annotation_font_color=MUTED)
        fig2.update_layout(**LAYOUT, height=260,
                           xaxis=dict(title='Mes', **AXIS),
                           yaxis=dict(title='% margen', **AXIS))
        st.plotly_chart(fig2, use_container_width=True)

    with c2:
        section("Tasa devolución mensual", color=COLORS['red'])
        devol_mes = sales.groupby('periodo').agg(
            n_total=('is_returned', 'count'),
            n_devol=('is_returned', 'sum')
        ).reset_index()
        devol_mes['tasa'] = devol_mes['n_devol'] / devol_mes['n_total'] * 100
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=devol_mes['periodo'], y=devol_mes['tasa'],
            line=dict(color=COLORS['orange'], width=2),
            mode='lines+markers', marker=dict(size=4)
        ))
        fig3.update_layout(**LAYOUT, height=260,
                           xaxis=dict(title='Mes', **AXIS),
                           yaxis=dict(title='% items devueltos', **AXIS))
        st.plotly_chart(fig3, use_container_width=True)

    section("Resumen anual", "Agregado por año desde fact_sales", color=COLORS['purple'])
    anual = sales.groupby('year').agg(
        n_ventas=('sale_id', 'nunique'),
        ingresos=('subtotal', 'sum'),
        margen=('gross_margin', 'sum'),
    ).reset_index()
    anual['mg_pct'] = (anual['margen'] / anual['ingresos'] * 100).round(2)
    anual.columns = ['Año', 'Nº ventas', 'Ingresos', 'Margen', 'Margen %']
    anual['Ingresos'] = anual['Ingresos'].apply(lambda x: f"{x:,.0f} €")
    anual['Margen']   = anual['Margen'].apply(lambda x: f"{x:,.0f} €")
    anual['Margen %'] = anual['Margen %'].apply(lambda x: f"{x:.2f} %")
    st.dataframe(anual, use_container_width=True, hide_index=True)

    footer("Datos cargados desde <code>marts.customer_360</code> y "
           "<code>dwh.fact_sales</code> · Cache TTL: 10 min")


# ══════════════════════════════════════════════════════════
# ANÁLISIS CLIENTE
# ══════════════════════════════════════════════════════════
elif pagina == "Analisis Cliente":
    st.markdown(f"""
    <div style='margin-bottom:20px'>
        <div style='font-size:11px;color:{COLORS["pink"]};font-weight:600;
                    letter-spacing:2px;text-transform:uppercase'>Saleshealth Analytics</div>
        <div style='font-size:32px;font-weight:800;color:{TEXT}'>Análisis de Cliente</div>
        <div style='font-size:13px;color:{MUTED}'>
            CLTV · Segmentación RFM · Churn Risk · Top clientes</div>
    </div>""", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("---")
        st.markdown(f"<div style='font-size:11px;color:{MUTED}'>Filtros</div>",
                    unsafe_allow_html=True)
        solo_recurrentes = st.checkbox("Solo clientes recurrentes (≥2 compras)")
        solo_activos     = st.checkbox("Solo clientes activos (no churn)")
        segmentos_disp   = sorted(c360['rfm_segment'].dropna().unique())
        seg_sel          = st.multiselect("Segmentos RFM", segmentos_disp,
                                          default=segmentos_disp)

    df = c360.copy()
    if solo_recurrentes: df = df[df['frequency'] >= 2]
    if solo_activos:     df = df[df['activo']]
    if seg_sel:          df = df[df['rfm_segment'].isin(seg_sel)]

    section(f"Resumen de la población",
            f"{len(df):,} de {len(c360):,} clientes ({len(df)/len(c360)*100:.1f}%)",
            color=COLORS['pink'])
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Clientes en filtro", f"{len(df):,}", color=COLORS['pink'])
    with c2: kpi("CLTV Total",         f"{df['cltv'].sum():,.0f} €", color=COLORS['green'])
    with c3: kpi("CLTV Medio",         f"{df['cltv'].mean():,.0f} €", color=COLORS['blue'])
    with c4: kpi("CLTV Mediano",       f"{df['cltv'].median():,.0f} €", color=COLORS['purple'])

    section("Distribución del CLTV histórico", color=COLORS['pink'])
    c1, c2 = st.columns(2)
    with c1:
        df_hist = df[df['cltv'] < df['cltv'].quantile(0.95)]
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=df_hist['cltv'], nbinsx=60,
            marker_color=COLORS['pink'], opacity=0.8
        ))
        fig_hist.add_vline(x=df['cltv'].mean(), line_dash='dash',
                           line_color=COLORS['green'],
                           annotation_text=f"Media: {df['cltv'].mean():,.0f}€",
                           annotation_font_color=COLORS['green'])
        fig_hist.add_vline(x=df['cltv'].median(), line_dash='dot',
                           line_color=COLORS['blue'],
                           annotation_text=f"Mediana: {df['cltv'].median():,.0f}€",
                           annotation_font_color=COLORS['blue'])
        fig_hist.update_layout(**LAYOUT, height=300,
                               xaxis=dict(title='CLTV histórico (€)', **AXIS),
                               yaxis=dict(title='Nº clientes', **AXIS))
        st.plotly_chart(fig_hist, use_container_width=True)

    with c2:
        section("Curva de Pareto del CLTV", color=COLORS['yellow'])
        df_sorted = df.sort_values('cltv', ascending=False).reset_index(drop=True)
        df_sorted['pct_clientes']  = (df_sorted.index + 1) / len(df_sorted) * 100
        df_sorted['cltv_acum_pct'] = (df_sorted['cltv'].cumsum() /
                                       df_sorted['cltv'].sum() * 100)
        fig_par = go.Figure()
        fig_par.add_trace(go.Scatter(
            x=df_sorted['pct_clientes'], y=df_sorted['cltv_acum_pct'],
            fill='tozeroy', fillcolor='rgba(227,179,65,0.15)',
            line=dict(color=COLORS['yellow'], width=2)
        ))
        fig_par.add_hline(y=80, line_dash='dot', line_color=MUTED,
                          annotation_text='80% CLTV',
                          annotation_font_color=MUTED)
        top20_pct = df_sorted[df_sorted['cltv_acum_pct'] <= 80]['pct_clientes'].max()
        fig_par.add_vline(x=top20_pct, line_dash='dot', line_color=COLORS['red'],
                          annotation_text=f'Top {top20_pct:.0f}%',
                          annotation_font_color=COLORS['red'])
        fig_par.update_layout(**LAYOUT, height=300,
                              xaxis=dict(title='% acumulado de clientes', **AXIS),
                              yaxis=dict(title='% CLTV acumulado', **AXIS))
        st.plotly_chart(fig_par, use_container_width=True)

    section("Segmentación RFM",
            "Segmentos accionables · Cada cliente clasificado por R-F-M",
            color=COLORS['blue'])
    rfm_stats = df.groupby('rfm_segment').agg(
        N        =('customer_id', 'count'),
        cltv_sum =('cltv', 'sum'),
        cltv_avg =('cltv', 'mean'),
    ).reset_index().sort_values('cltv_sum', ascending=False)
    rfm_stats['pct_base'] = rfm_stats['N'] / len(df) * 100
    rfm_stats['pct_cltv'] = rfm_stats['cltv_sum'] / rfm_stats['cltv_sum'].sum() * 100

    c1, c2 = st.columns(2)
    with c1:
        fig_rfm1 = px.bar(rfm_stats, x='N', y='rfm_segment', orientation='h',
                          color='rfm_segment', color_discrete_map=RFM_COLORS,
                          text='N', title='Nº clientes por segmento',
                          labels={'N': 'Nº clientes', 'rfm_segment': ''})
        fig_rfm1.update_layout(**LAYOUT, height=320, showlegend=False,
                               xaxis=AXIS, yaxis=AXIS)
        st.plotly_chart(fig_rfm1, use_container_width=True)
    with c2:
        fig_rfm2 = px.bar(rfm_stats, x='cltv_sum', y='rfm_segment', orientation='h',
                          color='rfm_segment', color_discrete_map=RFM_COLORS,
                          text=rfm_stats['pct_cltv'].apply(lambda x: f"{x:.1f}%"),
                          title='CLTV total por segmento (€)',
                          labels={'cltv_sum': 'CLTV total (€)', 'rfm_segment': ''})
        fig_rfm2.update_layout(**LAYOUT, height=320, showlegend=False,
                               xaxis=AXIS, yaxis=AXIS)
        st.plotly_chart(fig_rfm2, use_container_width=True)

    rfm_tabla = rfm_stats.copy()
    rfm_tabla['cltv_sum'] = rfm_tabla['cltv_sum'].apply(lambda x: f"{x:,.0f} €")
    rfm_tabla['cltv_avg'] = rfm_tabla['cltv_avg'].apply(lambda x: f"{x:,.2f} €")
    rfm_tabla['pct_base'] = rfm_tabla['pct_base'].apply(lambda x: f"{x:.1f} %")
    rfm_tabla['pct_cltv'] = rfm_tabla['pct_cltv'].apply(lambda x: f"{x:.1f} %")
    rfm_tabla.columns = ['Segmento RFM', 'Nº', 'CLTV total', 'CLTV medio',
                         '% base', '% CLTV']
    st.dataframe(rfm_tabla, use_container_width=True, hide_index=True)

    section("Distribución Churn Risk", color=COLORS['red'])
    c1, c2 = st.columns(2)
    with c1:
        df['activo_label'] = df['activo'].map({True: 'Active', False: 'Churned'})
        churn_data = df.groupby(['churn_label', 'activo_label']).size().reset_index(name='n')
        fig_ch = px.bar(churn_data, x='churn_label', y='n', color='activo_label',
                        color_discrete_map={
                            'Active': COLORS['green'], 'Churned': COLORS['pink']
                        },
                        text='n',
                        labels={'n': 'Nº clientes', 'churn_label': 'Nivel de Churn Risk'})
        fig_ch.update_layout(**LAYOUT, height=280, xaxis=AXIS, yaxis=AXIS)
        st.plotly_chart(fig_ch, use_container_width=True)
    with c2:
        section("Distribución de nº de pedidos", color=COLORS['cyan'])
        fig_freq = px.histogram(
            df[df['frequency'] <= 30], x='frequency', nbins=30,
            color_discrete_sequence=[COLORS['cyan']],
            labels={'frequency': 'Nº pedidos por cliente (capped a 30)',
                    'count': 'Nº clientes'}
        )
        fig_freq.update_layout(**LAYOUT, height=280, xaxis=AXIS, yaxis=AXIS)
        st.plotly_chart(fig_freq, use_container_width=True)

    section("Top 20 clientes por CLTV histórico",
            "Ranking de los clientes más valiosos en la población filtrada",
            color=COLORS['green'])
    top20 = df.nlargest(20, 'cltv')[
        ['customer_id', 'nombre', 'frequency', 'cltv',
         'recency_days', 'rfm_segment', 'churn_label']
    ].copy()
    top20['cltv'] = top20['cltv'].apply(lambda x: f"{x:,.2f} €")
    top20.columns = ['ID', 'Nombre', 'Nº pedidos', 'CLTV',
                     'Días desde última compra', 'Segmento RFM', 'Churn Risk']
    st.dataframe(top20, use_container_width=True, hide_index=True)

    footer(f"{len(df):,} clientes en el filtro actual · "
           "Datos desde <code>marts.customer_360</code>")


# ══════════════════════════════════════════════════════════
# CLUSTERING
# ══════════════════════════════════════════════════════════
elif pagina == "Clustering":
    st.markdown(f"""
    <div style='margin-bottom:20px'>
        <div style='font-size:11px;color:{COLORS["purple"]};font-weight:600;
                    letter-spacing:2px;text-transform:uppercase'>Saleshealth Analytics</div>
        <div style='font-size:32px;font-weight:800;color:{TEXT}'>Clustering K-Means</div>
        <div style='font-size:13px;color:{MUTED}'>
            Segmentación tras PCA · 4 clusters globales</div>
    </div>""", unsafe_allow_html=True)

    features = ['cltv', 'recency_days', 'frequency', 'monetary',
                'net_margin', 'purchase_frequency', 'churn_score']
    X     = c360[features].fillna(0)
    X_sc  = StandardScaler().fit_transform(X)
    pca   = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_sc)
    var_exp = pca.explained_variance_ratio_

    df_cl = c360.copy()
    df_cl['PC1'] = X_pca[:, 0]
    df_cl['PC2'] = X_pca[:, 1]
    cluster_col = 'cluster_label'

    stats = df_cl.groupby(cluster_col).agg(
        N           =('customer_id', 'count'),
        cltv_avg    =('cltv', 'mean'),
        cltv_total  =('cltv', 'sum'),
        orders_avg  =('frequency', 'mean'),
        recency_avg =('recency_days', 'mean'),
        churn_avg   =('churn_score', 'mean'),
    ).reset_index().sort_values('cltv_avg', ascending=False)

    section("Resumen del modelo global", f"{len(df_cl):,} clientes clusterizados",
            color=COLORS['purple'])
    cluster_border_colors = [
        COLORS['green'], COLORS['blue'], COLORS['yellow'], COLORS['red']
    ]
    cols = st.columns(len(stats))
    for i, (col, (_, row)) in enumerate(zip(cols, stats.iterrows())):
        with col:
            bc = cluster_border_colors[i % len(cluster_border_colors)]
            st.markdown(f"""
            <div class="kpi-card" style="border-top:2px solid {bc}">
                <div class="kpi-label">{row[cluster_col]}</div>
                <div class="kpi-value" style="color:{bc}">{row['N']:,}</div>
                <div class="kpi-sub">CLTV avg: {row['cltv_avg']:,.0f} €</div>
            </div>""", unsafe_allow_html=True)

    section("Proyección 2D (PCA)",
            "Cada cliente proyectado en las 2 primeras componentes principales",
            color=COLORS['purple'])
    fig_pca = px.scatter(
        df_cl, x='PC1', y='PC2', color=cluster_col,
        color_discrete_map=CLUSTER_COLORS,
        opacity=0.6,
        hover_data=['customer_id', 'nombre', 'cltv', 'rfm_segment'],
        labels={
            'PC1': f'PC1 ({var_exp[0]*100:.1f}% varianza)',
            'PC2': f'PC2 ({var_exp[1]*100:.1f}% varianza)',
            cluster_col: 'Cluster'
        }
    )
    for trace in fig_pca.data:
        n = stats[stats[cluster_col] == trace.name]['N'].values
        if len(n):
            trace.name = f"{trace.name} (n={n[0]:,})"
    fig_pca.update_layout(**LAYOUT, height=450, xaxis=AXIS, yaxis=AXIS)
    st.plotly_chart(fig_pca, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        section("Perfil comparativo (normalizado)",
                "Comparativa normalizada de las features (0=mínimo, 1=máximo en este modelo)",
                color=COLORS['cyan'])
        radar_features = ['cltv', 'frequency', 'recency_days', 'churn_score',
                          'net_margin', 'monetary', 'purchase_frequency']
        radar_labels   = ['CLTV', 'Frecuencia', 'Recencia', 'Churn',
                          'Margen', 'Ingresos netos', 'Ped/mes']
        radar_df   = df_cl.groupby(cluster_col)[radar_features].mean()
        radar_norm = (radar_df - radar_df.min()) / (radar_df.max() - radar_df.min() + 1e-9)

        radar_fill_colors = [
            'rgba(63,185,80,0.15)', 'rgba(88,166,255,0.15)',
            'rgba(227,179,65,0.15)', 'rgba(248,81,73,0.15)'
        ]
        fig_rad = go.Figure()
        for i, (cl, row) in enumerate(radar_norm.iterrows()):
            vals = list(row) + [row.iloc[0]]
            lbls = radar_labels + [radar_labels[0]]
            n_cl = stats[stats[cluster_col] == cl]['N'].values
            n_label = f" (n={n_cl[0]:,})" if len(n_cl) else ""
            fig_rad.add_trace(go.Scatterpolar(
                r=vals, theta=lbls, fill='toself',
                name=f"{cl}{n_label}",
                line=dict(color=cluster_border_colors[i % 4], width=2.5),
                fillcolor=radar_fill_colors[i % 4]
            ))
        # Quitar 'legend' de LAYOUT antes de pasarlo al radar
        layout_sin_legend = {k: v for k, v in LAYOUT.items() if k != 'legend'}
        fig_rad.update_layout(
            **layout_sin_legend, height=440,
            legend=dict(
                bgcolor=CARD, bordercolor=BORDER,
                font=dict(color=TEXT, size=11),
                orientation='h',
                yanchor='bottom', y=-0.30,
                xanchor='center', x=0.5
            ),
            showlegend=True,
            polar=dict(
                bgcolor=CARD,
                radialaxis=dict(
                    visible=True, range=[0, 1],
                    gridcolor=BORDER, tickcolor=MUTED,
                    tickfont=dict(color=MUTED, size=9)
                ),
                angularaxis=dict(
                    gridcolor=BORDER, tickcolor=MUTED,
                    color=TEXT, tickfont=dict(size=11, color=TEXT)
                )
            )
        )
        st.plotly_chart(fig_rad, use_container_width=True)

    with c2:
        section("Cruce Cluster ↔ Segmento RFM",
                "Cuántos clientes de cada cluster pertenecen a cada segmento RFM",
                color=COLORS['pink'])
        pivot = df_cl.groupby([cluster_col, 'rfm_segment']).size().unstack(fill_value=0)
        fig_heat = px.imshow(
            pivot, text_auto=True, aspect='auto',
            color_continuous_scale=[
                [0, '#1c2128'], [0.5, '#0d4a6b'], [1.0, '#f778ba']
            ],
            labels=dict(x='Segmento RFM', y='Cluster', color='Nº clientes')
        )
        fig_heat.update_layout(
            **LAYOUT, height=440,
            xaxis=dict(**AXIS, title='Segmento RFM'),
            yaxis=dict(**AXIS, title='Cluster'),
            coloraxis_colorbar=dict(
                tickfont=dict(color=MUTED),
                title=dict(text='Nº clientes', font=dict(color=MUTED))
            )
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    section("Detalle numérico", color=COLORS['green'])
    det = stats.copy()
    det['cltv_avg']    = det['cltv_avg'].apply(lambda x: f"{x:,.2f} €")
    det['cltv_total']  = det['cltv_total'].apply(lambda x: f"{x:,.0f} €")
    det['orders_avg']  = det['orders_avg'].round(1)
    det['churn_avg']   = det['churn_avg'].round(1).astype(str) + ' %'
    det['recency_avg'] = det['recency_avg'].round(0).astype(int).astype(str) + ' días'
    det.columns = ['Cluster', 'Nº', 'CLTV avg', 'CLTV total',
                   'Orders avg', 'Recencia avg', 'Churn avg']
    st.dataframe(det, use_container_width=True, hide_index=True)

    tox = stats.nlargest(1, 'churn_avg').iloc[0]
    insight(f"""
    <span style='font-size:13px;font-weight:700;color:#f78166'>Insight clave</span><br><br>
    <span style='color:#e6edf3'>
    El cluster <b style='color:#f85149'>"{tox[cluster_col]}"</b>
    (≈{tox['N']:,} clientes, {tox['N']/len(df_cl)*100:.1f}% de la base)
    tiene el mayor churn score medio ({tox['churn_avg']:.1f}) y aporta solo
    ~{tox['cltv_total']:,.0f} € de CLTV total — un segmento que el RFM tradicional
    <i>no detecta</i>. Solo el clustering multidimensional lo aísla.
    </span>
    """)

    footer("Clusters persistidos en <code>marts.customer_360</code> · "
           "PCA recalculado on-the-fly para la visualización 2D")


# ══════════════════════════════════════════════════════════
# CUSTOMER 360
# ══════════════════════════════════════════════════════════
elif pagina == "Customer 360":
    st.markdown(f"""
    <div style='margin-bottom:20px'>
        <div style='font-size:11px;color:{COLORS["cyan"]};font-weight:600;
                    letter-spacing:2px;text-transform:uppercase'>Saleshealth Analytics</div>
        <div style='font-size:32px;font-weight:800;color:{TEXT}'>Customer 360</div>
        <div style='font-size:13px;color:{MUTED}'>
            Ficha completa por cliente · Métricas, histórico de compras y comparativa</div>
    </div>""", unsafe_allow_html=True)

    section("Selecciona un cliente", color=COLORS['cyan'])
    modo = st.radio("", ["Top CLTV", "Buscar por ID / nombre"],
                    horizontal=True, label_visibility='collapsed')

    if modo == "Top CLTV":
        top_options = c360.nlargest(50, 'cltv')[['customer_id', 'nombre', 'cltv']]
        opts = {f"{r['customer_id']} — {r['nombre']}": r['customer_id']
                for _, r in top_options.iterrows()}
        sel = st.selectbox("", list(opts.keys()), label_visibility='collapsed')
        cid = opts[sel]
    else:
        cid = st.number_input("Customer ID", min_value=1,
                              max_value=int(c360['customer_id'].max()), value=1)

    cliente = c360[c360['customer_id'] == cid]
    if len(cliente) == 0:
        st.warning("Cliente no encontrado.")
        st.stop()

    r = cliente.iloc[0]
    cl_color  = (COLORS['green']  if r['churn_label'] == 'Low'    else
                 COLORS['orange'] if r['churn_label'] == 'Medium' else COLORS['red'])
    rfm_color = RFM_COLORS.get(r['rfm_segment'], COLORS['blue'])

    st.markdown(f"""
    <div class="kpi-card" style="border-left:3px solid {COLORS['cyan']};
                                  padding:20px 24px;position:relative">
        <div style='font-size:11px;color:{MUTED};letter-spacing:1px'>
            CLIENTE #{r['customer_id']}</div>
        <div style='font-size:28px;font-weight:800;color:{TEXT};margin:4px 0'>
            {r['nombre']}</div>
        <div style='font-size:13px;color:{MUTED}'>
            Email: {r.get('email', '—')} · Tel: {r.get('phone', '—')}</div>
        <div style='position:absolute;top:20px;right:20px'>
            <span style='background:{COLORS["green"]};color:#000;padding:4px 12px;
                         border-radius:20px;font-size:12px;font-weight:700;margin-right:6px'>
                {r.get('cluster_label', '—')}</span>
            <span style='background:{rfm_color};color:#000;padding:4px 12px;
                         border-radius:20px;font-size:12px;font-weight:700'>
                {r['rfm_segment']}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    section("Métricas del cliente", color=COLORS['cyan'])

    ventas_cliente = pd.read_sql(f"""
        SELECT fs.sale_id, fs.subtotal, fs.gross_margin,
               fs.is_returned, fs.quantity, dd.full_date
        FROM dwh.fact_sales fs
        JOIN dwh.dim_customer dc ON fs.customer_sk = dc.customer_sk
        JOIN dwh.dim_date dd     ON fs.date_sk = dd.date_sk
        WHERE dc.customer_id = {cid}
    """, engine)

    ticket_medio  = ventas_cliente.groupby('sale_id')['subtotal'].sum().mean()
    total_gastado = ventas_cliente['subtotal'].sum()
    total_margen  = ventas_cliente['gross_margin'].sum()
    n_devol       = ventas_cliente['is_returned'].sum()
    antiguedad    = (pd.Timestamp('2025-12-31') -
                     pd.to_datetime(ventas_cliente['full_date']).min()).days

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("CLTV Histórico",  f"{r['cltv']:,.2f} €", color=COLORS['cyan'])
    with c2: kpi("Nº Pedidos",      f"{r['frequency']}",
                 sub=f"{int(ventas_cliente['quantity'].sum())} unidades totales",
                 color=COLORS['green'])
    with c3: kpi("Ticket Medio",    f"{ticket_medio:,.2f} €", color=COLORS['blue'])
    with c4: kpi("Margen Generado", f"{total_margen:,.2f} €", color=COLORS['purple'])

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Última Compra Hace", f"{r['recency_days']} días",
                 color=COLORS['yellow'])
    with c2: kpi("Antigüedad",         f"{antiguedad} días", color=COLORS['orange'])
    with c3: kpi("Tasa Devolución",
                 f"{ventas_cliente['is_returned'].mean()*100:.1f} %",
                 color=cl_color)
    with c4: kpi("Estado",
                 "Activo" if r['activo'] else "Inactivo",
                 sub=f"Churn risk: {r['churn_label']}", color=cl_color)

    section("Histórico de compras",
            "Pedidos del cliente ordenados por fecha (más recientes primero)",
            color=COLORS['green'])

    historico = pd.read_sql(f"""
        SELECT dd.full_date AS fecha, fs.sale_id,
               SUM(fs.subtotal)       AS importe,
               SUM(fs.quantity)       AS unidades,
               BOOL_OR(fs.is_returned) AS tiene_devolucion
        FROM dwh.fact_sales fs
        JOIN dwh.dim_customer dc ON fs.customer_sk = dc.customer_sk
        JOIN dwh.dim_date dd     ON fs.date_sk = dd.date_sk
        WHERE dc.customer_id = {cid}
        GROUP BY dd.full_date, fs.sale_id
        ORDER BY dd.full_date
    """, engine)
    historico['full_date'] = pd.to_datetime(historico['fecha'])

    c1, c2 = st.columns([2, 1])
    with c1:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(
            x=historico['full_date'],
            y=historico['importe'],
            mode='markers+lines',
            marker=dict(
                size=historico['unidades'].clip(5, 30),
                color=historico['tiene_devolucion'].map(
                    {True: COLORS['red'], False: COLORS['orange']}
                ),
                opacity=0.8
            ),
            line=dict(color=COLORS['cyan'], width=1, dash='dot'),
            text=historico['importe'].apply(lambda x: f"{x:,.0f}€"),
            hovertemplate='%{x}<br>%{text}<extra></extra>'
        ))
        fig_hist.update_layout(**LAYOUT, height=320,
                               xaxis=dict(title='Fecha', **AXIS),
                               yaxis=dict(title='Importe (€)', **AXIS))
        st.plotly_chart(fig_hist, use_container_width=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Estadísticas del histórico</div><br>
            <div style='font-size:11px;color:{MUTED}'>TOTAL PEDIDOS</div>
            <div style='font-size:20px;font-weight:700;color:{COLORS["cyan"]}'>
                {r['frequency']}</div><br>
            <div style='font-size:11px;color:{MUTED}'>TOTAL GASTADO</div>
            <div style='font-size:20px;font-weight:700;color:{COLORS["pink"]}'>
                {total_gastado:,.2f} €</div><br>
            <div style='font-size:11px;color:{MUTED}'>TICKET MEDIO</div>
            <div style='font-size:20px;font-weight:700;color:{COLORS["green"]}'>
                {ticket_medio:,.2f} €</div><br>
            <div style='font-size:11px;color:{MUTED}'>PEDIDOS CON DEVOLUCIÓN</div>
            <div style='font-size:20px;font-weight:700;color:{COLORS["yellow"]}'>
                {int(n_devol)}</div>
        </div>""", unsafe_allow_html=True)

    with st.expander(f"Ver detalle de los {r['frequency']} pedidos"):
        det_pedidos = pd.read_sql(f"""
            SELECT dd.full_date  AS fecha,
                   dp.product_name  AS producto,
                   dp.category_name AS categoria,
                   ds.store_name    AS tienda,
                   fs.quantity      AS cantidad,
                   fs.subtotal,
                   fs.is_returned   AS devuelto
            FROM dwh.fact_sales fs
            JOIN dwh.dim_customer dc ON fs.customer_sk = dc.customer_sk
            JOIN dwh.dim_date dd     ON fs.date_sk = dd.date_sk
            JOIN dwh.dim_product dp  ON fs.product_sk = dp.product_sk
            JOIN dwh.dim_store ds    ON fs.store_sk = ds.store_sk
            WHERE dc.customer_id = {cid}
            ORDER BY dd.full_date DESC
        """, engine)
        st.dataframe(det_pedidos, use_container_width=True, hide_index=True)

    footer(f"Cliente #{cid} · Datos desde <code>dwh.fact_sales</code> "
           "y <code>marts.customer_360</code>")