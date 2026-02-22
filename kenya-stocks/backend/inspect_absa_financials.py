import json
from pathlib import Path

from fetch_nse_results_2023_2025 import DATA_ROOT  # type: ignore


def main() -> None:
    path = DATA_ROOT / "financials.json"
    if not path.exists():
        raise SystemExit(f"financials.json not found at {path}. Run extract_financials_from_pdfs.py first.")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise SystemExit("financials.json does not contain a list of records.")

    absa_rows = [
        r for r in data
        if r.get("company") and "absa" in str(r["company"]).lower()
    ]

    absa_rows.sort(key=lambda r: (r.get("year") or 0, r.get("period") or ""))

    print(f"Found {len(absa_rows)} ABSA rows\n")

    for r in absa_rows:
        year = r.get("year")
        period = r.get("period")
        rev = r.get("revenue")
        pat = r.get("profit_after_tax")
        eps = r.get("basic_eps")
        dps = r.get("dividend_per_share")
        print(
            f"{year} | {period} | Rev={rev} | PAT={pat} | EPS={eps} | Div/Share={dps}"
        )


if __name__ == "__main__":
    main()
