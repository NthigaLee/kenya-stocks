import json, re
content = open('frontend/data.js', encoding='utf-8').read()
# Extract JSON object from "const NSE_COMPANIES = { ... };"
match = re.search(r'const NSE_COMPANIES = (\{.*\});', content, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    kcb = data['KCB']
    print('KCB quarters in data.js:')
    for q in kcb['quarters']:
        period = q.get('period')
        dateKey = q.get('dateKey')
        print("  period='%s' dateKey='%s'" % (period, dateKey))
else:
    print("Could not extract JSON from data.js")
