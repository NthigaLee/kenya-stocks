import json
d = json.load(open('../data/nse/financials.json'))
for e in d:
    ck = e.get('company_key', e.get('company', '?'))
    ps = e.get('period_str', e.get('period', '?'))
    pat = e.get('profit_after_tax')
    rev = e.get('revenue')
    eps = e.get('basic_eps')
    print(f"{ck:12} {ps:10} PAT={pat} Rev={rev} EPS={eps}")
