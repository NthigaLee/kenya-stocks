const fs = require('fs');

const descriptions = {
  ABSA: "ABSA Bank Kenya, a subsidiary of South Africa's Absa Group, offers retail, corporate, and investment banking services across the country.",
  BAMB: "Bamburi Cement is East Africa's largest cement manufacturer, producing construction materials and operating quarrying and waste management businesses.",
  BATK: "British American Tobacco Kenya manufactures and markets cigarettes and tobacco products, holding a dominant share of Kenya's tobacco market.",
  BKG: "BK Group is Rwanda's largest bank by assets, cross-listed on the NSE, offering retail, corporate, and investment banking services across East Africa.",
  BOC: "BOC Kenya manufactures and distributes industrial, medical, and special gases including oxygen, nitrogen, and acetylene to various industries.",
  BRIT: "Britam Holdings is a diversified financial services group offering insurance, asset management, and banking products across Sub-Saharan Africa.",
  CARB: "Carbacid Investments is Kenya's sole producer of carbon dioxide gas, supplying the beverage, food processing, and welding industries.",
  CFC: "Stanbic Bank Kenya (CFC Stanbic Holdings) is a subsidiary of South Africa's Standard Bank Group, providing corporate, investment, and personal banking.",
  COOP: "Co-operative Bank of Kenya is the country's third-largest bank by assets, deeply rooted in the co-operative movement with a wide retail network.",
  CPKL: "Centum Investment is a leading African investment company with a diversified portfolio spanning private equity, real estate, and fast-moving consumer goods.",
  DTK: "Diamond Trust Bank Kenya is a mid-tier commercial bank with a strong presence in East Africa, focused on SME and retail banking.",
  EABL: "East African Breweries (EABL) is the region's leading beverages company, home to iconic brands including Tusker lager, Kenya Cane, and Johnnie Walker.",
  EAPC: "East African Portland Cement is a Kenyan cement manufacturer majority-owned by the government, producing Portland and other cement products.",
  EQTY: "Equity Group Holdings is Kenya's largest bank by customer numbers, with operations in 7 African countries and a strong focus on financial inclusion.",
  FANB: "Faida Investment Bank is a Nairobi-based boutique stockbroker and investment bank offering brokerage, advisory, and portfolio management services.",
  FTGH: "Fairtrade Holdings (formerly CMC Holdings) is a motor vehicle distributor and dealer representing major international automotive brands in Kenya.",
  HAFR: "Home Afrika is a Kenyan real estate development company focused on affordable and mid-market residential housing projects.",
  HBZE: "Habib AG Zurich Bank Kenya is a privately held niche bank serving the trade finance and personal banking needs of the Asian business community.",
  HFCK: "HF Group (Housing Finance) is Kenya's oldest mortgage lender, providing home loans, savings, and banking services to retail and corporate clients.",
  IMH: "I&M Holdings is a regional mid-tier bank with operations in Kenya, Tanzania, Rwanda, and Mauritius, focused on corporate and retail banking.",
  JUB: "Jubilee Holdings is Kenya's largest insurer by premium income, offering life, general, and medical insurance across East and Central Africa.",
  KAPA: "Kapchorua Tea Company operates tea estates in Kenya's Rift Valley, producing and exporting black tea to international auction and direct markets.",
  KCB: "KCB Group is Kenya's largest bank by assets, operating across 7 African countries with a strong focus on retail, corporate, and digital banking.",
  KEGN: "KenGen generates approximately 75% of Kenya's installed electricity capacity, primarily from geothermal and hydro sources, and is majority state-owned.",
  KPLC: "Kenya Power & Lighting Company is the sole electricity distributor in Kenya, managing the national transmission and distribution grid.",
  NBK: "National Bank of Kenya is a state-linked commercial bank and subsidiary of KCB Group, offering retail and corporate banking services nationwide.",
  NCBA: "NCBA Group is a pan-African bank best known for co-creating M-Shwari with Safaricom, offering retail, corporate, and digital financial services.",
  NMG: "Nation Media Group is East and Central Africa's largest independent media house, operating newspapers, TV, radio, and digital platforms across the region.",
  NSE: "The Nairobi Securities Exchange is Kenya's principal stock exchange, facilitating trading in equities, bonds, and derivatives, and itself listed on the bourse.",
  SASN: "Sasini is a Kenyan agribusiness company with tea and coffee estates, producing and exporting branded and bulk tea and coffee for global markets.",
  SCAN: "Scangroup (WPP Scangroup) is Sub-Saharan Africa's largest marketing and communications group, operating agencies across advertising, PR, and digital.",
  SCBK: "Standard Chartered Bank Kenya is part of the global Standard Chartered network, offering premium retail, corporate, and private banking services.",
  SGL: "Stanlib Fahari I-REIT is Kenya's first listed Real Estate Investment Trust, owning and managing a portfolio of income-generating commercial properties.",
  SLAM: "Sanlam Kenya (formerly Pan Africa Insurance) is a life insurance and financial services company, part of the South African Sanlam Group.",
  TCL: "Trans-Century is a Kenyan infrastructure and engineering company with interests in power cables, transformers, and water infrastructure across Africa.",
  TPSE: "TPS Eastern Africa operates the Serena Hotels & Resorts chain, providing luxury hospitality across Kenya, Tanzania, Uganda, Rwanda, and Mozambique.",
  UMME: "Umeme is Uganda's principal electricity distribution company, cross-listed on the NSE, managing the national distribution network under a government concession.",
  UNGA: "Unga Group is Kenya's leading grain miller, producing wheat flour, maize flour, and animal feeds under the Unga, Jogoo, and Starehe brands.",
  WTK: "Williamson Tea Kenya operates commercial tea estates and exports high-quality Kenyan tea to global markets, with operations in the Kericho highlands.",
  XPRS: "Express Kenya is a courier and logistics company providing parcel delivery, freight forwarding, and warehousing services across the country."
};

let content = fs.readFileSync('data.js', 'utf8');

for (const [ticker, desc] of Object.entries(descriptions)) {
  // Find the ticker block, then find the logo line within it and insert description after
  const escapedDesc = desc.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  // Match logo line inside the ticker's object block
  // We'll find '"ticker": "TICKER"' then replace the logo line following it
  const tickerPattern = new RegExp(
    '("ticker":\\s*"' + ticker + '"[\\s\\S]*?)"logo":\\s*"([^"]*)"',
    ''
  );
  content = content.replace(tickerPattern, (match, before, logoVal) => {
    // Check if description already exists (avoid double-insert)
    if (match.includes('"description"')) return match;
    return before + '"logo": "' + logoVal + '",\n    "description": "' + escapedDesc + '"';
  });
}

fs.writeFileSync('data.js', content, 'utf8');
console.log('Done! Descriptions injected into data.js');
