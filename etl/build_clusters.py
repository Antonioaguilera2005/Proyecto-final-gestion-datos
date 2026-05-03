import pandas as pd
import numpy as np
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

def build_clusters(engine, n_clusters=4):
    df = pd.read_sql("SELECT * FROM marts.customer_360", engine)

    features = ['cltv', 'recency_days', 'frequency', 'monetary',
                'net_margin', 'purchase_frequency', 'churn_score']

    X = df[features].fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    df['pca_x'] = X_pca[:, 0]
    df['pca_y'] = X_pca[:, 1]
    print(f"  📊 Varianza explicada PCA: {pca.explained_variance_ratio_.sum()*100:.1f}%")

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df['cluster_id'] = kmeans.fit_predict(X_scaled)

    # Etiquetar clusters por CLTV medio
    cltv_por_cluster = df.groupby('cluster_id')['cltv'].mean().sort_values(ascending=False)
    etiquetas = ['Alto Valor', 'Medio-Alto', 'Medio-Bajo', 'Bajo Valor']
    mapa_etiquetas = {cluster: etiqueta for cluster, etiqueta in zip(cltv_por_cluster.index, etiquetas)}
    df['cluster_label'] = df['cluster_id'].map(mapa_etiquetas)

    # Resumen por cluster
    print("\n  Perfil de clusters:")
    resumen = df.groupby('cluster_label').agg(
        n_clientes    = ('customer_id', 'count'),
        cltv_medio    = ('cltv', 'mean'),
        recency_medio = ('recency_days', 'mean'),
        churn_medio   = ('churn_score', 'mean')
    ).round(1)
    print(resumen.to_string())

    # Añadir columnas pca si no existen
    with engine.begin() as conn:
        for col, tipo in [('pca_x', 'NUMERIC(10,4)'), ('pca_y', 'NUMERIC(10,4)')]:
            try:
                conn.execute(text(f"ALTER TABLE marts.customer_360 ADD COLUMN {col} {tipo}"))
            except Exception:
                pass

    # Actualizar en batch
    updates = [
        {
            'cid':    int(row['cluster_id']),
            'clabel': row['cluster_label'],
            'px':     float(row['pca_x']),
            'py':     float(row['pca_y']),
            'sk':     int(row['customer_sk'])
        }
        for _, row in df.iterrows()
    ]

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE marts.customer_360
            SET cluster_id    = :cid,
                cluster_label = :clabel,
                pca_x         = :px,
                pca_y         = :py
            WHERE customer_sk = :sk
        """), updates)

    print(f"\n  ✅ Clusters asignados a {len(df)} clientes")