import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'backend')
from app.pricing_engine import analyze
from app.schemas import AnalyzeRequest

# Simulate quoting GI-THIN for KEC
req = AnalyzeRequest(
    customer_id=1047,
    customer_name='KEC Asian Cables Limited (Vadodara)',
    category_id='GI-THIN',
    quantity=None,
    mode='algo'
)

result = analyze(req)

print('=== CONTEXT CARDS ===')
for card in result.context_cards:
    print(f'  [{card.label}] {card.value}  --  {card.sub_text}')

print('\n=== MARKET SIGNALS ===')
for sig in result.market_signals:
    print(f'  [{sig.color}] {sig.text}')

print('\n=== PRICE RANGE ===')
pr = result.price_range
print(f'  Suggested: {pr.suggested_low} - {pr.suggested_high}')
print(f'  Market:    {pr.market_low} - {pr.market_high} (median {pr.market_median})')
print(f'  Samples:   {pr.sample_size}')

print('\n=== REASONING ===')
print(result.reasoning)
