#!/usr/bin/env python3
"""Draft and QA-check batch 13 research + copy."""

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
        "csv_index": 247,
        "first_name": "Kelcie",
        "last_name": "Gibbel",
        "title": "Sales Executive",
        "company": "Lawyers Title",
        "email": "kelcie.gibbel@ltic.com",
        "website": "https://ltic.com",
        "linkedin": "http://www.linkedin.com/in/kelcie-gibbel-869359145",
        "twitter": "",
        "facebook": "https://facebook.com/Lawyers-Title-111713535507208/",
        "research_signal": "Sales executive at Lawyers Title Prescott AZ on national ltic.com; CSV places Arizona with title insurance, escrow, and e-closing keywords.",
        "research_notes": "Prescott market, not Phoenix. Christy Stokes sales marketing Phoenix batch 12. Colin Joy San Diego escrow same batch.",
    },
    {
        "csv_index": 248,
        "first_name": "Amy",
        "last_name": "Duncan",
        "title": "Branch Manager Escrow Officer",
        "company": "Texas Premier Title",
        "email": "aduncan@txprem.com",
        "website": "https://txprem.com",
        "linkedin": "http://www.linkedin.com/in/amy-duncan-206408237",
        "twitter": "",
        "facebook": "https://web.facebook.com/texaspremiertitle/",
        "research_signal": "Branch manager and escrow officer at Texas Premier Title Terrell TX; CSV cites dedicated team and local market knowledge with active texaspremiertitle Facebook.",
        "research_notes": "Terrell branch. Seven txprem contacts batch 12. Creighton corp ops same batch.",
    },
    {
        "csv_index": 249,
        "first_name": "Christina",
        "last_name": "Maciel",
        "title": "Lifetime Real Estate Advisor/Marketing Specialist",
        "company": "revolv real estate",
        "email": "cmaciel@revolvre.com",
        "website": "https://revolvrealestate.com",
        "linkedin": "http://www.linkedin.com/in/christina-ann-maciel-b7001b5b",
        "twitter": "",
        "facebook": "",
        "research_signal": "Marketing specialist and lifetime real estate advisor at revolv Somerset MA; firm keywords include short sales, bank-owned listings, and professional-services crossover.",
        "research_notes": "Cory Dasilva salesperson batch 12 same firm. revolvrealestate.com timed out prior batches.",
    },
    {
        "csv_index": 250,
        "first_name": "Kelly",
        "last_name": "Kisiday",
        "title": "Marketing Director & Closing Agent",
        "company": "Phenix Title Services",
        "email": "kkisiday@phenixtitle.com",
        "website": "https://phenixtitle.com",
        "linkedin": "http://www.linkedin.com/in/kellykisiday",
        "twitter": "",
        "facebook": "https://facebook.com/pages/Phenix-Title-Services-LLC/109172535779156",
        "research_signal": "Marketing director and closing agent at Phenix Title Nashua NH; phenixtitle.com lists twelve offices and eighteen agents across Maine, New Hampshire, and Massachusetts.",
        "research_notes": "Dual marketing and closing role. Michael Cossitt marketing director batch 12. Chase Barlow same batch.",
    },
    {
        "csv_index": 251,
        "first_name": "Colin",
        "last_name": "Joy",
        "title": "Junior Escrow Officer",
        "company": "Lawyers Title",
        "email": "colin.joy@ltic.com",
        "website": "https://ltic.com",
        "linkedin": "http://www.linkedin.com/in/colin-joy-4972b7132",
        "twitter": "",
        "facebook": "https://facebook.com/Lawyers-Title-111713535507208/",
        "research_signal": "Junior escrow officer at Lawyers Title San Diego on national ltic.com; Melody Coleman account manager used lticsd.com in batch 7.",
        "research_notes": "San Diego desk. Junior officer training video angle.",
    },
    {
        "csv_index": 252,
        "first_name": "Chase",
        "last_name": "Barlow",
        "title": "Real Estate Agent",
        "company": "Phenix Title Services",
        "email": "cbarlow@phenixtitle.com",
        "website": "https://phenixtitle.com",
        "linkedin": "http://www.linkedin.com/in/chase-barlow-67180b1a3",
        "twitter": "",
        "facebook": "https://facebook.com/pages/Phenix-Title-Services-LLC/109172535779156",
        "research_signal": "Closing agent at Phenix Title Portsmouth NH per phenixtitle.com footprint; CSV title lists agent with firm title-insurance and mortgage-closing keywords.",
        "research_notes": "NH desk agent-facing partner media. Kelly Kisiday marketing same batch.",
    },
    {
        "csv_index": 253,
        "first_name": "Creighton",
        "last_name": "Dippel",
        "title": "Corporate Operations - Escrow Officer",
        "company": "Texas Premier Title",
        "email": "cdippel@txprem.com",
        "website": "https://txprem.com",
        "linkedin": "http://www.linkedin.com/in/creightondippel",
        "twitter": "",
        "facebook": "https://web.facebook.com/texaspremiertitle/",
        "research_signal": "Corporate operations escrow officer at Texas Premier Title Dallas; CSV lists contract reviews and transaction management with txprem.com DNS still propagating May 2026.",
        "research_notes": "Corporate ops vs branch managers. Amy Duncan Terrell same batch.",
    },
    {
        "csv_index": 254,
        "first_name": "Vicki",
        "last_name": "Larmee",
        "title": "Closing Agent",
        "company": "Stephen Cooley Real Estate",
        "email": "vicki@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/vicki-larmee-2772a839",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Closing agent at Stephen Cooley Real Estate Fort Mill SC; stephencooley.com leads with highest-price sales, instant home value, and cash-offer programs across Charlotte to Rock Hill.",
        "research_notes": "Six Cooley contacts batch 13. Vicki closing vs agent roles.",
    },
    {
        "csv_index": 255,
        "first_name": "Sarah",
        "last_name": "Loftis",
        "title": "REALTOR at Stephen Cooley Real Estate",
        "company": "Stephen Cooley Real Estate",
        "email": "sarah@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/sarah-kate-loftis-5862aa206",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Realtor at Stephen Cooley Charlotte NC; site highlights neighborhood guides for Ballantyne, Waxhaw, and Lake Wylie with team-led buyer and seller marketing.",
        "research_notes": "Charlotte agent listing media. CooleyTeam Twitter active.",
    },
    {
        "csv_index": 256,
        "first_name": "Wendi",
        "last_name": "Canty",
        "title": "Leadership Management",
        "company": "Stephen Cooley Real Estate",
        "email": "wendi@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/wendi-canty-78a13872",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Leadership management at Stephen Cooley Rock Hill; firm positions as top Rock Hill agents with Ebenezer Road headquarters and multi-market listings.",
        "research_notes": "Leadership sets agent video standard. Stephen Cooley namesake agent same batch.",
    },
    {
        "csv_index": 257,
        "first_name": "Steve",
        "last_name": "McAvenia",
        "title": "Real Estate Broker Associate",
        "company": "Red Tree Real Estate",
        "email": "steve@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/steve-mcavenia-88a71621",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Broker associate at Red Tree Real Estate Boston; redtreeboston.com lists Steve on the team since 2013 with two trees planted per transaction via One Tree Planted.",
        "research_notes": "Four Red Tree contacts batch 13. Nick and Samuel on team page.",
    },
    {
        "csv_index": 258,
        "first_name": "Stephanie",
        "last_name": "Capriulo",
        "title": "Senior Property Manager",
        "company": "Premier Property Solutions",
        "email": "stephanie@premierpropertyma.com",
        "website": "https://premierpropertyma.com",
        "linkedin": "http://www.linkedin.com/in/stephanie-capriulo-a05a2865",
        "twitter": "https://twitter.com/PremierPropMA",
        "facebook": "https://www.facebook.com/PremierPropertySolutionsMA",
        "research_signal": "Senior property manager at Premier Property Solutions Woburn; premierpropertyma.com cites Boston condo management, capital improvements, and Western MA expansion.",
        "research_notes": "Four Premier contacts batch 13. Rosie ops director same firm.",
    },
    {
        "csv_index": 259,
        "first_name": "Stephen",
        "last_name": "Cooley",
        "title": "Real Estate Agent",
        "company": "Stephen Cooley Real Estate",
        "email": "stephen@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/stephenjcooley",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Agent at the namesake Stephen Cooley Real Estate Rock Hill team; site promotes sell-for-highest-price positioning and cash-buyer programs.",
        "research_notes": "Namesake agent brand. Wendi leadership same batch.",
    },
    {
        "csv_index": 260,
        "first_name": "Nick",
        "last_name": "Burnes",
        "title": "Real Estate Agent",
        "company": "Red Tree Real Estate",
        "email": "nick@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/nick-burnes-57435712a",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Agent at Red Tree Real Estate Boston on Brookline-founded firm with May 2026 open-house articles and off-campus housing guides on redtreeboston.com.",
        "research_notes": "Nick listed on team carousel. Steve and Samuel same batch.",
    },
    {
        "csv_index": 261,
        "first_name": "Tonja",
        "last_name": "Morrell",
        "title": "Realtor",
        "company": "Stephen Cooley Real Estate",
        "email": "morrell@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/tonja-morrell-7636a922",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Realtor at Stephen Cooley Fort Mill SC; firm keywords emphasize Charlotte real estate investing and negotiating for buyers and sellers.",
        "research_notes": "Fort Mill desk. Sharon broker same batch.",
    },
    {
        "csv_index": 262,
        "first_name": "Stephanie",
        "last_name": "Toomey",
        "title": "Portfolio Manager",
        "company": "Premier Property Solutions",
        "email": "st@premierpropertyma.com",
        "website": "https://premierpropertyma.com",
        "linkedin": "http://www.linkedin.com/in/stephanie-toomey-0aa4331a4",
        "twitter": "https://twitter.com/PremierPropMA",
        "facebook": "https://www.facebook.com/PremierPropertySolutionsMA",
        "research_signal": "Portfolio manager at Premier Property Solutions; site trustee testimonials praise one-hour meetings and building upkeep across Greater Boston condos.",
        "research_notes": "Portfolio angle for investor owners. Stephanie Capriulo senior PM same batch.",
    },
    {
        "csv_index": 263,
        "first_name": "Rosie",
        "last_name": "Villanueva",
        "title": "Director Of Operations",
        "company": "Premier Property Solutions",
        "email": "rv@premierpropertyma.com",
        "website": "https://premierpropertyma.com",
        "linkedin": "http://www.linkedin.com/in/rosie-villanueva-5a895233",
        "twitter": "https://twitter.com/PremierPropMA",
        "facebook": "https://www.facebook.com/PremierPropertySolutionsMA",
        "research_signal": "Director of operations at Premier Property Solutions Boston; firm mission is personalized service with expedient follow-through on owner and trustee issues.",
        "research_notes": "Ops leader for PM firm media consistency.",
    },
    {
        "csv_index": 264,
        "first_name": "Samuel",
        "last_name": "Mataev",
        "title": "Sales And Leasing Agent",
        "company": "Red Tree Real Estate",
        "email": "smataev@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/samuel-mataev-4340a311a",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Sales and leasing agent at Red Tree Real Estate; site features Samuel on the Boston team with rental and September-lease content for university markets.",
        "research_notes": "Leasing plus sales. Lena Lyons ops director writes open-house articles on site.",
    },
    {
        "csv_index": 265,
        "first_name": "Sharon",
        "last_name": "Salisbury",
        "title": "Realtor/Broker",
        "company": "Stephen Cooley Real Estate",
        "email": "sharon@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/sharonsalisbury",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Realtor and broker at Stephen Cooley Clover SC; firm runs instant valuation and cash-offer funnels agents can embed in listing marketing.",
        "research_notes": "Broker-level Cooley team. Six contacts need cross-differentiation in email 3.",
    },
    {
        "csv_index": 266,
        "first_name": "Steven",
        "last_name": "Schlom",
        "title": "Leasing / Sales Manager",
        "company": "Premier Property Solutions",
        "email": "stevenschlom@premierpropertyboston.com",
        "website": "https://premierpropertyma.com",
        "linkedin": "http://www.linkedin.com/in/steven-schlom-b0279b11",
        "twitter": "https://twitter.com/PremierPropMA",
        "facebook": "https://www.facebook.com/PremierPropertySolutionsMA",
        "research_signal": "Leasing and sales manager at Premier Property Solutions Boston; brokerage office on Newbury Street per site with property management at 190 High Street.",
        "research_notes": "premierpropertyboston.com email domain. Red Tree also has leasing manager content on blog.",
    },
]

COPY = {
    "kelcie.gibbel@ltic.com": [
        [
            "Sales exec Prescott",
            "Hi Kelcie,\n\nYou sales executive at Lawyers Title Prescott AZ on national ltic.com with title insurance and escrow in the CSV keywords.\n\nSales executives win when referral partners get short clips they actually forward, not dense PDFs.\n\nWe finish supplied partner and event footage.\n\nWorth a sample?",
        ],
        [
            "Prescott not Phoenix",
            "Hi Kelcie,\n\nNorthern Arizona partners still expect national-brand polish on every outreach touch.\n\nWe batch hook variants from one master interview you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Christy Phoenix separate",
            "Hi Kelcie,\n\nChristy Stokes may have seen Phoenix sales notes in batch 12; yours is Kelcie-led Prescott growth.\n\nOpen to a partner reel plan?",
        ],
    ],
    "aduncan@txprem.com": [
        [
            "Branch mgr Terrell",
            "Hi Amy,\n\nYou branch manager and escrow officer at Texas Premier Title Terrell with dedicated team positioning in the CSV and active texaspremiertitle Facebook.\n\nBranch managers scale when every assistant sends the same wire-safety clip quality.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Terrell desk standard",
            "Hi Amy,\n\nTerrell, Plano, and Dallas desks should sound like one firm on video, not three different styles.\n\nWe standardize on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Corres Plano separate",
            "Hi Amy,\n\nCorres Marisa may have seen Plano branch notes in batch 12; yours is Amy-led Terrell standards.\n\nWant a branch enablement outline?",
        ],
    ],
    "cmaciel@revolvre.com": [
        [
            "Marketing revolv",
            "Hi Christina,\n\nYou marketing specialist and lifetime advisor at revolv Somerset with short sales and bank-owned listings in the firm keywords.\n\nMarketing owns whether agent reels match the professional-services story at 865 County St.\n\nWe finish supplied listing and seminar footage.\n\nWorth a sample?",
        ],
        [
            "Advisor brand clips",
            "Hi Christina,\n\nLifetime advisor positioning should show in forty-five second hooks, not static flyers alone.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Cory agent separate",
            "Hi Christina,\n\nCory Dasilva may have seen salesperson notes in batch 12; yours is Christina-led marketing and advisor media.\n\nOpen to a revolv reel spec?",
        ],
    ],
    "kkisiday@phenixtitle.com": [
        [
            "Marketing closing NH",
            "Hi Kelly,\n\nYou marketing director and closing agent at Phenix Nashua where phenixtitle.com lists twelve offices and eighteen agents across New England.\n\nDual roles win when partner reels and desk explainers share one finishing standard.\n\nWe finish supplied event and closing footage.\n\nWorth a sample?",
        ],
        [
            "Closing agent hooks",
            "Hi Kelly,\n\nClosing agents need wire-safety clips that still look as polished as your marketing campaigns.\n\nWe batch variants from narration you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Michael Cossitt separate",
            "Hi Kelly,\n\nMichael Cossitt may have seen marketing director notes in batch 12; yours is Kelly-led NH desk and brand.\n\nWant a closing-plus-marketing kit outline?",
        ],
    ],
    "colin.joy@ltic.com": [
        [
            "Junior escrow San Diego",
            "Hi Colin,\n\nYou junior escrow officer at Lawyers Title San Diego on national ltic.com while lticsd.com highlights Good people doing great work for local agents.\n\nJunior officers grow faster when training clips look production-grade, not screen recordings left raw.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Agent ONE netsheets",
            "Hi Colin,\n\nAgent education should match the polish of net sheet and farm tools agents already trust.\n\nWe engineer shorts from footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Melody SD separate",
            "Hi Colin,\n\nMelody Coleman may have seen San Diego account notes in batch 7; yours is Colin-led escrow training.\n\nOpen to a junior-officer reel spec?",
        ],
    ],
    "cbarlow@phenixtitle.com": [
        [
            "Closing agent Portsmouth",
            "Hi Chase,\n\nYou closing agent at Phenix Portsmouth NH on a firm site built around title insurance, mortgage closings, and multi-state offices.\n\nAgents and lenders forward clips that look consistent with Phenix marketing, not one-off phone recordings.\n\nWe polish supplied partner walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "NH partner media",
            "Hi Chase,\n\nPortsmouth partners still judge the whole brand by your listing and closing media.\n\nWe batch hooks from one shoot day you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Kelly Kisiday separate",
            "Hi Chase,\n\nKelly Kisiday may get marketing and closing notes this batch; yours is Chase-led partner-facing media.\n\nWant an agent-forwardable reel outline?",
        ],
    ],
    "cdippel@txprem.com": [
        [
            "Corp ops escrow Dallas",
            "Hi Creighton,\n\nYou corporate operations escrow officer at Texas Premier Title Dallas with contract reviews in the CSV while txprem.com DNS still propagates.\n\nCorporate ops scales when every branch uses the same fraud and timeline template.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Desk consistency TX",
            "Hi Creighton,\n\nSamantha Morehead set ops standards in batch 12; corporate video should match what Terrell and Grand Prairie desks send.\n\nWe standardize on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Amy Terrell separate",
            "Hi Creighton,\n\nAmy Duncan may get Terrell branch notes this batch; yours is Creighton-led corporate consistency.\n\nWant an ops enablement outline?",
        ],
    ],
    "vicki@stephencooley.com": [
        [
            "Closing agent Cooley",
            "Hi Vicki,\n\nYou closing agent at Stephen Cooley Fort Mill where stephencooley.com pushes highest-price sales, instant home value, and cash-offer programs.\n\nClosing specialists cut repeat questions when timeline clips look clear on mobile.\n\nWe finish supplied client walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Cash offer funnel",
            "Hi Vicki,\n\nCash-offer and valuation funnels should pair with video that explains next steps in under sixty seconds.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Sarah realtor separate",
            "Hi Vicki,\n\nSarah Loftis may get Charlotte realtor notes; yours is Vicki-led closing clarity.\n\nOpen to a closing FAQ reel spec?",
        ],
    ],
    "sarah@stephencooley.com": [
        [
            "Realtor Charlotte Cooley",
            "Hi Sarah,\n\nYou realtor at Stephen Cooley Charlotte where the site maps Ballantyne, Waxhaw, and Lake Wylie neighborhood guides.\n\nAgents win when listing tours look cinematic, not unedited phone footage.\n\nWe polish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Neighborhood hooks",
            "Hi Sarah,\n\nEach neighborhood guide should become a forty-five second hook from one master shoot day.\n\nPost-production on footage you supply.\n\nCurious?",
        ],
        [
            "Tonja Fort Mill",
            "Hi Sarah,\n\nTonja Morrell may get Fort Mill notes; yours is Sarah-led Charlotte listing media.\n\nWant an agent reel plan?",
        ],
    ],
    "wendi@stephencooley.com": [
        [
            "Leadership Cooley Rock Hill",
            "Hi Wendi,\n\nYou leadership management at Stephen Cooley Rock Hill with Ebenezer Road headquarters and top-team positioning on stephencooley.com.\n\nLeaders set whether every agent sends the same listing and seller-reel quality.\n\nWe finish supplied team event footage.\n\nWorth a sample?",
        ],
        [
            "Multi-market listings",
            "Hi Wendi,\n\nRock Hill to Charlotte listings should share one video template so the brand feels national, not fragmented.\n\nWe batch cuts from footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Stephen namesake separate",
            "Hi Wendi,\n\nStephen Cooley may get namesake agent notes; yours is Wendi-led leadership standards.\n\nOpen to a team enablement outline?",
        ],
    ],
    "steve@redtreeboston.com": [
        [
            "Broker Red Tree Boston",
            "Hi Steve,\n\nYou broker associate at Red Tree Real Estate where redtreeboston.com lists you on the team since 2013 and plants two trees per transaction with One Tree Planted.\n\nBrokers win when listing hooks feel as data-backed as the comps you cite.\n\nWe polish supplied tour footage.\n\nWorth a sample?",
        ],
        [
            "Greater Boston since 2013",
            "Hi Steve,\n\nServing Greater Boston since 2013 means buyers expect production-grade open-house reels, not slideshow stills.\n\nWe engineer retention pacing on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Nick agent separate",
            "Hi Steve,\n\nNick Burnes may get parallel agent notes; yours is Steve-led broker associate media.\n\nWant a Boston listing reel spec?",
        ],
    ],
    "stephanie@premierpropertyma.com": [
        [
            "Senior PM Premier",
            "Hi Stephanie,\n\nYou senior property manager at Premier Property Solutions Woburn where premierpropertyma.com highlights Boston condo management, capital improvements, and Western MA expansion.\n\nPMs retain owners when building update videos look as disciplined as your maintenance logs.\n\nWe finish supplied property walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Trustee testimonials",
            "Hi Stephanie,\n\nTrustees praise one-hour meetings on your site; video updates should save even more back-and-forth.\n\nWe polish supplied interior footage with captions.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Rosie ops separate",
            "Hi Stephanie,\n\nRosie Villanueva may get ops director notes; yours is Stephanie-led senior PM owner comms.\n\nOpen to a trustee update reel outline?",
        ],
    ],
    "stephen@stephencooley.com": [
        [
            "Namesake agent Cooley",
            "Hi Stephen,\n\nYou agent at the namesake Stephen Cooley team where stephencooley.com sells for the highest possible price on your timeline with cash-buyer options.\n\nNamesake brands win when your listings set the video standard for Wendi, Sarah, and the roster.\n\nWe polish supplied tour footage.\n\nWorth a sample?",
        ],
        [
            "Rock Hill headquarters",
            "Hi Stephen,\n\nRock Hill headquarters credibility should show in the first three seconds of every listing reel.\n\nWe batch hook variants from one shoot you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Wendi leadership separate",
            "Hi Stephen,\n\nWendi Canty may get leadership notes; yours is Stephen-led personal brand media.\n\nWant a namesake listing reel plan?",
        ],
    ],
    "nick@redtreeboston.com": [
        [
            "Agent Red Tree May 2026",
            "Hi Nick,\n\nYou agent at Red Tree Real Estate Boston where redtreeboston.com published May 2026 open-house roundups and off-campus housing guides.\n\nAgents win when weekend tour clips look ready for Instagram, not buried in MLS stills.\n\nWe polish supplied open-house footage.\n\nWorth a sample?",
        ],
        [
            "Brookline founded 2013",
            "Hi Nick,\n\nFounded in Brookline in 2013, the brand should feel premium in every neighborhood reel from Newton to Jamaica Plain.\n\nPost-production on footage you supply.\n\nUseful?",
        ],
        [
            "Samuel leasing separate",
            "Hi Nick,\n\nSamuel Mataev may get leasing notes; yours is Nick-led sales listing media.\n\nOpen to an open-house reel spec?",
        ],
    ],
    "morrell@stephencooley.com": [
        [
            "Realtor Fort Mill",
            "Hi Tonja,\n\nYou realtor at Stephen Cooley Fort Mill with Charlotte investing and buyer-agent keywords in the firm CSV.\n\nFort Mill agents compete on speed; hooks should surface price and timeline in three seconds.\n\nWe polish supplied listing footage.\n\nWorth a sample?",
        ],
        [
            "CooleyTeam social",
            "Hi Tonja,\n\nCooleyTeam Twitter and Facebook need shorts agents will actually post, not raw tour files.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Sharon broker separate",
            "Hi Tonja,\n\nSharon Salisbury may get broker notes; yours is Tonja-led Fort Mill listings.\n\nWant an agent reel outline?",
        ],
    ],
    "st@premierpropertyma.com": [
        [
            "Portfolio mgr Premier",
            "Hi Stephanie,\n\nYou portfolio manager at Premier Property Solutions where trustee testimonials praise one-hour meetings and spotless buildings on premierpropertyma.com.\n\nPortfolio managers retain investors when quarterly updates look cinematic, not spreadsheet screenshots.\n\nWe finish supplied property footage.\n\nWorth a sample?",
        ],
        [
            "Owner trustee updates",
            "Hi Stephanie,\n\nOwners decide faster when capital project plans include clear video walkthroughs.\n\nWe polish supplied site footage with motion and captions.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Capriulo PM separate",
            "Hi Stephanie,\n\nStephanie Capriulo may get senior PM notes; yours is Toomey-led portfolio storytelling.\n\nOpen to an investor update reel spec?",
        ],
    ],
    "rv@premierpropertyma.com": [
        [
            "Ops director Premier",
            "Hi Rosie,\n\nYou director of operations at Premier Property Solutions Boston with a mission of expedient follow-through on owner and trustee issues.\n\nOps leaders scale when every PM sends the same owner-update video template.\n\nWe finish supplied maintenance and walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Western MA expansion",
            "Hi Rosie,\n\nWestern Massachusetts expansion means Boston and Springfield desks should sound identical on video.\n\nWe standardize on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Steven leasing separate",
            "Hi Rosie,\n\nSteven Schlom may get leasing manager notes; yours is Rosie-led ops consistency.\n\nWant an ops media kit outline?",
        ],
    ],
    "smataev@redtreeboston.com": [
        [
            "Leasing agent Red Tree",
            "Hi Samuel,\n\nYou sales and leasing agent at Red Tree Boston on a team page with Samuel listed beside May 2026 rental and September-lease articles on redtreeboston.com.\n\nLeasing agents win when apartment tours hook in three seconds on mobile.\n\nWe polish supplied unit walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Off campus housing",
            "Hi Samuel,\n\nOff-campus housing guides for BU, Northeastern, and MIT should become short reels renters actually watch.\n\nWe batch variants from footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Steve broker separate",
            "Hi Samuel,\n\nSteve McAvenia may get broker associate notes; yours is Samuel-led leasing media.\n\nOpen to a rental reel plan?",
        ],
    ],
    "sharon@stephencooley.com": [
        [
            "Broker Clover SC",
            "Hi Sharon,\n\nYou realtor and broker at Stephen Cooley Clover with instant valuation and cash-offer funnels on stephencooley.com.\n\nBrokers set whether the team’s social clips match the highest-price positioning on the site.\n\nWe polish supplied seller and buyer footage.\n\nWorth a sample?",
        ],
        [
            "Seller timeline video",
            "Hi Sharon,\n\nSeller timelines confuse less when video explains cash-offer vs traditional paths side by side.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Wendi leadership separate",
            "Hi Sharon,\n\nWendi Canty may get leadership notes; yours is Sharon-led broker media.\n\nWant a seller-education reel outline?",
        ],
    ],
    "stevenschlom@premierpropertyboston.com": [
        [
            "Leasing mgr Premier",
            "Hi Steven,\n\nYou leasing and sales manager at Premier Property Solutions with Newbury Street brokerage and High Street management offices on premierpropertyma.com.\n\nLeasing managers fill units faster when listing tours look production-grade.\n\nWe polish supplied unit and amenity footage.\n\nWorth a sample?",
        ],
        [
            "Boston rental market",
            "Hi Steven,\n\nGreater Boston rentals compete on clarity; hooks should show layout and commute in the first frame.\n\nWe batch cuts from footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Rosie ops separate",
            "Hi Steven,\n\nRosie Villanueva may get ops notes; yours is Steven-led leasing and sales media.\n\nOpen to a rental portfolio reel spec?",
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
                failures.append((email, subj, issues, word_count(body)))

    if failures:
        for f in failures:
            print("FAIL", f)
        raise SystemExit(1)

    (ROOT / "campaigns" / "pilot-20-batch13-research.json").write_text(
        json.dumps(research_out, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "campaigns" / "pilot-20-batch13-copy.json").write_text(
        json.dumps(COPY, indent=2) + "\n", encoding="utf-8"
    )
    print("OK: 20 leads, 60 emails, QA pre-check passed")


if __name__ == "__main__":
    main()
