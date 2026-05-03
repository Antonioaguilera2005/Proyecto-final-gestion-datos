from etl.config import get_engine
from etl.extract import extract_all
from etl.transform import (
    truncate_all,
    load_dim_date, load_dim_customer, load_dim_product,
    load_dim_store, load_dim_offer, load_dim_return_reason,
    load_fact_sales, load_fact_returns
)
from etl.build_customer360 import build_customer_360
from etl.build_clusters import build_clusters
from etl.validate import run_validations

def run():
    print("\n>>> FASE 1 — EXTRACT")
    data = extract_all()

    engine = get_engine()

    print("\n>>> LIMPIANDO TABLAS DWH")
    truncate_all(engine)

    print("\n>>> FASE 2 — DIMENSIONES")
    load_dim_date(engine, data['sale'])
    load_dim_customer(engine, data['customer'])
    load_dim_product(engine, data['product'], data['central_product'], data['brand'], data['category'])
    load_dim_store(engine, data['store'], data['city_zone'])
    load_dim_offer(engine, data['offer'])
    load_dim_return_reason(engine, data['return_reason'])

    print("\n>>> FASE 3 — HECHOS")
    load_fact_sales(engine, data['sale'], data['sale_item'], data['central_product'])
    load_fact_returns(engine, data['return_item'], data['sale'], data['sale_item'])

    print("\n>>> FASE 4 — CUSTOMER 360")
    build_customer_360(engine)

    print("\n>>> FASE 5 — CLUSTERING")
    build_clusters(engine)

    print("\n>>> FASE 6 — VALIDACIONES")
    run_validations(engine)

    print("\n✅ PIPELINE COMPLETADO")

if __name__ == "__main__":
    run()