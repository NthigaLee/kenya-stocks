// Full NSE Kenya stock list — all TradingView NSEKE tickers
// Source: TradingView markets/stocks-kenya (March 2026)
// Format: { TICKER: "Full Company Name" }
// TradingView symbol = "NSEKE:" + TICKER

const NSE_ALL_STOCKS = {
  "ABSA":  "Absa Bank Kenya Plc",
  "ALP":   "Alp Industrial Rei",
  "AMAC":  "Africa Mega Agricorp PLC",
  "BAT":   "British American Tobacco Kenya PLC",
  "BKG":   "BK Group Plc",
  "BOC":   "B.O.C Kenya Ltd",
  "BRIT":  "Britam Holdings PLC",
  "CARB":  "Carbacid Investments Ltd",
  "CGEN":  "Car & General (Kenya) PLC",
  "CIC":   "CIC Insurance Group PLC",
  "COOP":  "Co-operative Bank of Kenya Ltd",
  "CRWN":  "Crown Paints Kenya PLC",
  "CTUM":  "Centum Investment Company PLC",
  "DTK":   "Diamond Trust Bank Kenya Ltd",
  "EABL":  "East African Breweries Plc",
  "EGAD":  "Eaagads Ltd",
  "EQTY":  "Equity Group Holdings Limited",
  "EVRD":  "Eveready East Africa PLC",
  "FTGH":  "Flame Tree Group Holdings Ltd",
  "HAFR":  "Home Afrika Ltd",
  "HFCK":  "HF Group PLC",
  "IMH":   "I&M Group Plc",
  "JUB":   "Jubilee Holdings Ltd",
  "KAPC":  "Kapchorua Tea Kenya PLC",
  "KCB":   "KCB Group PLC",
  "KEGN":  "Kenya Electricity Generating Company PLC",
  "KNRE":  "Kenya Re-Insurance Corporation Ltd",
  "KPC":   "Kenya Pipeline Company PLC",
  "KPLC":  "Kenya Power & Lighting Company Plc",
  "KQ":    "Kenya Airways PLC",
  "KUKZ":  "Kakuzi PLC",
  "KURV":  "Kurwitu Ventures Ltd",
  "LBTY":  "Liberty Kenya Holdings Ltd",
  "LIMT":  "Limuru Tea Plc",
  "LKL":   "Longhorn Publishers Limited",
  "NBV":   "Nairobi Business Ventures Ltd",
  "NCBA":  "NCBA Group PLC",
  "NMG":   "Nation Media Group Limited",
  "NSE":   "Nairobi Securities Exchange PLC",
  "OCH":   "Olympia Capital Holdings Limited",
  "PORT":  "East African Portland Cement Co Ltd",
  "SASN":  "Sasini PLC",
  "SBIC":  "Stanbic Holdings Plc",
  "SCAN":  "WPP Scangroup Plc",
  "SCBK":  "Standard Chartered Bank Kenya Ltd",
  "SCOM":  "Safaricom PLC",
  "SGL":   "Standard Group PLC",
  "SKL":   "Shri Krishana Overseas Ltd",
  "SLAM":  "Sanlam Allianz Holdings (Kenya) PLC",
  "SMER":  "Sameer Africa PLC",
  "TOTL":  "TotalEnergies Marketing Kenya Plc",
  "TPSE":  "TPS Eastern Africa PLC",
  "UCHM":  "Uchumi Supermarkets PLC",
  "UMME":  "Umeme Ltd",
  "UNGA":  "Unga Group PLC",
  "WTK":   "Williamson Tea Kenya PLC",
  "XPRS":  "Express Kenya Ltd"
};

// Note: internal data (financials.json) only covers 7 companies:
// ABSA, COOP, DTK (mapped as DTK not DTB in TV), EQTY, KCB, NCBA, SCBK
// For all other stocks, the price chart will still work — just no financial overlay data.
// DTB internal ticker maps to DTK on TradingView.
