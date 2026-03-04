"""Quick fix: swap CompanyConfig dataclass field order to match constructor call order."""
import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("backend/populate.py", "r", encoding="utf-8") as f:
    content = f.read()

old = (
    "    keywords:     List[str]\n"
    "    latest_price: float = 0.0\n"
    '    emoji:        str   = "\\U0001f3e2"'
)

# Try a simpler approach: just find and replace the relevant lines
import re

# Replace the dataclass body
old_block = (
    "    keywords:     List[str]\n"
    "    latest_price: float = 0.0\n"
)
new_block = (
    "    latest_price: float = 0.0\n"
    "    keywords:     List[str] = field(default_factory=list)\n"
)

# Remove the emoji line (we'll keep it but move it)
if old_block in content:
    content = content.replace(old_block, new_block)
    # Also fix the emoji line - move it before keywords
    content = content.replace(
        "    latest_price: float = 0.0\n    keywords:     List[str] = field(default_factory=list)\n"
        '    emoji:        str   = "\U0001f3e2"',
        "    latest_price: float = 0.0\n"
        '    emoji:        str   = "\U0001f3e2"\n'
        "    keywords:     List[str] = field(default_factory=list)"
    )
    with open("backend/populate.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Patch applied.")
else:
    print("Block not found. Trying regex approach...")
    # Find the dataclass definition
    m = re.search(r'(@dataclass\nclass CompanyConfig:.*?)(?=\n\ndef )', content, re.DOTALL)
    if m:
        print("Found dataclass at:", m.start(), m.end())
        print(repr(m.group(0)[:500]))
    else:
        print("Dataclass not found")
        # Show around keywords
        idx = content.find("keywords")
        print(repr(content[max(0,idx-200):idx+200]))
