import json
data = json.load(open('../data/nse/financials.json'))
kcb = [e for e in data if 'KCB' in (e.get('company') or '')]
print(f'KCB entries: {len(kcb)}')
for e in sorted(kcb, key=lambda x: (x.get('year') or 0)):
    yr  = e.get('year')
    pt  = e.get('period_type') or '?'
    per = str(e.get('period') or '-')
    ped = e.get('period_end_date') or '-'
    tk  = e.get('ticker') or '-'
    nii = e.get('net_interest_income')
    print(f'  {yr} | {pt:12} | {per:28} | ped={ped:12} | tick={tk} | nii={nii}')
