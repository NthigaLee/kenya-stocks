import json

content = open('frontend/data.js').read()
start = content.find('{')
data = json.loads(content[start:-3])

kcb = data['KCB']
print("KCB quarters:")
for q in kcb['quarters']:
    print(f"  period='{q.get('period')}' dateKey='{q.get('dateKey')}'")

print("\nKCB annuals:")
for a in kcb['annuals']:
    print(f"  period='{a.get('period')}' dateKey='{a.get('dateKey')}'")
