import json
data = json.load(open('data/nse/financials.json'))
kcb = [r for r in data if r.get('ticker') == 'KCB']
print('KCB records with H1 or missing period_end_date:')
for r in kcb:
    if 'H1' in str(r.get('period', '')):
        print(f"  period={r.get('period')}, period_end_date={r.get('period_end_date')}, period_type={r.get('period_type')}")
