from app.database import upsert_product_cost_config

data = [
    {'cat': 'RCA Fine COM 0.90 MM', 'min': 0.80, 'max': 0.90, 'gsm': 60, 'steel': 'Prime', 'conv': 'Wiping Fine'},
    {'cat': 'RCA Fine IS 0.90 MM', 'min': 0.80, 'max': 0.90, 'gsm': 75, 'steel': 'Prime', 'conv': 'Wiping Fine'},
    {'cat': 'RCA Wire BS GRADE Fine (0.8-0.9)', 'name': 'RCA Wire BS GRADE Fine', 'min': 0.80, 'max': 0.90, 'gsm': 155, 'steel': 'Prime', 'conv': 'Heavy Fine'},
    {'cat': 'RCA Fine COM 1.25MM', 'min': 0.91, 'max': 1.25, 'gsm': 60, 'steel': 'Prime', 'conv': 'Wiping Fine'},
    {'cat': 'RCA Fine IS 1.25MM', 'min': 0.91, 'max': 1.25, 'gsm': 90, 'steel': 'Prime', 'conv': 'Wiping Fine'},
    {'cat': 'RCA Wire BS GRADE Fine (0.91-1.25)', 'name': 'RCA Wire BS GRADE Fine', 'min': 0.91, 'max': 1.25, 'gsm': 155, 'steel': 'Prime', 'conv': 'Heavy Fine'},
    {'cat': 'GI Wire 60-90 GSM', 'min': 2.00, 'max': 4.00, 'gsm': 60, 'steel': 'Commercial', 'conv': 'Wiping Thick'},
    {'cat': 'GI Wire 90-120 GSM', 'min': 2.00, 'max': 4.00, 'gsm': 90, 'steel': 'Commercial', 'conv': 'Wiping Thick'},
    {'cat': 'GI Wire 120+ GSM', 'min': 2.00, 'max': 4.00, 'gsm': 120, 'steel': 'Commercial', 'conv': 'Wiping Thick'},
    {'cat': 'RCA Wire BS GRADE Thick', 'min': 2.00, 'max': 4.00, 'gsm': 260, 'steel': 'Prime', 'conv': 'Heavy Thick'},
    {'cat': 'ACSR (1.57-1.90)', 'name': 'ACSR', 'min': 1.57, 'max': 1.90, 'gsm': 210, 'steel': 'HC', 'conv': 'Heavy Fine'},
    {'cat': 'ACSR (1.91-4.09)', 'name': 'ACSR', 'min': 1.91, 'max': 4.09, 'gsm': 250, 'steel': 'HC', 'conv': 'Heavy Thick'},
    {'cat': 'RCA Fine COM 1.40-1.60 MM', 'min': 1.40, 'max': 1.60, 'gsm': 70, 'steel': 'Commercial', 'conv': 'Wiping Fine'},
    {'cat': 'RCA Fine IS 1.40-1.60 MM', 'min': 1.40, 'max': 1.60, 'gsm': 95, 'steel': 'Prime', 'conv': 'Wiping Fine'}
]

for row in data:
    cat_id = row['cat'].upper().replace(' ', '_').replace('.', '_').replace('-', '_').replace('(', '').replace(')', '')
    payload = {
        'category_id': cat_id,
        'category_name': row.get('name', row['cat']),
        'size_min': row['min'],
        'size_max': row['max'],
        'gsm_kg_per_mt': row['gsm'],
        'steel_type': row['steel'],
        'conversion_process': row['conv'],
        'steel_weight': 1050.0,
        'yield_loss_pct': 2.0,
        'min_margin_pct': 10.0,
        'max_margin_pct': 15.0
    }
    upsert_product_cost_config(payload)
    print(f"Upserted {payload['category_id']}")
