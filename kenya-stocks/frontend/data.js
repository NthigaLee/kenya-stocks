// Kenya NSE Companies — Embedded Financial Data
// Units: Revenue/NII/PAT in KES thousands (except Safaricom = KES millions)
// Source: NSE annual results PDFs (via extraction pipeline)
// Note: Some values may have extraction artifacts — review COMPANY_NOTES.md

const NSE_COMPANIES = {

  ABSA: {
    name: "ABSA Bank Kenya PLC",
    ticker: "ABSA",
    exchange: "NSE",
    sector: "Banking",
    logo: "🏦",
    currency: "KES",
    units: "thousands",
    latestPrice: 14.20,   // approximate, update when live prices available
    annuals: [
      { year: 2019, revenue: 15374667, pat: 3877714,  nii: 10950301, eps: 0.66, dps: 0.20 },
      { year: 2020, revenue: 24321027, pat: 5347181,  nii: 16801899, eps: 0.98, dps: 1.10 },
      { year: 2022, revenue: 33585983, pat: null,     nii: 23280874, eps: 0.69, dps: 1.10 },
      { year: 2023, revenue: 20230852, pat: null,     nii: 14343849, eps: 1.09, dps: 0.20 },
      { year: 2024, revenue: 44555765, pat: 30681559, nii: 32131322, eps: 2.55, dps: 1.35 },
    ]
  },

  STANCHART: {
    name: "Standard Chartered Bank Kenya",
    ticker: "SCBK",
    exchange: "NSE",
    sector: "Banking",
    logo: "🏦",
    currency: "KES",
    units: "thousands",
    latestPrice: 195.00,
    annuals: [
      { year: 2015, revenue: null,     pat: 3877266,  nii: null,     eps: 19.60, dps: 17.00 },
      { year: 2019, revenue: 14663490, pat: 4705902,  nii: 9842875,  eps: 12.76, dps: 5.00  },
      { year: 2020, revenue: 13231587, pat: 3233064,  nii: 9371914,  eps: 8.26,  dps: 12.50 },
      { year: 2022, revenue: 14112995, pat: 9043839,  nii: 9115386,  eps: 12.69, dps: 19.00 },
      { year: 2024, revenue: 33977048, pat: 12057935, nii: 22223065, eps: 31.47, dps: 22.00 },
    ]
  },

  SAFARICOM: {
    name: "Safaricom PLC",
    ticker: "SCOM",
    exchange: "NSE",
    sector: "Telecom",
    logo: "📱",
    currency: "KES",
    units: "millions",  // Safaricom reports in KES millions
    latestPrice: 15.85,
    annuals: [
      { year: 2023, revenue: 295692, pat: 52483, nii: null, eps: 1.55, dps: 1.20 },
      { year: 2024, revenue: 335353, pat: 42658, nii: null, eps: 1.57, dps: null  },
    ]
  },

  KCB: {
    name: "KCB Group PLC",
    ticker: "KCB",
    exchange: "NSE",
    sector: "Banking",
    logo: "🏦",
    currency: "KES",
    units: "thousands",
    latestPrice: 34.50,
    annuals: [
      { year: 2019, revenue: null, pat: null,      nii: 21924708, eps: 0.41, dps: 0.06 },
      { year: 2020, revenue: null, pat: null,      nii: 25001099, eps: 0.26, dps: 0.30 },
      { year: 2022, revenue: null, pat: 19521783,  nii: 30321254, eps: 0.61, dps: 0.20 },
      { year: 2023, revenue: null, pat: 15595576,  nii: 28522558, eps: 0.52, dps: 0.58 },
    ]
  },

  EQUITY: {
    name: "Equity Group Holdings",
    ticker: "EQTY",
    exchange: "NSE",
    sector: "Banking",
    logo: "🏦",
    currency: "KES",
    units: "thousands",
    latestPrice: 40.50,
    annuals: [
      { year: 2020, revenue: 39980566, pat: null, nii: 24430341, eps: 479.31, dps: 400.00 },
      { year: 2022, revenue: 33898064, pat: null, nii: 22241691, eps: 479.99, dps: 233.33 },
      { year: 2024, revenue: 85951042, pat: null, nii: 58411267, eps: 1113.13, dps: 600.00 },
    ]
  },

  COOP: {
    name: "Co-operative Bank of Kenya",
    ticker: "COOP",
    exchange: "NSE",
    sector: "Banking",
    logo: "🏦",
    currency: "KES",
    units: "thousands",
    latestPrice: 12.35,
    annuals: [
      { year: 2020, revenue: 53829689, pat: 14528812, nii: 36348966, eps: 1.98, dps: 1.00 },
      { year: 2023, revenue: 35370987, pat: 9445250,  nii: 21546517, eps: 2.08, dps: 1.50 },
    ]
  },

};
