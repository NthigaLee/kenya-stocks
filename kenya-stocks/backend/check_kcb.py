import json

data = json.load(open('../data/nse/financials.json'))
kcb = [e for e in data if 'KCB' in (e.get('company') or '')]
print(f'Total entries: {len(data)}')
print(f'KCB entries: {len(kcb)}')
print()
print(f"{'Year':<6} {'Period':<20} {'NII (KES 000s)':>20} {'Total Assets':>20}")
print("-" * 70)
for e in sorted(kcb, key=lambda x: (x.get('year') or 0, str(x.get('period') or ''))):
    ni = e.get('net_interest_income')
    ta = e.get('total_assets')
    period = e.get('period') or '-'
    year = e.get('year') or '?'
    ni_str = f"{ni:,.0f}" if ni else "-"
    ta_str = f"{ta:,.0f}" if ta else "-"
    print(f"{str(year):<6} {period:<20} {ni_str:>20} {ta_str:>20}")
