"""Quick test of the 4 JSE extraction fixes."""
from extractors.ifrs_extractor import IFRSExtractor
from exchanges.jse import JSE

e = IFRSExtractor(exchange='JSE')
nse = IFRSExtractor(exchange='NSE')
jse = JSE()

pass_count = 0
fail_count = 0

def check(label, got, expected):
    global pass_count, fail_count
    if expected is None:
        ok = got is None
    elif isinstance(expected, float):
        ok = got is not None and abs(got - expected) < 0.001
    else:
        ok = got == expected
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: got={got!r} exp={expected!r}")
    if ok:
        pass_count += 1
    else:
        fail_count += 1

print("=== FIX #2: SCALE DETECTION ===")
check("R'000 -> thousands", e._detect_scale("in R'000"), "thousands")
check("thousands of rand", e._detect_scale("expressed in thousands of rand"), "thousands")
check("ZAR millions", e._detect_scale("ZAR millions"), "millions")
check("in millions", e._detect_scale("in millions"), "millions")
check("USD millions", e._detect_scale("USD millions"), "millions")
check("no scale -> single", e._detect_scale("random text only"), "single")

print("\n=== FIX #3: DPS NARRATIVE EXTRACTION ===")
check("70.0 cents/share", e._extract_dps_narrative("dividend per share of 70.0 cents", "ZAR"), 0.70)
check("proposed 120c", e._extract_dps_narrative("proposed dividend of 120 cents per share", "ZAR"), 1.20)
check("total dividend 35c", e._extract_dps_narrative("total dividend 35 cents per share", "ZAR"), 0.35)
check("final dividend 50c", e._extract_dps_narrative("final dividend 50 cents per share", "ZAR"), 0.50)
check("interim dividend 25c", e._extract_dps_narrative("interim dividend 25 cents per share", "ZAR"), 0.25)
check("no dividend -> None", e._extract_dps_narrative("no dividend mentioned", "ZAR"), None)

print("\n=== FIX #4: EPS NORMALIZATION ===")
check("500c -> 5.0 ZAR (cents text)", e._normalize_eps(500.0, "ZAR", "earnings per share in cents"), 5.0)
check("150c -> 1.5 ZAR (heuristic)", e._normalize_eps(150.0, "ZAR", "text"), 1.50)
check("1.5 ZAR noop", e._normalize_eps(1.5, "ZAR", "text"), 1.5)
check("NSE 25 KES noop", nse._normalize_eps(25.0, "KES", "text"), 25.0)
check("None -> None", e._normalize_eps(None, "ZAR", "text"), None)

print("\n=== FIX #4: PERIOD DETECTION (improved) ===")
check("year ended -> annual", e._detect_period_type("for the year ended 31 December 2024", "f"), "annual")
check("six months ended -> half_year", e._detect_period_type("six months ended 30 June 2024", "h1"), "half_year")
check("three months ended -> quarter", e._detect_period_type("three months ended 31 March 2024", "q1"), "quarter")
check("annual report kw -> annual", e._detect_period_type("annual report 2024", "annual_2024"), "annual")
check("h1/interim kw -> half_year", e._detect_period_type("h1 results interim report", "h1_2024"), "half_year")
check("default -> annual (not half_year)", e._detect_period_type("some random text", "random_file"), "annual")

print("\n=== FIX #1: PDF REGISTRY ===")
check("registry has 30 companies", len(jse._registry) >= 30, True)
for ticker in ["BHG", "NTC", "PRX", "BTI", "FSR", "SBK", "MTN"]:
    urls = jse.get_pdf_urls_from_registry(ticker)
    meta = jse.get_registry_meta(ticker)
    check(f"{ticker} has URLs", len(urls) > 0, True)
    check(f"{ticker} has currency", bool(meta.get("currency")), True)

print(f"\n{'='*40}")
print(f"TOTAL: {pass_count} passed, {fail_count} failed")
