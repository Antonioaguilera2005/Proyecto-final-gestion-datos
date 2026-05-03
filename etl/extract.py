import pandas as pd
from etl.config import get_engine

TABLAS_ORIGEN = [
    'sale', 'sale_item', 'customer', 'product', 'store',
    'offer', 'product_offer', 'return_item', 'return_reason',
    'brand', 'category', 'central_product', 'city_zone'
]

def extract_all():
    engine = get_engine()
    data = {}
    for tabla in TABLAS_ORIGEN:
        data[tabla] = pd.read_sql(f"SELECT * FROM {tabla}", engine)
        print(f"  ✅ {tabla}: {len(data[tabla])} filas")
    return data