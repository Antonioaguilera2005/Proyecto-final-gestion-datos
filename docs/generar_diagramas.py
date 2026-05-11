import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

# ══════════════════════════════════════════════════════════
# DIAGRAMA 1 — MODELO DIMENSIONAL (ESTRELLA)
# ══════════════════════════════════════════════════════════

def draw_star_schema():
    fig, ax = plt.subplots(1, 1, figsize=(20, 14))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 14)
    ax.axis('off')
    fig.patch.set_facecolor('#0f1117')
    ax.set_facecolor('#0f1117')

    def draw_table(ax, x, y, w, h, title, fields, color_header, color_body='#1e2130'):
        # Header
        header = FancyBboxPatch((x, y + h - 0.6), w, 0.6,
                                boxstyle="round,pad=0.05",
                                facecolor=color_header, edgecolor='#3d4466', linewidth=1.5)
        ax.add_patch(header)
        ax.text(x + w/2, y + h - 0.3, title, ha='center', va='center',
                fontsize=8, fontweight='bold', color='white')
        # Body
        body = FancyBboxPatch((x, y), w, h - 0.6,
                              boxstyle="round,pad=0.05",
                              facecolor=color_body, edgecolor='#3d4466', linewidth=1.5)
        ax.add_patch(body)
        for i, field in enumerate(fields):
            color = '#f97316' if field.startswith('PK') else '#6366f1' if field.startswith('FK') else '#a0aec0'
            ax.text(x + 0.15, y + h - 0.9 - i * 0.35, field,
                    fontsize=6.5, color=color, va='center')

    def draw_arrow(ax, x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='#4a5568',
                                   lw=1.5, connectionstyle='arc3,rad=0'))

    # FACT_SALES (centro)
    draw_table(ax, 7.5, 5.0, 5.0, 4.2, '⭐ fact_sales', [
        'PK sale_item_sk',
        'FK date_sk',
        'FK customer_sk',
        'FK product_sk',
        'FK store_sk',
        'FK offer_sk',
        '   sale_id',
        '   sale_item_id',
        '   quantity',
        '   unit_price',
        '   unit_cost',
        '   subtotal',
        '   gross_margin',
        '   is_returned',
    ], '#7c3aed')

    # FACT_RETURNS (centro-derecha)
    draw_table(ax, 13.5, 5.5, 4.5, 3.5, '⭐ fact_returns', [
        'PK return_sk',
        'FK date_sk',
        'FK customer_sk',
        'FK product_sk',
        'FK store_sk',
        'FK reason_sk',
        '   sale_item_id',
        '   quantity_returned',
        '   refund_amount',
    ], '#7c3aed')

    # DIM_DATE (arriba centro)
    draw_table(ax, 7.8, 10.2, 4.5, 3.0, '📅 dim_date', [
        'PK date_sk',
        '   full_date',
        '   year',
        '   quarter',
        '   month / month_name',
        '   week',
        '   day_of_week / day_name',
        '   is_weekend',
    ], '#1d4ed8')

    # DIM_CUSTOMER (izquierda arriba)
    draw_table(ax, 0.5, 8.5, 4.5, 3.0, '👤 dim_customer', [
        'PK customer_sk',
        '   customer_id',
        '   first_name',
        '   last_name',
        '   email',
        '   phone',
        '   postal_code',
        '   zone_name',
        '   created_at',
    ], '#065f46')

    # DIM_PRODUCT (izquierda abajo)
    draw_table(ax, 0.5, 4.0, 4.5, 3.5, '📦 dim_product', [
        'PK product_sk',
        '   product_id',
        '   product_name',
        '   brand_name',
        '   category_name',
        '   unit_price',
        '   unit_cost',
        '   is_cost_imputed',
    ], '#065f46')

    # DIM_STORE (abajo centro)
    draw_table(ax, 7.8, 0.5, 4.5, 3.2, '🏪 dim_store', [
        'PK store_sk',
        '   store_id',
        '   store_name',
        '   address / city',
        '   postal_code',
        '   latitude / longitude',
    ], '#1d4ed8')

    # DIM_OFFER (derecha arriba)
    draw_table(ax, 15.0, 9.5, 4.0, 2.5, '🏷️ dim_offer', [
        'PK offer_sk',
        '   offer_id',
        '   offer_name',
        '   discount_pct',
    ], '#92400e')

    # DIM_RETURN_REASON (derecha abajo)
    draw_table(ax, 15.0, 3.0, 4.5, 2.5, '↩️ dim_return_reason', [
        'PK reason_sk',
        '   reason_id',
        '   reason_desc',
    ], '#92400e')

    # Flechas fact_sales → dims
    draw_arrow(ax, 10.0, 9.2, 10.5, 10.2)   # → dim_date
    draw_arrow(ax, 7.5,  7.5, 5.0,  9.0)    # → dim_customer
    draw_arrow(ax, 7.5,  6.5, 5.0,  6.0)    # → dim_product
    draw_arrow(ax, 10.0, 5.0, 10.0, 3.7)    # → dim_store
    draw_arrow(ax, 12.5, 8.5, 15.0, 10.0)   # → dim_offer

    # Flechas fact_returns → dims
    draw_arrow(ax, 13.5, 8.5, 12.0, 10.0)   # → dim_date
    draw_arrow(ax, 13.5, 7.5, 5.0,  9.5)    # → dim_customer
    draw_arrow(ax, 13.5, 6.5, 5.0,  5.5)    # → dim_product
    draw_arrow(ax, 15.5, 5.5, 15.0, 5.0)    # → dim_return_reason

    # Título y leyenda
    ax.text(10, 13.5, 'Modelo Dimensional · Saleshealth DWH',
            ha='center', va='center', fontsize=14, fontweight='bold', color='white')
    ax.text(10, 13.1, 'Esquema en estrella tipo Kimball · Grano: 1 línea de venta = 1 sale_item',
            ha='center', va='center', fontsize=9, color='#a0aec0')

    legend = [
        mpatches.Patch(color='#f97316', label='PK — Primary Key'),
        mpatches.Patch(color='#6366f1', label='FK — Foreign Key'),
        mpatches.Patch(color='#7c3aed', label='Tabla de hechos'),
        mpatches.Patch(color='#1d4ed8', label='Dimensión temporal/geográfica'),
        mpatches.Patch(color='#065f46', label='Dimensión cliente/producto'),
        mpatches.Patch(color='#92400e', label='Dimensión descriptiva'),
    ]
    ax.legend(handles=legend, loc='lower left', fontsize=7,
              facecolor='#1e2130', edgecolor='#3d4466', labelcolor='white')

    plt.tight_layout()
    plt.savefig('docs/modelo_dimensional.png', dpi=150,
                bbox_inches='tight', facecolor='#0f1117')
    plt.close()
    print("✅ docs/modelo_dimensional.png generado")


# ══════════════════════════════════════════════════════════
# DIAGRAMA 2 — MODELO ER ORIGEN
# ══════════════════════════════════════════════════════════

def draw_er_origen():
    fig, ax = plt.subplots(1, 1, figsize=(24, 16))
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 16)
    ax.axis('off')
    fig.patch.set_facecolor('#0f1117')
    ax.set_facecolor('#0f1117')

    def draw_table(ax, x, y, w, title, fields, color='#1e2130'):
        h = 0.5 + len(fields) * 0.32
        header = FancyBboxPatch((x, y + h - 0.45), w, 0.45,
                                boxstyle="round,pad=0.03",
                                facecolor=color, edgecolor='#4a5568', linewidth=1.2)
        ax.add_patch(header)
        ax.text(x + w/2, y + h - 0.22, title, ha='center', va='center',
                fontsize=7.5, fontweight='bold', color='white')
        body = FancyBboxPatch((x, y), w, h - 0.45,
                              boxstyle="round,pad=0.03",
                              facecolor='#1a1f2e', edgecolor='#4a5568', linewidth=1.2)
        ax.add_patch(body)
        for i, (fname, ftype, is_pk, is_fk) in enumerate(fields):
            color_f = '#f97316' if is_pk else '#6366f1' if is_fk else '#cbd5e0'
            prefix = '🔑' if is_pk else '🔗' if is_fk else '  '
            ax.text(x + 0.12, y + h - 0.7 - i * 0.32,
                    f"{prefix} {fname} : {ftype}",
                    fontsize=5.8, color=color_f, va='center')
        return h

    def arrow(ax, x1, y1, x2, y2, color='#4a5568'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.2))

    # VENTAS
    draw_table(ax, 9, 9.5, 3.8, 'sale', [
        ('sale_id',     'SERIAL PK', True,  False),
        ('customer_id', 'INT FK',    False, True),
        ('store_id',    'INT FK',    False, True),
        ('sale_date',   'TIMESTAMP', False, False),
        ('total',       'NUMERIC',   False, False),
    ], '#1d4ed8')

    draw_table(ax, 9, 5.5, 3.8, 'sale_item', [
        ('sale_item_id', 'SERIAL PK', True,  False),
        ('sale_id',      'INT FK',    False, True),
        ('product_id',   'INT FK',    False, True),
        ('quantity',     'INT',       False, False),
        ('unit_price',   'NUMERIC',   False, False),
        ('offer_id',     'INT FK',    False, True),
        ('subtotal',     'NUMERIC',   False, False),
    ], '#1d4ed8')

    # CLIENTE
    draw_table(ax, 0.3, 9.0, 3.8, 'customer', [
        ('customer_id', 'SERIAL PK', True,  False),
        ('first_name',  'VARCHAR',   False, False),
        ('last_name',   'VARCHAR',   False, False),
        ('last_name2',  'VARCHAR',   False, False),
        ('email',       'VARCHAR',   False, False),
        ('phone',       'VARCHAR',   False, False),
        ('created_at',  'TIMESTAMP', False, False),
    ], '#065f46')

    # PRODUCTO
    draw_table(ax, 0.3, 4.0, 3.8, 'product', [
        ('product_id',    'SERIAL PK', True,  False),
        ('name',          'VARCHAR',   False, False),
        ('category',      'VARCHAR',   False, False),
        ('manufacturer',  'VARCHAR',   False, False),
        ('price',         'NUMERIC',   False, False),
        ('created_at',    'TIMESTAMP', False, False),
    ], '#065f46')

    draw_table(ax, 0.3, 0.3, 3.8, 'central_product', [
        ('product_id',  'INT PK',  True,  False),
        ('name',        'VARCHAR', False, False),
        ('category_id', 'INT FK',  False, True),
        ('brand_id',    'INT FK',  False, True),
        ('sku',         'VARCHAR', False, False),
        ('unit_cost',   'NUMERIC', False, False),
        ('unit_price',  'NUMERIC', False, False),
    ], '#065f46')

    # TIENDA
    draw_table(ax, 13.5, 9.5, 3.8, 'store', [
        ('store_id',     'SERIAL PK', True,  False),
        ('name',         'VARCHAR',   False, False),
        ('address',      'VARCHAR',   False, False),
        ('city',         'VARCHAR',   False, False),
        ('postal_code',  'VARCHAR',   False, False),
        ('latitude',     'NUMERIC',   False, False),
        ('longitude',    'NUMERIC',   False, False),
        ('opened_date',  'DATE',      False, False),
    ], '#92400e')

    # DEVOLUCIONES
    draw_table(ax, 13.5, 5.5, 3.8, 'return_item', [
        ('return_id',    'SERIAL PK', True,  False),
        ('sale_item_id', 'INT FK',    False, True),
        ('return_date',  'TIMESTAMP', False, False),
        ('quantity',     'INT',       False, False),
        ('reason_id',    'INT FK',    False, True),
    ], '#7c3aed')

    draw_table(ax, 13.5, 2.5, 3.5, 'return_reason', [
        ('reason_id',  'SERIAL PK', True,  False),
        ('reason',     'VARCHAR',   False, False),
        ('active',     'BOOLEAN',   False, False),
    ], '#7c3aed')

    # CATÁLOGOS
    draw_table(ax, 4.5, 0.3, 3.5, 'brand', [
        ('brand_id', 'SERIAL PK', True,  False),
        ('name',     'VARCHAR',   False, False),
        ('country',  'VARCHAR',   False, False),
        ('website',  'VARCHAR',   False, False),
    ], '#b45309')

    draw_table(ax, 4.5, 3.5, 3.0, 'category', [
        ('category_id',  'SERIAL PK', True,  False),
        ('name',         'VARCHAR',   False, False),
        ('description',  'TEXT',      False, False),
    ], '#b45309')

    draw_table(ax, 4.5, 6.5, 3.2, 'offer', [
        ('offer_id',        'SERIAL PK', True,  False),
        ('name',            'VARCHAR',   False, False),
        ('discount_percent','NUMERIC',   False, False),
        ('start_date',      'DATE',      False, False),
        ('end_date',        'DATE',      False, False),
    ], '#b45309')

    draw_table(ax, 4.5, 9.5, 3.2, 'city_zone', [
        ('postal_code',      'VARCHAR PK', True,  False),
        ('district',         'VARCHAR',    False, False),
        ('area_type',        'VARCHAR',    False, False),
        ('zone_orientation', 'VARCHAR',    False, False),
        ('city_code',        'INT',        False, False),
        ('city',             'VARCHAR',    False, False),
    ], '#b45309')

    # INVENTARIO
    draw_table(ax, 18.5, 9.5, 3.8, 'inventory', [
        ('inventory_id', 'SERIAL PK', True,  False),
        ('product_id',   'INT FK',    False, True),
        ('store_id',     'INT FK',    False, True),
        ('stock',        'INT',       False, False),
        ('updated_at',   'TIMESTAMP', False, False),
    ], '#374151')

    draw_table(ax, 18.5, 5.5, 3.8, 'central_inventory', [
        ('id',          'SERIAL PK', True,  False),
        ('product_id',  'INT FK',    False, True),
        ('location_id', 'INT FK',    False, True),
        ('warehouse_id','INT FK',    False, True),
        ('stock',       'INT',       False, False),
        ('updated_at',  'TIMESTAMP', False, False),
    ], '#374151')

    draw_table(ax, 18.5, 2.0, 3.5, 'warehouse', [
        ('warehouse_id', 'SERIAL PK', True,  False),
        ('name',         'VARCHAR',   False, False),
        ('address',      'VARCHAR',   False, False),
        ('city',         'VARCHAR',   False, False),
    ], '#374151')

    draw_table(ax, 18.5, 0.0, 3.5, 'warehouse_location', [
        ('location_id',  'SERIAL PK', True,  False),
        ('warehouse_id', 'INT FK',    False, True),
        ('aisle',        'VARCHAR',   False, False),
        ('shelf',        'VARCHAR',   False, False),
    ], '#374151')

    draw_table(ax, 18.5, 13.0, 3.5, 'product_offer', [
        ('product_id', 'INT FK', False, True),
        ('offer_id',   'INT FK', False, True),
    ], '#b45309')

    # Flechas principales
    arrow(ax, 9.0,  11.0, 4.1, 11.5)   # sale → customer
    arrow(ax, 9.0,  10.5, 13.5, 10.5)  # sale → store
    arrow(ax, 10.9, 9.5,  10.9, 8.5)   # sale → sale_item
    arrow(ax, 9.0,  7.0,  4.1, 5.0)    # sale_item → product
    arrow(ax, 9.0,  6.5,  7.7, 7.5)    # sale_item → offer
    arrow(ax, 13.5, 7.0,  17.3, 7.0)   # sale_item → return_item
    arrow(ax, 17.3, 6.2,  17.0, 4.2)   # return_item → return_reason
    arrow(ax, 4.1,  1.5,  4.1, 3.5)    # central_product → category
    arrow(ax, 4.1,  1.2,  4.1, 0.8)    # central_product → brand

    # Título
    ax.text(12, 15.5, 'Modelo Entidad-Relación · saleshealth_origen',
            ha='center', fontsize=14, fontweight='bold', color='white')
    ax.text(12, 15.1, '17 tablas · Base de datos operacional de venta retail de productos de salud',
            ha='center', fontsize=9, color='#a0aec0')

    legend = [
        mpatches.Patch(color='#f97316', label='PK — Primary Key'),
        mpatches.Patch(color='#6366f1', label='FK — Foreign Key'),
        mpatches.Patch(color='#1d4ed8', label='Ventas (núcleo transaccional)'),
        mpatches.Patch(color='#065f46', label='Clientes y Productos'),
        mpatches.Patch(color='#92400e', label='Tiendas'),
        mpatches.Patch(color='#7c3aed', label='Devoluciones'),
        mpatches.Patch(color='#b45309', label='Catálogos y zonas'),
        mpatches.Patch(color='#374151', label='Inventario (no usado en DWH)'),
    ]
    ax.legend(handles=legend, loc='lower left', fontsize=7,
              facecolor='#1e2130', edgecolor='#3d4466', labelcolor='white')

    plt.tight_layout()
    plt.savefig('docs/er_origen.png', dpi=150,
                bbox_inches='tight', facecolor='#0f1117')
    plt.close()
    print("✅ docs/er_origen.png generado")


if __name__ == "__main__":
    draw_star_schema()
    draw_er_origen()
    print("\n✅ Diagramas guardados en docs/")