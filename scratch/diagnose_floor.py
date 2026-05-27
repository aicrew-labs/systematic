import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'backend')
from app.pricing_engine import analyze
from app.schemas import AnalyzeRequest

req = AnalyzeRequest(
    customer_id=1047,
    customer_name='KEC Asian Cables Limited (Vadodara)',
    category_id='ACSR_1_91_4_09',
    quantity=None,
    mode='algo'
)

result = analyze(req)

print('=== CONTEXT CARDS ===')
for card in result.context_cards:
    print(f'  [{card.label}] {card.value}  --  {card.sub_text}')
