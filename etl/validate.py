import pandas as pd
from sqlalchemy import text

def run_validations(engine):
    validaciones = []

    def check(nombre, query, esperado=None, condicion=None):
        with engine.connect() as conn:
            result = conn.execute(text(query)).scalar()
        if condicion:
            ok = condicion(result)
        else:
            ok = result == esperado
        estado = "✅ PASS" if ok else "❌ FAIL"
        validaciones.append({'nombre': nombre, 'resultado': result, 'estado': estado})
        print(f"  {estado} | {nombre}: {result}")
        return ok

    print("\n  — Row counts —")
    check("fact_sales filas",        "SELECT COUNT(*) FROM dwh.fact_sales",        42555)
    check("fact_returns filas",      "SELECT COUNT(*) FROM dwh.fact_returns",       2330)
    check("dim_customer filas",      "SELECT COUNT(*) FROM dwh.dim_customer",       5750)
    check("dim_product filas",       "SELECT COUNT(*) FROM dwh.dim_product",         50)
    check("dim_store filas",         "SELECT COUNT(*) FROM dwh.dim_store",             20)
    check("customer_360 filas",      "SELECT COUNT(*) FROM marts.customer_360",      5750)

    print("\n  — Integridad FK —")
    check("FK customer sin huérfanos",
          "SELECT COUNT(*) FROM dwh.fact_sales WHERE customer_sk NOT IN (SELECT customer_sk FROM dwh.dim_customer)",
          0)
    check("FK product sin huérfanos",
          "SELECT COUNT(*) FROM dwh.fact_sales WHERE product_sk NOT IN (SELECT product_sk FROM dwh.dim_product)",
          0)
    check("FK date sin huérfanos",
          "SELECT COUNT(*) FROM dwh.fact_sales WHERE date_sk NOT IN (SELECT date_sk FROM dwh.dim_date)",
          0)

    print("\n  — Nulos críticos —")
    check("Sin customer_sk nulos en fact_sales",
          "SELECT COUNT(*) FROM dwh.fact_sales WHERE customer_sk IS NULL", 0)
    check("Sin product_sk nulos en fact_sales",
          "SELECT COUNT(*) FROM dwh.fact_sales WHERE product_sk IS NULL", 0)
    check("Sin CLTV nulos en customer_360",
          "SELECT COUNT(*) FROM marts.customer_360 WHERE cltv IS NULL", 0)

    print("\n  — Reglas de negocio —")
    check("CLTV >= 0 para todos",
          "SELECT COUNT(*) FROM marts.customer_360 WHERE cltv < 0", 0)
    check("Subtotal > 0 siempre",
          "SELECT COUNT(*) FROM dwh.fact_sales WHERE subtotal <= 0", 0)
    check("Churn score entre 0 y 100",
          "SELECT COUNT(*) FROM marts.customer_360 WHERE churn_score < 0 OR churn_score > 100", 0)
    check("Clusters asignados a todos",
          "SELECT COUNT(*) FROM marts.customer_360 WHERE cluster_id IS NULL", 0)
    check("RFM segment sin nulos",
          "SELECT COUNT(*) FROM marts.customer_360 WHERE rfm_segment IS NULL", 0)

    total = len(validaciones)
    pasadas = sum(1 for v in validaciones if 'PASS' in v['estado'])
    print(f"\n  {'✅' if pasadas == total else '⚠️'} {pasadas}/{total} validaciones OK")
    return pasadas == total