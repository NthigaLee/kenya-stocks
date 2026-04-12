import re

with open('frontend/data.js') as f:
    raw = f.read()

tickers = re.findall(r'^  ([A-Z]+): \{', raw, re.MULTILINE)
for ticker in tickers:
    # Find annual block
    block_match = re.search(rf'  {ticker}: \{{.*?annuals: \[(.*?)\]', raw, re.DOTALL)
    if block_match:
        years = re.findall(r'"year": (\d+)', block_match.group(1))
        print(f'{ticker}: annuals={years}')
    else:
        print(f'{ticker}: no annuals found')
    
    # Find quarters block
    q_match = re.search(rf'  {ticker}: \{{.*?quarters: \[(.*?)\]', raw, re.DOTALL)
    if q_match:
        qperiods = re.findall(r'"period": "([^"]+)"', q_match.group(1))
        print(f'  quarters={qperiods}')
    else:
        print(f'  quarters=none')
