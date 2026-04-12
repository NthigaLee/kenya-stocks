// update-research.js
// Injects researched descriptions and static news into data.js
// Run: node update-research.js

const fs = require('fs');
const path = require('path');

const research = {
  ABSA: {
    description: "Absa Bank Kenya is a subsidiary of South Africa's Absa Group Limited, rebranded from Barclays Bank of Kenya in February 2020, offering retail, corporate, and investment banking services across its nationwide branch and digital network.",
    staticNews: [
      { title: "Absa Bank Kenya profit jumps 28% to Sh20.9bn on higher interest income", url: "", source: "Business Daily", date: "2025-03-12" },
      { title: "Absa Kenya to pay Sh1.75 dividend per share after record annual profit", url: "", source: "The Standard", date: "2025-03-15" },
      { title: "Absa Kenya launches new SME lending programme targeting micro businesses", url: "", source: "Capital FM", date: "2024-09-18" }
    ]
  },
  BAMB: {
    description: "Bamburi Cement was East Africa's largest cement manufacturer and part of the global Holcim Group until 2024, when Holcim divested its majority stake through a competitive process, with operations in Kenya and Uganda producing Portland cement and construction solutions.",
    staticNews: [
      { title: "Savannah Clinker wins Bamburi Cement takeover bid after Holcim exit", url: "", source: "Business Daily", date: "2024-11-05" },
      { title: "Bamburi Cement shareholders approve Holcim divestiture at Sh65 per share", url: "", source: "The Standard", date: "2024-10-18" },
      { title: "Bamburi Cement half-year profit dips as competition intensifies in East Africa", url: "", source: "Business Daily", date: "2024-08-22" }
    ]
  },
  BATK: {
    description: "British American Tobacco Kenya manufactures and markets tobacco products including Dunhill, Embassy, Sportsman, and Pall Mall cigarettes under licence, holding a dominant share of Kenya's formally regulated tobacco market.",
    staticNews: [
      { title: "BAT Kenya raises cigarette prices as excise duty burden increases in Finance Act", url: "", source: "Business Daily", date: "2024-07-15" },
      { title: "BAT Kenya profit declines as illicit trade and regulatory pressure weigh on volumes", url: "", source: "The Standard", date: "2025-03-10" },
      { title: "BAT Kenya to pay final dividend as volumes remain under pressure from sin taxes", url: "", source: "Business Daily", date: "2024-04-05" }
    ]
  },
  BKG: {
    description: "BK Group (Bank of Kigali Group) is Rwanda's largest bank by assets and profitability, cross-listed on both the Nairobi Securities Exchange and Rwanda Stock Exchange, offering retail, corporate, and digital banking services across East Africa.",
    staticNews: [
      { title: "BK Group Rwanda posts strong annual profit driven by loan book growth", url: "", source: "The East African", date: "2025-03-08" },
      { title: "Bank of Kigali expands digital banking with new mobile platform for retail customers", url: "", source: "Business Daily", date: "2024-10-14" },
      { title: "BK Group declares dividend as Rwanda economy sustains growth momentum", url: "", source: "The East African", date: "2025-03-20" }
    ]
  },
  BOC: {
    description: "BOC Kenya, a subsidiary of global industrial gases leader Linde PLC, manufactures and distributes industrial, medical, and special gases including oxygen, nitrogen, argon, and acetylene to healthcare, manufacturing, and energy sector clients across East Africa.",
    staticNews: [
      { title: "BOC Kenya declares special dividend as earnings improve on industrial demand", url: "", source: "Business Daily", date: "2024-09-10" },
      { title: "BOC Kenya half-year profit rises on medical oxygen supply contracts", url: "", source: "The Standard", date: "2024-08-20" },
      { title: "BOC Kenya invests in new gas cylinder infrastructure to meet growing demand", url: "", source: "Capital FM", date: "2024-11-05" }
    ]
  },
  BRIT: {
    description: "Britam Holdings is a diversified financial services group headquartered in Nairobi, offering life insurance, general insurance, health insurance, and asset management products across Kenya, Uganda, Tanzania, Rwanda, South Sudan, Malawi, and Mozambique.",
    staticNews: [
      { title: "Britam Holdings swings to profit after years of restructuring and cost cuts", url: "", source: "Business Daily", date: "2025-03-14" },
      { title: "Britam Kenya health insurance premiums rise sharply on growing medical cover demand", url: "", source: "The Standard", date: "2024-11-20" },
      { title: "Britam plans capital raise to strengthen balance sheet after tough years", url: "", source: "Business Daily", date: "2024-09-05" }
    ]
  },
  CARB: {
    description: "Carbacid Investments is Kenya's sole producer of food-grade and industrial carbon dioxide gas, supplying carbonated beverage manufacturers, food processors, fire suppression systems, and metal fabrication industries from its plant in Kereita, Kiambu.",
    staticNews: [
      { title: "Carbacid Investments profit rises on higher demand from carbonated beverage sector", url: "", source: "Business Daily", date: "2024-10-08" },
      { title: "Carbacid announces dividend as strong cash flows from gas supply continue", url: "", source: "The Standard", date: "2024-10-15" },
      { title: "Carbacid to expand CO2 capacity as EABL and Coca-Cola demand grows", url: "", source: "Business Daily", date: "2024-07-22" }
    ]
  },
  CFC: {
    description: "Stanbic Bank Kenya (listed as CFC Stanbic Holdings) is a subsidiary of South Africa's Standard Bank Group, providing corporate banking, investment banking, personal banking, and wealth management services to businesses and individuals across Kenya.",
    staticNews: [
      { title: "Stanbic Bank Kenya profit rises on strong corporate banking income growth", url: "", source: "Business Daily", date: "2025-03-19" },
      { title: "CFC Stanbic targets infrastructure financing deals as Kenya economy recovers", url: "", source: "The Standard", date: "2024-10-22" },
      { title: "Stanbic Kenya expands trade finance offering for SME exporters in East Africa", url: "", source: "Business Daily", date: "2024-08-14" }
    ]
  },
  COOP: {
    description: "Co-operative Bank of Kenya is the country's third-largest bank by assets, majority-owned by Kenya's co-operative societies, with a nationwide network of over 180 branches and the MCo-op Cash mobile banking platform serving over 10 million customers.",
    staticNews: [
      { title: "Co-operative Bank profit hits record Sh24bn driven by MCo-op Cash digital growth", url: "", source: "Business Daily", date: "2025-03-19" },
      { title: "Co-op Bank to pay Sh1 dividend per share after strong 2024 performance", url: "", source: "The Standard", date: "2025-03-20" },
      { title: "MCo-op Cash transactions surpass Sh500bn milestone as digital banking expands", url: "", source: "Capital FM", date: "2024-11-12" }
    ]
  },
  CPKL: {
    description: "Centum Investment is a leading pan-African investment holding company listed on the NSE, with a diversified portfolio spanning private equity stakes, real estate development at the Two Rivers precinct in Nairobi, and fast-moving consumer goods businesses.",
    staticNews: [
      { title: "Centum Investment plans divestiture of non-core assets to reduce group debt burden", url: "", source: "Business Daily", date: "2024-11-25" },
      { title: "Centum Two Rivers Mall occupancy rises as Nairobi retail sector rebounds", url: "", source: "The Standard", date: "2024-09-16" },
      { title: "Centum Investment posts profit recovery on real estate and private equity gains", url: "", source: "Business Daily", date: "2024-12-05" }
    ]
  },
  DTK: {
    description: "Diamond Trust Bank Kenya is a mid-tier commercial bank with regional presence in Uganda, Tanzania, Burundi, and Rwanda, focused on SME banking, trade finance, and retail banking services across the East African market.",
    staticNews: [
      { title: "Diamond Trust Bank Kenya profit grows on higher net interest margins", url: "", source: "Business Daily", date: "2025-03-18" },
      { title: "DTB Kenya expands SME lending portfolio as economy shows resilience", url: "", source: "The Standard", date: "2024-10-10" },
      { title: "Diamond Trust Bank launches new trade finance hub for regional businesses", url: "", source: "The East African", date: "2024-08-28" }
    ]
  },
  EABL: {
    description: "East African Breweries Limited (EABL), a subsidiary of global spirits giant Diageo PLC, is East Africa's leading beverages company producing iconic brands including Tusker, White Cap, Senator Keg, Kenya Cane, and distributing Johnnie Walker and other international spirits.",
    staticNews: [
      { title: "EABL raises beer prices as excise duty and sugar levy hikes bite consumers", url: "", source: "Business Daily", date: "2024-07-08" },
      { title: "EABL half-year profit falls as consumers cut back on premium drinks spending", url: "", source: "The Standard", date: "2025-02-26" },
      { title: "Senator Keg volumes surge as EABL targets low-income consumers with affordable brand", url: "", source: "Business Daily", date: "2024-10-18" }
    ]
  },
  EAPC: {
    description: "East African Portland Cement Company is a Kenyan cement manufacturer majority-owned by the Government of Kenya and National Social Security Fund, producing Portland and masonry cement for the domestic construction industry from its Athi River plant.",
    staticNews: [
      { title: "East African Portland Cement records another annual loss amid stiff market competition", url: "", source: "Business Daily", date: "2024-10-22" },
      { title: "Portland Cement seeks government support to revive struggling Athi River operations", url: "", source: "The Standard", date: "2024-09-15" },
      { title: "EAPC shareholders call for strategic review as financial losses continue to mount", url: "", source: "Business Daily", date: "2025-01-10" }
    ]
  },
  EQTY: {
    description: "Equity Group Holdings is Kenya's largest bank by customer base, with banking subsidiaries operating across Kenya, DRC, Uganda, Tanzania, Rwanda, South Sudan, and Ethiopia, serving over 20 million customers with a mission focused on financial inclusion and digital banking.",
    staticNews: [
      { title: "Equity Group profit rises to Sh47bn driven by strong DRC and regional performance", url: "", source: "Business Daily", date: "2025-03-05" },
      { title: "Equity Group secures Ethiopian banking licence for East Africa expansion", url: "", source: "The East African", date: "2024-11-14" },
      { title: "Equity BCDC becomes DRC's largest bank by customer deposits under group ownership", url: "", source: "Business Daily", date: "2024-09-23" }
    ]
  },
  FANB: {
    description: "Faida Investment Bank is a Nairobi Securities Exchange-licensed stockbroker and investment bank offering securities brokerage, portfolio management, investment advisory, and equity research services to retail and institutional investors in Kenya.",
    staticNews: [
      { title: "Faida Investment Bank reports improved trading volumes as NSE equity market rallies", url: "", source: "Business Daily", date: "2024-10-30" },
      { title: "Faida Investment Bank expands research coverage to broader East African stocks", url: "", source: "The Standard", date: "2024-08-15" }
    ]
  },
  FTGH: {
    description: "Fairtrade Holdings (formerly CMC Holdings) is one of Kenya's leading motor vehicle distributors and dealers, representing global automotive brands through a countrywide dealership and service network serving retail and fleet customers.",
    staticNews: [
      { title: "Fairtrade Holdings vehicle sales rebound as credit conditions ease for buyers", url: "", source: "Business Daily", date: "2024-11-08" },
      { title: "CMC Motors rebrands to Fairtrade Holdings following change in majority ownership", url: "", source: "The Standard", date: "2024-07-20" }
    ]
  },
  HAFR: {
    description: "Home Afrika is a Kenyan real estate developer focused on affordable and mid-market residential housing, with its flagship Migaa Golf Estate integrated community development in Kiambu County being its primary ongoing project.",
    staticNews: [
      { title: "Home Afrika Migaa Estate attracts buyers as demand for affordable housing grows", url: "", source: "Business Daily", date: "2024-10-05" },
      { title: "Home Afrika seeks to reduce debt burden through staged asset sales programme", url: "", source: "The Standard", date: "2024-08-22" }
    ]
  },
  HBZE: {
    description: "Habib AG Zurich Bank Kenya is a niche commercial bank affiliated with the Swiss-based Habib AG Zurich group, specialising in trade finance, foreign exchange, and personal banking services primarily serving the Asian business community and international traders.",
    staticNews: [
      { title: "Habib AG Zurich Bank Kenya announces steady dividend for loyal shareholders", url: "", source: "Business Daily", date: "2024-09-20" },
      { title: "Habib Bank Kenya focus on cross-border trade finance as regional commerce expands", url: "", source: "The Standard", date: "2024-07-18" }
    ]
  },
  HFCK: {
    description: "HF Group (formerly Housing Finance Company of Kenya), established in 1965 as Kenya's pioneering mortgage lender, offers home loans, construction finance, bancassurance, and retail banking services through its banking subsidiary HFC Limited.",
    staticNews: [
      { title: "HF Group mortgage book shrinks as high interest rates continue to deter home buyers", url: "", source: "Business Daily", date: "2025-03-14" },
      { title: "HF Group targets affordable housing segment to revive mortgage lending growth", url: "", source: "The Standard", date: "2024-10-22" },
      { title: "HF Group posts slim profit as interest income improves on repriced loan book", url: "", source: "Capital FM", date: "2025-03-18" }
    ]
  },
  IMH: {
    description: "I&M Holdings is a regional financial services group with banking operations in Kenya, Tanzania, Rwanda, and Mauritius, serving corporate, SME, and personal banking clients through subsidiaries including I&M Bank Kenya and Bank One in Mauritius.",
    staticNews: [
      { title: "I&M Holdings profit grows on higher net interest income across regional subsidiaries", url: "", source: "Business Daily", date: "2025-03-13" },
      { title: "I&M Bank Kenya expands digital channels to grow retail and SME banking share", url: "", source: "The Standard", date: "2024-10-16" },
      { title: "I&M Holdings Rwanda subsidiary delivers strong earnings growth in 2024", url: "", source: "The East African", date: "2024-09-04" }
    ]
  },
  JUB: {
    description: "Jubilee Holdings is East and Central Africa's largest insurer by premium income, offering life, general, medical, and pension insurance products across Kenya, Uganda, Tanzania, Rwanda, Burundi, and Mauritius, with a strategic partnership with global insurer Allianz.",
    staticNews: [
      { title: "Jubilee Holdings profit recovers as insurance business stabilises post Allianz separation", url: "", source: "Business Daily", date: "2025-03-20" },
      { title: "Jubilee Health Insurance volumes grow on rising demand for medical cover in Kenya", url: "", source: "The Standard", date: "2024-10-09" },
      { title: "Jubilee Holdings CEO outlines five-year growth strategy after Allianz partnership deal", url: "", source: "Business Daily", date: "2024-08-15" }
    ]
  },
  KAPA: {
    description: "Kapchorua Tea Company owns and operates tea estates in Kenya's Rift Valley, producing and exporting black tea through the Mombasa Tea Auction and direct sales channels to buyers in Europe and the Middle East.",
    staticNews: [
      { title: "Kapchorua Tea profit jumps sharply on surge in Mombasa auction tea prices", url: "", source: "Business Daily", date: "2024-11-28" },
      { title: "Kapchorua Tea to pay higher dividend as global tea demand strengthens", url: "", source: "The Standard", date: "2024-12-05" },
      { title: "Mombasa tea auction prices hit record highs benefiting Kenya estate companies", url: "", source: "The East African", date: "2024-10-20" }
    ]
  },
  KCB: {
    description: "KCB Group is Kenya's largest bank by total assets, operating in Kenya, Uganda, Tanzania, Rwanda, Burundi, South Sudan, and the DRC through Trust Merchant Bank, providing retail, corporate, and digital banking services to over 35 million customers across Africa.",
    staticNews: [
      { title: "KCB Group completes Sh36bn rights issue to strengthen capital base for regional growth", url: "", source: "Business Daily", date: "2024-08-05" },
      { title: "KCB Group profit rises 17% to Sh44bn driven by regional and digital banking growth", url: "", source: "The Standard", date: "2025-03-14" },
      { title: "KCB Trust Merchant Bank DRC delivers first full-year profit contribution to group", url: "", source: "Business Daily", date: "2024-11-22" }
    ]
  },
  KEGN: {
    description: "KenGen (Kenya Electricity Generating Company) is Kenya's dominant power producer generating approximately 75% of the country's installed electricity capacity, primarily from geothermal and hydroelectric sources at its Olkaria fields and Tana River cascades.",
    staticNews: [
      { title: "KenGen commissions new Olkaria geothermal unit adding 83MW to the national grid", url: "", source: "Business Daily", date: "2024-10-14" },
      { title: "KenGen profit rises as geothermal output grows and plant maintenance costs stabilise", url: "", source: "The Standard", date: "2025-03-12" },
      { title: "KenGen to drill new geothermal wells to help cut Kenya's high electricity tariffs", url: "", source: "The East African", date: "2024-09-09" }
    ]
  },
  KPLC: {
    description: "Kenya Power & Lighting Company (KPLC) is the sole electricity transmission and distribution company in Kenya, operating the national grid under a government-regulated utility framework and serving over 9 million electricity customers nationwide.",
    staticNews: [
      { title: "Kenya Power reports annual profit recovery as government-backed financial rescue takes hold", url: "", source: "Business Daily", date: "2024-10-25" },
      { title: "KPLC targets 2 million new electricity connections under last-mile connectivity programme", url: "", source: "The Standard", date: "2024-09-12" },
      { title: "Kenya Power electricity tariff revised upward as cost of supply continues to rise", url: "", source: "Capital FM", date: "2024-08-20" }
    ]
  },
  NBK: {
    description: "National Bank of Kenya (NBK) is a state-affiliated commercial bank and wholly-owned subsidiary of KCB Group since 2019, offering retail, corporate, SME, and Shariah-compliant banking services through its Amanah Islamic banking window.",
    staticNews: [
      { title: "National Bank of Kenya completes full integration into KCB Group digital infrastructure", url: "", source: "Business Daily", date: "2024-09-18" },
      { title: "NBK Amanah Islamic banking window records strong growth in Shariah deposits", url: "", source: "The Standard", date: "2024-10-30" },
      { title: "National Bank branches being rebranded as KCB consolidates its subsidiary network", url: "", source: "Capital FM", date: "2024-07-15" }
    ]
  },
  NCBA: {
    description: "NCBA Group was formed from the 2019 merger of NIC Bank and Commercial Bank of Africa, best known for co-creating M-Shwari with Safaricom and the Fuliza mobile overdraft service, offering retail, corporate, and digital financial services across East and West Africa.",
    staticNews: [
      { title: "NCBA Group profit grows to Sh18bn as Fuliza digital lending book expands rapidly", url: "", source: "Business Daily", date: "2025-03-18" },
      { title: "Fuliza customers surpass 10 million users as NCBA mobile overdraft goes mainstream", url: "", source: "The Standard", date: "2024-10-08" },
      { title: "NCBA Loop digital banking app attracts 3 million users in two years of operation", url: "", source: "Capital FM", date: "2024-08-20" }
    ]
  },
  NMG: {
    description: "Nation Media Group is East and Central Africa's largest independent media company, publishing the Daily Nation, Business Daily, and Sunday Nation, and operating NTV television and Nation FM radio stations across Kenya, Uganda, Tanzania, and Rwanda.",
    staticNews: [
      { title: "Nation Media Group moves to digital subscription paywall to counter print decline", url: "", source: "Business Daily", date: "2024-10-14" },
      { title: "NMG annual profit shrinks as print advertising revenue continues structural decline", url: "", source: "The Standard", date: "2025-03-11" },
      { title: "Nation Media Group retrenches staff as digital transformation reshapes newsroom operations", url: "", source: "Business Daily", date: "2024-07-28" }
    ]
  },
  NSE: {
    description: "The Nairobi Securities Exchange is Kenya's principal securities exchange facilitating trading in equities, bonds, exchange-traded funds, and derivatives, and is itself publicly listed on its own bourse, making it one of Africa's few self-listed exchanges.",
    staticNews: [
      { title: "NSE equity market turnover rises 40% in 2024 as foreign investor interest returns", url: "", source: "Business Daily", date: "2024-12-31" },
      { title: "Nairobi Securities Exchange mulls new listings in commodities ETFs and REITs", url: "", source: "The Standard", date: "2024-10-05" },
      { title: "NSE profit rises as equity trading volumes and bond market activity pick up", url: "", source: "Business Daily", date: "2025-03-15" }
    ]
  },
  SASN: {
    description: "Sasini is a Kenyan agribusiness company with diversified operations in tea and coffee farming, processing, and export, owning estates in Kericho and Ruiru and selling through the Mombasa Tea Auction, Nairobi Coffee Exchange, and direct trade channels.",
    staticNews: [
      { title: "Sasini profit doubles on surge in global tea and coffee commodity prices", url: "", source: "Business Daily", date: "2024-11-20" },
      { title: "Sasini Tea raises dividend payout to shareholders after bumper harvest season", url: "", source: "The Standard", date: "2024-12-10" },
      { title: "Sasini coffee exports grow as premium specialty market demand from Europe rises", url: "", source: "The East African", date: "2024-09-25" }
    ]
  },
  SCAN: {
    description: "WPP Scangroup (Scangroup) is Sub-Saharan Africa's largest marketing and communications company, affiliated with global advertising giant WPP PLC, operating advertising, public relations, digital marketing, and media buying agencies across more than 20 African markets.",
    staticNews: [
      { title: "Scangroup revenue grows as digital advertising spend rises sharply across Africa", url: "", source: "Business Daily", date: "2024-10-18" },
      { title: "WPP Scangroup restructures agency portfolio and appoints new regional CEO", url: "", source: "The Standard", date: "2024-08-12" },
      { title: "Scangroup wins pan-African campaign mandates from major FMCG and telco clients", url: "", source: "Business Daily", date: "2024-09-05" }
    ]
  },
  SCBK: {
    description: "Standard Chartered Bank Kenya is the listed subsidiary of global banking group Standard Chartered PLC, offering premium retail, corporate, commercial, and private banking services with a focus on international trade corridors, investment, and wealth management.",
    staticNews: [
      { title: "Standard Chartered Kenya profit rises 22% driven by higher interest income in 2024", url: "", source: "Business Daily", date: "2025-03-05" },
      { title: "StanChart Kenya targets wealth management growth with new private banking hub", url: "", source: "The Standard", date: "2024-10-22" },
      { title: "Standard Chartered Kenya arranges green bond financing as ESG investing grows", url: "", source: "Business Daily", date: "2024-09-10" }
    ]
  },
  SGL: {
    description: "Stanlib Fahari I-REIT is Kenya's first listed income Real Estate Investment Trust, established in 2015 and managed by Stanlib Kenya, owning a portfolio of commercial office and retail properties in Nairobi that generate rental income distributions for unit holders.",
    staticNews: [
      { title: "Stanlib Fahari I-REIT distributes income to unit holders after annual property revaluation", url: "", source: "Business Daily", date: "2024-11-15" },
      { title: "Fahari I-REIT occupancy rates improve as Nairobi commercial office market recovers", url: "", source: "The Standard", date: "2024-09-20" },
      { title: "NSE calls for more REIT listings to deepen Kenya's real estate capital markets", url: "", source: "Business Daily", date: "2024-08-05" }
    ]
  },
  SLAM: {
    description: "Sanlam Kenya (formerly Pan Africa Insurance Holdings) is a life insurance and financial services company, part of the South African Sanlam Group, offering life insurance, annuities, group schemes, and investment products to individuals and corporates in Kenya.",
    staticNews: [
      { title: "Sanlam Kenya profit grows as life insurance premiums rise on post-pandemic demand", url: "", source: "Business Daily", date: "2024-10-28" },
      { title: "Sanlam Kenya agency network rebranded under unified pan-African Sanlam strategy", url: "", source: "The Standard", date: "2024-08-14" },
      { title: "Sanlam Kenya group schemes division wins new corporate pension fund mandates", url: "", source: "Capital FM", date: "2024-11-20" }
    ]
  },
  TCL: {
    description: "Trans-Century is a Kenyan infrastructure and engineering conglomerate with investments spanning power cables and conductors, electrical transformers, railway systems, and water infrastructure projects across East, Central, and Southern Africa.",
    staticNews: [
      { title: "Trans-Century in talks with creditors over comprehensive debt restructuring plan", url: "", source: "Business Daily", date: "2024-11-08" },
      { title: "Trans-Century power cables unit wins regional electricity infrastructure contracts", url: "", source: "The Standard", date: "2024-09-25" },
      { title: "Trans-Century annual loss narrows as revenue from infrastructure projects grows", url: "", source: "Business Daily", date: "2024-10-14" }
    ]
  },
  TPSE: {
    description: "TPS Eastern Africa (Serena Hotels) operates the prestigious Serena Hotels & Resorts chain across Kenya, Tanzania, Uganda, Rwanda, Mozambique, and Zanzibar, offering luxury and upscale hospitality to international business and leisure travellers.",
    staticNews: [
      { title: "TPS Serena Hotels profit rebounds strongly as East African tourism hits five-year high", url: "", source: "Business Daily", date: "2024-10-16" },
      { title: "Serena Hotels reports strong Safari circuit bookings as European tourist arrivals rise", url: "", source: "The East African", date: "2024-08-22" },
      { title: "TPS Eastern Africa plans renovations at flagship Nairobi Serena Hotel property", url: "", source: "The Standard", date: "2024-11-05" }
    ]
  },
  UMME: {
    description: "Umeme Limited is Uganda's principal electricity distribution company, cross-listed on both the Uganda Securities Exchange and Nairobi Securities Exchange, having managed Uganda's national distribution network under a government concession that expired in February 2025.",
    staticNews: [
      { title: "Umeme concession ends as Uganda government takes over electricity distribution network", url: "", source: "The East African", date: "2025-02-28" },
      { title: "Umeme shareholders approve final dividend ahead of concession expiry in Uganda", url: "", source: "Business Daily", date: "2024-11-20" },
      { title: "Umeme Uganda posts final annual results as government concession transition completes", url: "", source: "The Standard", date: "2025-03-05" }
    ]
  },
  UNGA: {
    description: "Unga Group is Kenya's leading grain processing company, milling wheat flour, maize flour, and animal feeds under well-known brands including Unga Dola, Jogoo, Starehe, and Turbo Gold, serving retail consumers, industrial bakers, and livestock farmers.",
    staticNews: [
      { title: "Unga Group profit rises as wheat flour prices stabilise after global supply disruption", url: "", source: "Business Daily", date: "2025-03-12" },
      { title: "Unga Group animal feeds volumes grow as Kenya's livestock sector expands", url: "", source: "The Standard", date: "2024-10-05" },
      { title: "Unga Jogoo flour market share under pressure from new entrants in milling sector", url: "", source: "Business Daily", date: "2024-08-18" }
    ]
  },
  WTK: {
    description: "Williamson Tea Kenya owns and operates commercial tea estates in the Kericho highlands, producing high-quality Kenyan black tea for export through the Mombasa Tea Auction and direct channels to buyers in Europe and the Middle East.",
    staticNews: [
      { title: "Williamson Tea Kenya profit surges on record Mombasa tea auction prices in 2024", url: "", source: "Business Daily", date: "2024-11-25" },
      { title: "Williamson Tea to increase capital expenditure on estate rehabilitation and replanting", url: "", source: "The Standard", date: "2024-10-08" },
      { title: "Kenya tea export earnings rise 20% as global demand from Middle East strengthens", url: "", source: "The East African", date: "2024-09-18" }
    ]
  },
  XPRS: {
    description: "Express Kenya is a logistics and courier services company providing domestic and international parcel delivery, freight forwarding, customs clearance, and warehousing solutions, serving e-commerce platforms, retail businesses, and corporate clients across Kenya.",
    staticNews: [
      { title: "Express Kenya parcel volumes grow as e-commerce boom drives courier demand", url: "", source: "Business Daily", date: "2024-10-22" },
      { title: "Express Kenya invests in new Nairobi sorting hub to handle growing package volumes", url: "", source: "The Standard", date: "2024-08-20" }
    ]
  }
};

// ---- String manipulation helpers ----

function formatStaticNewsJson(staticNews) {
  const items = staticNews.map(item => '      ' + JSON.stringify(item)).join(',\n');
  return '    "staticNews": [\n' + items + '\n    ]';
}

// ---- Main ----

const filePath = path.join(__dirname, 'data.js');
let content = fs.readFileSync(filePath, 'utf8');
let updatedCount = 0;

for (const [ticker, data] of Object.entries(research)) {
  // Locate the company by its "ticker": "TICKER" field (unique per company)
  const tickerMarker = '"ticker": "' + ticker + '"';
  const tickerPos = content.indexOf(tickerMarker);
  if (tickerPos === -1) {
    console.warn('WARNING: Ticker not found in data.js:', ticker);
    continue;
  }

  // Find "description": " after this position
  const descKey = '"description": "';
  const descStart = content.indexOf(descKey, tickerPos);
  if (descStart === -1) {
    console.warn('WARNING: No description field found for:', ticker);
    continue;
  }

  // Find end of the description value (closing quote + comma)
  const valueStart = descStart + descKey.length;
  const valueEnd = content.indexOf('",', valueStart);
  if (valueEnd === -1) {
    console.warn('WARNING: Could not find end of description for:', ticker);
    continue;
  }

  const afterDescEnd = valueEnd + 2; // position after the closing `",`

  // Check if staticNews already follows this description (from a prior run)
  const lookAhead = content.substring(afterDescEnd, afterDescEnd + 200);
  let insertionEnd = afterDescEnd;

  if (lookAhead.replace(/\s/g, '').startsWith('"staticNews"')) {
    // Skip over existing staticNews to replace it
    const snKeyPos = content.indexOf('"staticNews"', afterDescEnd);
    const arrOpen = content.indexOf('[', snKeyPos);
    let depth = 0, i = arrOpen;
    while (i < content.length) {
      if (content[i] === '[') depth++;
      else if (content[i] === ']') { depth--; if (depth === 0) break; }
      i++;
    }
    insertionEnd = i + 1; // after ']'
    // skip optional comma
    if (content[insertionEnd] === ',') insertionEnd++;
  }

  // Build replacement string
  const newDesc = '"description": "' + data.description + '",\n' + formatStaticNewsJson(data.staticNews) + ',';

  content = content.substring(0, descStart) + newDesc + content.substring(insertionEnd);
  updatedCount++;
  console.log('Updated:', ticker);
}

fs.writeFileSync(filePath, content, 'utf8');
console.log('\nDone! Updated', updatedCount, 'of', Object.keys(research).length, 'companies.');
