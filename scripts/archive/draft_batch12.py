#!/usr/bin/env python3
"""Draft and QA-check batch 12 research + copy, then write JSON files."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANNED = [
    "hope this email finds you well",
    "impressive linkedin",
    "pick your brain",
    "circle back",
    "touch base",
    "deep dive",
    "—",
]

RESEARCH = [
    {
        "csv_index": 227,
        "first_name": "Michael",
        "last_name": "Cossitt",
        "title": "Director of Marketing And Business Development",
        "company": "Phenix Title Services",
        "email": "mcossitt@phenixtitle.com",
        "website": "https://phenixtitle.com",
        "linkedin": "http://www.linkedin.com/in/michael-cossitt-94a275234",
        "twitter": "",
        "facebook": "https://facebook.com/pages/Phenix-Title-Services-LLC/109172535779156",
        "research_signal": "Director of marketing at Phenix Title Services; phenixtitle.com lists 12 closing offices and 18 agents across Maine, New Hampshire, and Massachusetts with commercial and new construction expertise.",
        "research_notes": "Six Phenix contacts batch 12. Michael owns partner-facing brand media. Pat CEO, Brenda VP, Debra CFO, Nancy post closer same firm.",
    },
    {
        "csv_index": 228,
        "first_name": "Robin",
        "last_name": "Townsend",
        "title": "Escrow Assistant",
        "company": "CentraLand Title Company",
        "email": "rtownsend@centralandtitle.com",
        "website": "https://centralandtitle.com",
        "linkedin": "http://www.linkedin.com/in/robin-townsend-91454642",
        "twitter": "",
        "facebook": "https://www.facebook.com/CentraLand/",
        "research_signal": "Escrow assistant at CentraLand Title Temple TX; centralandtitle.com leads with surprise-free closings and a 2026 agent resource slide on the homepage carousel.",
        "research_notes": "Summer Allen order entry batch 11 same firm. Robin is escrow-assistant file-prep angle.",
    },
    {
        "csv_index": 229,
        "first_name": "Pat",
        "last_name": "Enright",
        "title": "CEO",
        "company": "Phenix Title Services",
        "email": "penright@phenixtitle.com",
        "website": "https://phenixtitle.com",
        "linkedin": "http://www.linkedin.com/in/patrick-enright-a5b31696",
        "twitter": "",
        "facebook": "https://facebook.com/pages/Phenix-Title-Services-LLC/109172535779156",
        "research_signal": "CEO at locally owned Phenix Title Services with state-of-the-art technology messaging and three-state New England coverage on phenixtitle.com.",
        "research_notes": "CEO sets standard for 48-person firm. Differentiate from Michael marketing and Brenda VP ops.",
    },
    {
        "csv_index": 230,
        "first_name": "Randy",
        "last_name": "Schell",
        "title": "Director of Development",
        "company": "Golden Eagle Group",
        "email": "rschell@goldeneaglegroup.net",
        "website": "https://goldeneaglegroup.net",
        "linkedin": "http://www.linkedin.com/in/randy-schell-8234a691",
        "twitter": "",
        "facebook": "",
        "research_signal": "Director of development at Golden Eagle Group; goldeneaglegroup.net highlights DC-metro community development and projects like Georgetown Colonial and Waterway in The Woodlands.",
        "research_notes": "Investment firm not title. Five contacts batch 12. Randy leads development storytelling for investors.",
    },
    {
        "csv_index": 231,
        "first_name": "Sherrian",
        "last_name": "Erwin",
        "title": "Accounting Technician",
        "company": "Texas Premier Title",
        "email": "serwin@txprem.com",
        "website": "https://txprem.com",
        "linkedin": "http://www.linkedin.com/in/sherrian-erwin-7815aa63",
        "twitter": "",
        "facebook": "https://web.facebook.com/texaspremiertitle/",
        "research_signal": "Accounting technician at Texas Premier Title Plano; CSV cites secure transactions and digital calculators, Facebook texaspremiertitle active while txprem.com DNS still propagating.",
        "research_notes": "Seven txprem contacts batch 12. Samantha McCoy escrow batch 11. Sherrian is back-office accuracy angle.",
    },
    {
        "csv_index": 232,
        "first_name": "Nancy",
        "last_name": "Bonafine",
        "title": "Post Closer",
        "company": "Phenix Title Services",
        "email": "nbonafine@phenixtitle.com",
        "website": "https://phenixtitle.com",
        "linkedin": "http://www.linkedin.com/in/nancy-bonafine-349a34a9",
        "twitter": "",
        "facebook": "https://facebook.com/pages/Phenix-Title-Services-LLC/109172535779156",
        "research_signal": "Post closer at Phenix Title Services Standish ME; firm site emphasizes reverse mortgage and cash closing specialists across northern New England.",
        "research_notes": "Post-close payoff explainers. Maine desk distinct from NH leadership.",
    },
    {
        "csv_index": 233,
        "first_name": "Stephen",
        "last_name": "Speer",
        "title": "Owner",
        "company": "Golden Eagle Group",
        "email": "sspeer@testladders.com",
        "website": "https://goldeneaglegroup.net",
        "linkedin": "http://www.linkedin.com/in/stephen-speer-40457b44",
        "twitter": "",
        "facebook": "",
        "research_signal": "Owner at Golden Eagle Group since 1991; site cites $1.2B+ in acquisitions and 3,500+ residential units sold across commercial and residential portfolios.",
        "research_notes": "Personal email testladders.com in CSV. Owner investor narrative, not title ops.",
    },
    {
        "csv_index": 234,
        "first_name": "Samantha",
        "last_name": "Morehead",
        "title": "VP of Title Operations",
        "company": "Texas Premier Title",
        "email": "smorehead@txprem.com",
        "website": "https://txprem.com",
        "linkedin": "http://www.linkedin.com/in/samantha-morehead-66465a2ab",
        "twitter": "",
        "facebook": "https://web.facebook.com/texaspremiertitle/",
        "research_signal": "VP of title operations at Texas Premier Title Plano; CSV keywords include contract reviews, transaction management, and certified title services.",
        "research_notes": "Ops leader for desk consistency. Differentiate from Samantha McCoy escrow officer batch 11.",
    },
    {
        "csv_index": 235,
        "first_name": "Rabiya",
        "last_name": "Ahmad",
        "title": "Accountant",
        "company": "Golden Eagle Group",
        "email": "rabiya@goldeneaglegroup.net",
        "website": "https://goldeneaglegroup.net",
        "linkedin": "http://www.linkedin.com/in/rabiya-faridi-ahmad-7b63754a",
        "twitter": "",
        "facebook": "",
        "research_signal": "Accountant at Golden Eagle Group Baltimore; firm site stresses structured investment portfolios and property management across 2.2 million sq ft managed.",
        "research_notes": "Finance role. Investor reporting clarity, not agent marketing.",
    },
    {
        "csv_index": 236,
        "first_name": "Ashley",
        "last_name": "Campbell",
        "title": "Executive Assistant/Office Manager",
        "company": "Golden Eagle Group",
        "email": "ashley@goldeneaglegroup.net",
        "website": "https://goldeneaglegroup.net",
        "linkedin": "http://www.linkedin.com/in/ashley-campbell-495020151",
        "twitter": "",
        "facebook": "",
        "research_signal": "Executive assistant and office manager at Golden Eagle Group; firm highlights acquisition strategy and nationally recognized property management partners on goldeneaglegroup.net.",
        "research_notes": "Gatekeeper for leadership media. Coordinate with Stephen owner angle.",
    },
    {
        "csv_index": 237,
        "first_name": "Debra",
        "last_name": "Pratt",
        "title": "CFO",
        "company": "Phenix Title Services",
        "email": "dpratt@phenixtitle.com",
        "website": "https://phenixtitle.com",
        "linkedin": "http://www.linkedin.com/in/debra-pratt-8b78b995",
        "twitter": "",
        "facebook": "https://facebook.com/pages/Phenix-Title-Services-LLC/109172535779156",
        "research_signal": "CFO at Phenix Title Services Farmington NH; firm revenue scale per CSV with online title ordering and multi-state closing footprint.",
        "research_notes": "CFO cares about vendor ROI and brand consistency per office. Differentiate from Pat CEO.",
    },
    {
        "csv_index": 238,
        "first_name": "Macie",
        "last_name": "Sandlin",
        "title": "Corporate Marketing Associate",
        "company": "Texas Premier Title",
        "email": "msandlin@txprem.com",
        "website": "https://txprem.com",
        "linkedin": "http://www.linkedin.com/in/macie-sandlin-277700233",
        "twitter": "",
        "facebook": "https://web.facebook.com/texaspremiertitle/",
        "research_signal": "Corporate marketing associate at Texas Premier Title; CSV lists community resources, informational flyers, and client communication keywords with active Facebook presence.",
        "research_notes": "Primary marketing contact at txprem. Pair with ops VP Samantha Morehead.",
    },
    {
        "csv_index": 239,
        "first_name": "Kellese",
        "last_name": "Key",
        "title": "Escrow Assistant",
        "company": "Texas Premier Title",
        "email": "kkey@txprem.com",
        "website": "https://txprem.com",
        "linkedin": "http://www.linkedin.com/in/kellese-key-56b20325",
        "twitter": "",
        "facebook": "https://web.facebook.com/texaspremiertitle/",
        "research_signal": "Escrow assistant at Texas Premier Title Frisco; CSV cites escrow services and educational resources for agents and lenders.",
        "research_notes": "Frisco desk. Differentiate from Alyssa and Meagan escrow officers.",
    },
    {
        "csv_index": 240,
        "first_name": "Cory",
        "last_name": "Dasilva",
        "title": "Real Estate Salesperson",
        "company": "revolv real estate",
        "email": "cory@revolvre.com",
        "website": "https://revolvrealestate.com",
        "linkedin": "http://www.linkedin.com/in/cory-dasilva-0b67a0152",
        "twitter": "",
        "facebook": "",
        "research_signal": "Salesperson at revolv real estate Somerset MA; CSV keywords include short sales, bank-owned listings, and professional-services crossover at 865 County St.",
        "research_notes": "revolvrealestate.com timed out May 2026. Use CSV and LinkedIn. Christina Maciel marketing same firm later in list.",
    },
    {
        "csv_index": 241,
        "first_name": "Corres",
        "last_name": "Marisa",
        "title": "Branch Manager",
        "company": "Texas Premier Title",
        "email": "mcorres@txprem.com",
        "website": "https://txprem.com",
        "linkedin": "http://www.linkedin.com/in/corres-marisa-51814b47",
        "twitter": "",
        "facebook": "https://web.facebook.com/texaspremiertitle/",
        "research_signal": "Branch manager at Texas Premier Title Plano; CSV cites local area market knowledge and dedicated team positioning for Texas closings.",
        "research_notes": "Branch manager sets desk training standard. Name order per CSV.",
    },
    {
        "csv_index": 242,
        "first_name": "Brenda",
        "last_name": "Butkus",
        "title": "Vice President",
        "company": "Phenix Title Services",
        "email": "bbutkus@phenixtitle.com",
        "website": "https://phenixtitle.com",
        "linkedin": "http://www.linkedin.com/in/brenda-butkus-274168125",
        "twitter": "",
        "facebook": "https://facebook.com/pages/Phenix-Title-Services-LLC/109172535779156",
        "research_signal": "Vice president at Phenix Title Services Manchester NH; firm promotes seasoned attorneys for commercial transactions and builder-focused new construction closings.",
        "research_notes": "VP ops angle. Pat CEO and Michael marketing same batch.",
    },
    {
        "csv_index": 243,
        "first_name": "Michael",
        "last_name": "Nathan",
        "title": "Asset Manager at Golden Eagle Group, Inc.",
        "company": "Golden Eagle Group",
        "email": "mnathan@goldeneaglegroup.net",
        "website": "https://goldeneaglegroup.net",
        "linkedin": "http://www.linkedin.com/in/michael-nathan-8066616",
        "twitter": "",
        "facebook": "",
        "research_signal": "Asset manager at Golden Eagle Group; site portfolio includes 1910 John Street Columbus and 5,250 acres in land acquisitions with below-market acquisition strategy.",
        "research_notes": "Asset manager needs property and investor update reels. Not title escrow.",
    },
    {
        "csv_index": 244,
        "first_name": "Alyssa",
        "last_name": "Kinsey",
        "title": "Escrow Officer",
        "company": "Texas Premier Title",
        "email": "aclowdus@txprem.com",
        "website": "https://txprem.com",
        "linkedin": "http://www.linkedin.com/in/alyssa-kinsey",
        "twitter": "",
        "facebook": "https://web.facebook.com/texaspremiertitle/",
        "research_signal": "Escrow officer at Texas Premier Title; email domain txprem with wire-safety and closing-process keywords in firm CSV data.",
        "research_notes": "LinkedIn slug alyssa-kinsey; email aclowdus@txprem.com. Differentiate from Meagan Crow escrow officer.",
    },
    {
        "csv_index": 245,
        "first_name": "Christy",
        "last_name": "Stokes",
        "title": "Sales and Marketing Executive",
        "company": "Lawyers Title",
        "email": "christy.stokes@ltic.com",
        "website": "https://ltic.com",
        "linkedin": "http://www.linkedin.com/in/christy-stokes-1997386",
        "twitter": "",
        "facebook": "https://facebook.com/Lawyers-Title-111713535507208/",
        "research_signal": "Sales and marketing executive at Lawyers Title Phoenix on national ltic.com; CSV places her in Arizona with title insurance and escrow platform keywords.",
        "research_notes": "Stacey Dennison AVP escrow and Tina Rynhard branch manager batch 11 same Phoenix market. Christy is sales-led growth angle.",
    },
    {
        "csv_index": 246,
        "first_name": "Meagan",
        "last_name": "Crow",
        "title": "Escrow Officer",
        "company": "Texas Premier Title",
        "email": "mcrow@txprem.com",
        "website": "https://txprem.com",
        "linkedin": "http://www.linkedin.com/in/meagan-crow-470b32132",
        "twitter": "",
        "facebook": "https://web.facebook.com/texaspremiertitle/",
        "research_signal": "Escrow officer at Texas Premier Title Grand Prairie; CSV cites secure transactions and Dallas-area title exchange positioning.",
        "research_notes": "Grand Prairie desk. Samantha McCoy batch 11 was first txprem contact.",
    },
]

COPY = {
    "mcossitt@phenixtitle.com": [
        [
            "Marketing Phenix NE",
            "Hi Michael,\n\nYou director of marketing at Phenix with twelve offices and eighteen agents across Maine, New Hampshire, and Massachusetts on phenixtitle.com.\n\nMarketing directors win when builder and lender partner clips look identical market to market.\n\nWe finish supplied event and training footage.\n\nWorth a sample?",
        ],
        [
            "New construction closings",
            "Hi Michael,\n\nPhenix highlights new construction and commercial work with attorneys on staff; that story should show in every partner reel.\n\nWe batch hook variants from one master interview you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Pat CEO separate",
            "Hi Michael,\n\nPat may get CEO notes this batch; yours is Michael-led brand and partner media.\n\nOpen to a three-state enablement outline?",
        ],
    ],
    "rtownsend@centralandtitle.com": [
        [
            "Escrow assistant CentraLand",
            "Hi Robin,\n\nYou escrow assistant at CentraLand Title where centralandtitle.com promises surprise-free closings and fresh 2026 agent resources on the homepage.\n\nAssistants cut repeat calls when wire and timeline clips match what order entry promises.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Temple Central Texas",
            "Hi Robin,\n\nThirty years in Central Texas means agents expect the same calm tone from your desk as from leadership.\n\nWe engineer shorts from narration you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Summer order entry",
            "Hi Robin,\n\nSummer may have seen order-entry notes in batch 11; yours is Robin-led escrow file prep.\n\nWant an assistant training kit outline?",
        ],
    ],
    "penright@phenixtitle.com": [
        [
            "CEO Phenix locally owned",
            "Hi Pat,\n\nYou CEO at locally owned Phenix Title with three-state coverage and state-of-the-art technology on phenixtitle.com.\n\nCEOs set whether eighteen closing agents send the same partner clip quality.\n\nWe finish supplied leadership and event footage.\n\nWorth a sample?",
        ],
        [
            "Online title order",
            "Hi Pat,\n\nYour site pushes online title orders; digital intake should pair with video that looks as polished as the form experience.\n\nWe engineer retention pacing on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Michael marketing separate",
            "Hi Pat,\n\nMichael may get marketing director notes; yours is Pat-led firm standard.\n\nOpen to an owner reel plan?",
        ],
    ],
    "rschell@goldeneaglegroup.net": [
        [
            "Development Golden Eagle",
            "Hi Randy,\n\nYou director of development at Golden Eagle Group where goldeneaglegroup.net showcases Georgetown Colonial and Waterway in The Woodlands.\n\nDevelopment leads need investor reels that match the prestige of the communities you build.\n\nWe finish supplied drone and site footage.\n\nWorth a sample?",
        ],
        [
            "DC metro communities",
            "Hi Randy,\n\nCommunity development in the DC metro should look cinematic in every partner update, not slideshow stills.\n\nWe grade and pace footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Stephen owner separate",
            "Hi Randy,\n\nStephen may get owner notes; yours is Randy-led project storytelling.\n\nWant a development portfolio reel spec?",
        ],
    ],
    "serwin@txprem.com": [
        [
            "Accounting txprem Plano",
            "Hi Sherrian,\n\nYou accounting technician at Texas Premier Title Plano while txprem.com DNS catches up; CSV still cites secure transactions and active texaspremiertitle Facebook.\n\nAccounting teams reduce disputes when funding and ledger explainers look identical branch to branch.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Digital calculators CSV",
            "Hi Sherrian,\n\nYour firm keywords mention digital calculators and client communication; short clips should match that clarity on mobile.\n\nPost-production on footage you supply.\n\nUseful?",
        ],
        [
            "Samantha McCoy escrow",
            "Hi Sherrian,\n\nSamantha McCoy may have seen escrow notes in batch 11; yours is Sherrian-led back-office accuracy.\n\nWant a funding FAQ video outline?",
        ],
    ],
    "nbonafine@phenixtitle.com": [
        [
            "Post closer Phenix ME",
            "Hi Nancy,\n\nYou post closer at Phenix in Standish where phenixtitle.com emphasizes reverse mortgage and cash closing specialists across northern New England.\n\nPost-close teams cut repeat calls when payoff explainers look clear on mobile.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Reverse mortgage niche",
            "Hi Nancy,\n\nReverse and cash niches need explainers agents actually forward, not dense PDFs alone.\n\nWe engineer shorts from narration you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Michael marketing separate",
            "Hi Nancy,\n\nMichael may get marketing notes; yours is Nancy-led post-close follow-through.\n\nWant a post-close kit outline?",
        ],
    ],
    "sspeer@testladders.com": [
        [
            "Owner Golden Eagle",
            "Hi Stephen,\n\nYou owner at Golden Eagle Group since 1991 with $1.2B+ in acquisitions and 3,500+ residential units on goldeneaglegroup.net.\n\nOwners set whether investor updates look as premium as the assets you acquire.\n\nWe finish supplied portfolio and site footage.\n\nWorth a sample?",
        ],
        [
            "Investment partners",
            "Hi Stephen,\n\nAcquisition and property management storylines should hold attention in under ninety seconds for busy partners.\n\nWe engineer retention pacing on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Randy development separate",
            "Hi Stephen,\n\nRandy may get development director notes; yours is Stephen-led investor narrative.\n\nOpen to an owner update reel plan?",
        ],
    ],
    "smorehead@txprem.com": [
        [
            "VP title ops txprem",
            "Hi Samantha,\n\nYou VP of title operations at Texas Premier Title Plano with contract reviews and transaction management in the firm keywords.\n\nOps VPs scale when every desk sends the same wire-safety and timeline clip quality.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Certified title services",
            "Hi Samantha,\n\nCertified title positioning only works if branch training video matches Grand Prairie and Frisco desks.\n\nWe standardize on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "McCoy escrow separate",
            "Hi Samantha,\n\nSamantha McCoy may have seen escrow-officer notes in batch 11; yours is Morehead-led ops consistency.\n\nWant a desk enablement outline?",
        ],
    ],
    "rabiya@goldeneaglegroup.net": [
        [
            "Accountant Golden Eagle",
            "Hi Rabiya,\n\nYou accountant at Golden Eagle Group Baltimore where the site cites 2.2 million sq ft managed and structured investment portfolios.\n\nFinance partners trust firms whose quarterly updates look as disciplined as the spreadsheets.\n\nWe finish supplied reporting walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Property management scale",
            "Hi Rabiya,\n\nNationally recognized property managers still need crisp investor explainers when numbers change.\n\nWe polish supplied screen recordings with motion and captions.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Ashley EA separate",
            "Hi Rabiya,\n\nAshley may get office manager notes; yours is Rabiya-led reporting clarity.\n\nWant a quarterly update video spec?",
        ],
    ],
    "ashley@goldeneaglegroup.net": [
        [
            "EA Golden Eagle",
            "Hi Ashley,\n\nYou executive assistant and office manager at Golden Eagle Group with acquisition strategy and management partners highlighted on goldeneaglegroup.net.\n\nEAs keep leadership media consistent when investor calls stack up.\n\nWe finish supplied event and site footage.\n\nWorth a sample?",
        ],
        [
            "Leadership scheduling",
            "Hi Ashley,\n\nOne polished reel template saves hours when Randy, Stephen, or Michael need assets the same week.\n\nWe batch cuts from footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Stephen owner separate",
            "Hi Ashley,\n\nStephen may get owner notes; yours is Ashley-led coordination and delivery.\n\nOpen to a leadership media kit outline?",
        ],
    ],
    "dpratt@phenixtitle.com": [
        [
            "CFO Phenix Title",
            "Hi Debra,\n\nYou CFO at Phenix Title Services with multi-state offices and online title ordering on phenixtitle.com.\n\nCFOs care when partner media ROI is predictable and every market uses the same finishing standard.\n\nWe finish supplied training footage with clear scope.\n\nWorth a sample?",
        ],
        [
            "Vendor consistency",
            "Hi Debra,\n\nTwelve offices should not mean twelve different video styles for lenders and builders.\n\nWe engineer one template from footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Pat CEO separate",
            "Hi Debra,\n\nPat may get CEO notes; yours is Debra-led spend and quality control.\n\nWant a CFO vendor brief outline?",
        ],
    ],
    "msandlin@txprem.com": [
        [
            "Marketing txprem",
            "Hi Macie,\n\nYou corporate marketing associate at Texas Premier Title with community resources and informational flyers in the CSV keywords and active texaspremiertitle Facebook.\n\nMarketing owns whether agents see polished fraud and timeline clips or ad hoc desk recordings.\n\nWe finish supplied partner and social footage.\n\nWorth a sample?",
        ],
        [
            "Flyers to video",
            "Hi Macie,\n\nFlyers agents ignore should become forty-five second hooks from one master walkthrough you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Samantha VP ops",
            "Hi Macie,\n\nSamantha Morehead may get ops notes; yours is Macie-led brand and agent media.\n\nOpen to a Texas partner reel plan?",
        ],
    ],
    "kkey@txprem.com": [
        [
            "Escrow assistant Frisco",
            "Hi Kellese,\n\nYou escrow assistant at Texas Premier Title Frisco with educational resources for agents in the firm keywords.\n\nAssistants win when wire and document clips match what branch managers promise lenders.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Agent education shorts",
            "Hi Kellese,\n\nShort explainers cut repeat status calls when pacing is built for mobile.\n\nWe engineer from footage you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Corres branch manager",
            "Hi Kellese,\n\nCorres Marisa may get branch manager notes; yours is Kellese-led file prep clarity.\n\nWant an assistant checklist video outline?",
        ],
    ],
    "cory@revolvre.com": [
        [
            "Agent revolv Somerset",
            "Hi Cory,\n\nYou salesperson at revolv real estate Somerset with short sales and bank-owned listings in the firm keywords at 865 County St.\n\nAgents win when distressed and REO tours look cinematic, not phone footage left unedited.\n\nWe polish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Short sale listings",
            "Hi Cory,\n\nShort sale and bank-owned buyers decide fast; hooks should surface condition and timeline in the first three seconds.\n\nWe batch variants from one shoot day you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Christina marketing later",
            "Hi Cory,\n\nChristina Maciel may get marketing notes later in the list; yours is Cory-led listing media.\n\nOpen to an agent reel spec?",
        ],
    ],
    "mcorres@txprem.com": [
        [
            "Branch manager Plano",
            "Hi Corres,\n\nYou branch manager at Texas Premier Title Plano with local market and dedicated team positioning in the CSV.\n\nBranch managers scale when every escrow desk uses the same training template.\n\nWe finish supplied partner footage.\n\nWorth a sample?",
        ],
        [
            "Desk consistency",
            "Hi Corres,\n\nPlano, Frisco, and Grand Prairie should sound like one firm on video, not three different styles.\n\nWe standardize on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Meagan escrow separate",
            "Hi Corres,\n\nMeagan Crow may get escrow officer notes; yours is Corres-led branch standards.\n\nWant a branch enablement outline?",
        ],
    ],
    "bbutkus@phenixtitle.com": [
        [
            "VP Phenix commercial",
            "Hi Brenda,\n\nYou vice president at Phenix Manchester where phenixtitle.com promotes seasoned attorneys on commercial and builder new construction closings.\n\nVPs scale when every office sends the same lender and builder clip quality.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Builder new construction",
            "Hi Brenda,\n\nBuilder audiences need distinct forty-five second cuts from one master interview.\n\nWe batch hooks on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Pat CEO separate",
            "Hi Brenda,\n\nPat may get CEO notes; yours is Brenda-led operational excellence.\n\nOpen to a VP enablement reel plan?",
        ],
    ],
    "mnathan@goldeneaglegroup.net": [
        [
            "Asset manager Golden Eagle",
            "Hi Michael,\n\nYou asset manager at Golden Eagle Group with portfolio assets like 1910 John Street Columbus and large land acquisitions on goldeneaglegroup.net.\n\nAsset managers need property updates investors actually watch.\n\nWe finish supplied drone and interior footage.\n\nWorth a sample?",
        ],
        [
            "Below market acquisitions",
            "Hi Michael,\n\nAcquisition storylines should show location upside in the first frame, not buried in a PDF deck.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Randy development separate",
            "Hi Michael,\n\nRandy Schell may get development notes; yours is Michael-led asset updates.\n\nWant an investor property reel outline?",
        ],
    ],
    "aclowdus@txprem.com": [
        [
            "Escrow officer txprem",
            "Hi Alyssa,\n\nYou escrow officer at Texas Premier Title with secure transaction keywords in the firm CSV while txprem.com is still propagating.\n\nEscrow officers need wire-safety clips agents actually forward.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Fraud education angle",
            "Hi Alyssa,\n\nOne master recording should become distinct lender and agent cuts with captions for mobile.\n\nPost-production on footage you supply.\n\nUseful?",
        ],
        [
            "Meagan Crow separate",
            "Hi Alyssa,\n\nMeagan Crow may get parallel escrow notes; yours is Alyssa-led desk outreach.\n\nOpen to a wire-safety reel spec?",
        ],
    ],
    "christy.stokes@ltic.com": [
        [
            "Sales marketing Phoenix",
            "Hi Christy,\n\nYou sales and marketing executive at Lawyers Title Phoenix on national ltic.com in Arizona.\n\nSales leaders scale when every AE and escrow desk sends partner clips that match the parent brand.\n\nWe finish supplied event and training footage.\n\nWorth a sample?",
        ],
        [
            "Phoenix ltic growth",
            "Hi Christy,\n\nPhoenix growth only compounds if local outreach looks as polished as the national platform.\n\nWe batch hook variants from footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Stacey Tina batch 11",
            "Hi Christy,\n\nStacey and Tina may have seen escrow and branch notes in batch 11; yours is Christy-led sales and marketing growth.\n\nWant a Phoenix partner reel outline?",
        ],
    ],
    "mcrow@txprem.com": [
        [
            "Escrow Grand Prairie",
            "Hi Meagan,\n\nYou escrow officer at Texas Premier Title Grand Prairie with secure transactions in the firm keywords.\n\nEscrow officers cut fraud calls when wire-safety clips look consistent with Plano and Frisco desks.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Dallas area closings",
            "Hi Meagan,\n\nDallas-area agents share clips that look phone-recorded unless finishing is production-grade.\n\nWe polish supplied explainers with motion and captions.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Samantha McCoy first",
            "Hi Meagan,\n\nSamantha McCoy opened txprem in batch 11; yours is Meagan-led Grand Prairie desk media.\n\nWant an escrow-led fraud clip outline?",
        ],
    ],
}


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def qa(subject: str, body: str) -> list:
    issues = []
    if word_count(body) > 100:
        issues.append(f"words {word_count(body)}")
    if len(subject) > 60:
        issues.append(f"subject {len(subject)}")
    low = (subject + body).lower()
    for b in BANNED:
        if b in low:
            issues.append(b)
    if "calendly" in low or "book 15" in low:
        issues.append("hard CTA")
    return issues


def main():
    research_out = []
    for item in RESEARCH:
        row = dict(item)
        row["row"] = item["csv_index"] + 1
        research_out.append(row)

    failures = []
    for email, seq in COPY.items():
        for subj, body in seq:
            issues = qa(subj, body)
            if issues:
                failures.append((email, subj, issues))

    if failures:
        for f in failures:
            print("FAIL", f)
        raise SystemExit(1)

    if len(COPY) != 20:
        raise SystemExit(f"copy count {len(COPY)}")
    if len(research_out) != 20:
        raise SystemExit(f"research count {len(research_out)}")

    emails_r = {r["email"].lower() for r in research_out}
    if emails_r != set(COPY.keys()):
        raise SystemExit(f"email mismatch {emails_r ^ set(COPY.keys())}")

    (ROOT / "campaigns" / "pilot-20-batch12-research.json").write_text(
        json.dumps(research_out, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "campaigns" / "pilot-20-batch12-copy.json").write_text(
        json.dumps(COPY, indent=2) + "\n", encoding="utf-8"
    )
    print("OK: 20 leads, 60 emails, QA pre-check passed")


if __name__ == "__main__":
    main()
