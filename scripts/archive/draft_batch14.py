#!/usr/bin/env python3
"""Draft and QA-check batch 14 research + copy."""

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
        "csv_index": 267,
        "first_name": "Moshe",
        "last_name": "Rosenbloom",
        "title": "Real Estate Agent",
        "company": "Red Tree Real Estate",
        "email": "moshe@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/moshe-rosenbloom-6a0a13147",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Agent at Red Tree Real Estate Brookline MA; redtreeboston.com lists Moshe on the Boston team founded in 2013 with two trees planted per transaction.",
        "research_notes": "Ten Red Tree contacts batch 14. Steve, Nick, Samuel batch 13. Brookline home market.",
    },
    {
        "csv_index": 268,
        "first_name": "Zach",
        "last_name": "Willis",
        "title": "Real Estate Agent",
        "company": "Stephen Cooley Real Estate",
        "email": "zach@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/zach-willis-945582168",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Agent at Stephen Cooley Rock Hill SC; stephencooley.com promotes sell-for-highest-price positioning and cash-offer programs from Ebenezer Road headquarters.",
        "research_notes": "Ten Cooley contacts batch 14. Six contacted batch 13. Zach Rock Hill agent.",
    },
    {
        "csv_index": 269,
        "first_name": "Toby",
        "last_name": "Stephens",
        "title": "Real Estate Consultant",
        "company": "Stephen Cooley Real Estate",
        "email": "toby@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/tobycstephens",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Real estate consultant at Stephen Cooley Charlotte NC; firm site maps Charlotte, Concord, and Huntersville neighborhood guides for buyers and sellers.",
        "research_notes": "Consultant vs realtor title. Differentiate from agents Sarah and Kim Charlotte.",
    },
    {
        "csv_index": 270,
        "first_name": "Sherry",
        "last_name": "Avant",
        "title": "Realtor",
        "company": "Stephen Cooley Real Estate",
        "email": "sherry@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/sherry-avant-9665b935",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Realtor at Stephen Cooley Rock Hill; site highlights Fort Mill, Gastonia, and Waxhaw markets with instant home value tools.",
        "research_notes": "Rock Hill desk. Amanda and Jackson same city batch 14.",
    },
    {
        "csv_index": 271,
        "first_name": "Eric",
        "last_name": "Anderson",
        "title": "Licensed Real Estate Professional",
        "company": "Red Tree Real Estate",
        "email": "eric@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/eric-anderson-7424874b",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Licensed professional at Red Tree Real Estate Boston; firm articles cover May 2026 open houses across Newton, Dedham, and Brighton on redtreeboston.com.",
        "research_notes": "Eric on team carousel prior fetch. Open-house reel angle.",
    },
    {
        "csv_index": 272,
        "first_name": "Dan",
        "last_name": "Bedjanov",
        "title": "Real Estate Agent",
        "company": "Red Tree Real Estate",
        "email": "dan@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/danielbedjanov",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Agent at Red Tree Real Estate Boston; site team page lists Daniel Bedjanov with featured listings up to $2.2M in Newton and Commonwealth Ave inventory.",
        "research_notes": "LinkedIn danielbedjanov. Premium listing hooks.",
    },
    {
        "csv_index": 273,
        "first_name": "Alexandra",
        "last_name": "Mishenina",
        "title": "Real Estete professional",
        "company": "Red Tree Real Estate",
        "email": "alexandra@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/alexandra-mishenina-1548baa2",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Real estate professional at Red Tree Boston; Alexandra Mishenina appears on the redtreeboston.com team carousel serving Greater Boston since 2013.",
        "research_notes": "CSV typo Real Estete. Team page confirmed May 2026 fetch batch 13.",
    },
    {
        "csv_index": 274,
        "first_name": "Julie",
        "last_name": "Gaines",
        "title": "Real Estate Agent",
        "company": "Stephen Cooley Real Estate",
        "email": "julie@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/julie-gaines-9994a58",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Agent at Stephen Cooley Fort Mill SC; firm promotes Tega Cay and Baxter Village neighborhood content alongside Rock Hill listings.",
        "research_notes": "Fort Mill market. Kellee broker same town batch 14.",
    },
    {
        "csv_index": 275,
        "first_name": "Amanda",
        "last_name": "Ballog",
        "title": "Professional Realtor",
        "company": "Stephen Cooley Real Estate",
        "email": "amanda@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/amanda-ballog-05208079",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Professional realtor at Stephen Cooley Rock Hill; CSV keywords emphasize Charlotte real estate investing and buyer-agent negotiation.",
        "research_notes": "Rock Hill realtor. Sherry and Jackson parallel.",
    },
    {
        "csv_index": 276,
        "first_name": "Lee",
        "last_name": "Kennon",
        "title": "Real Estate Agent",
        "company": "Red Tree Real Estate",
        "email": "lee@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/lee-kennon-5b5676227",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Agent at Red Tree Real Estate Dedham MA; site neighborhood guides include Dedham alongside Brookline, Newton, and Jamaica Plain.",
        "research_notes": "Dedham-focused agent. Lee Kennon on team page batch 13 site fetch.",
    },
    {
        "csv_index": 277,
        "first_name": "Kellee",
        "last_name": "Wilson",
        "title": "NC/ SC Broker/ Realtor",
        "company": "Stephen Cooley Real Estate",
        "email": "kellee@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/kellee-wilson-4a643959",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "NC and SC broker and realtor at Stephen Cooley Fort Mill; dual-state license fits firm Charlotte-to-Rock Hill footprint on stephencooley.com.",
        "research_notes": "Broker title. Sharon broker Clover batch 13. Leadership media angle.",
    },
    {
        "csv_index": 278,
        "first_name": "Brandyn",
        "last_name": "Huynh",
        "title": "Licensed Real Estate Professional",
        "company": "Red Tree Real Estate",
        "email": "brandyn@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/brandynhuynh",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Licensed professional at Red Tree Boston; Brandyn Huynh listed on team carousel with first-time buyer and market insights programs on redtreeboston.com.",
        "research_notes": "First-time buyer funnel on site. Brandyn on team page.",
    },
    {
        "csv_index": 279,
        "first_name": "Kim",
        "last_name": "Johnson",
        "title": "Professional Realtor",
        "company": "Stephen Cooley Real Estate",
        "email": "kim@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/kim-johnson-093a18a3",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Professional realtor at Stephen Cooley Charlotte NC; site neighborhood pages cover Ballantyne, Matthews, and Pineville for buyer marketing.",
        "research_notes": "Charlotte realtor. Toby consultant same market.",
    },
    {
        "csv_index": 280,
        "first_name": "Jackson",
        "last_name": "Burns",
        "title": "Real Estate Agent",
        "company": "Stephen Cooley Real Estate",
        "email": "jackson@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/jackson-burns-61a895161",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Agent at Stephen Cooley Rock Hill SC headquarters market; firm runs home-listing search across Rock Hill, Fort Mill, and Charlotte corridors.",
        "research_notes": "Rock Hill agent. HQ market emphasis.",
    },
    {
        "csv_index": 281,
        "first_name": "Denis",
        "last_name": "Cruz",
        "title": "Creative Director",
        "company": "Red Tree Real Estate",
        "email": "denis@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/denis-cruz-841482203",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Creative director at Red Tree Real Estate Boston; Denis Cruz on team page while site publishes agent-written market articles and open-house media May 2026.",
        "research_notes": "Only creative director in pilot. Strong post-production fit. Adam founder same batch.",
    },
    {
        "csv_index": 282,
        "first_name": "Adam",
        "last_name": "Kotkin",
        "title": "Owner",
        "company": "Red Tree Real Estate",
        "email": "adam@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/adam-kotkin-9a822b170",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Owner and co-founder of Red Tree Real Estate; redtreeboston.com states Adam Kotkin and Jerome Bibuld founded the Brookline firm in 2013 serving Greater Boston.",
        "research_notes": "Owner sets brand video standard. Denis creative director reports into brand ops.",
    },
    {
        "csv_index": 283,
        "first_name": "Chris",
        "last_name": "Hood",
        "title": "Realtor",
        "company": "Stephen Cooley Real Estate",
        "email": "chris@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/chris-hood-88065aa4",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Realtor at Stephen Cooley Rock Hill; CooleyTeam social and cash-offer landing pages support agent-led seller funnels.",
        "research_notes": "Rock Hill realtor. Chris vs Chris Hood distinct from other batches.",
    },
    {
        "csv_index": 284,
        "first_name": "Alex",
        "last_name": "Porfiris",
        "title": "Real Estate Agent",
        "company": "Stephen Cooley Real Estate",
        "email": "alex@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/alex-porfiris-228401284",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Agent at Stephen Cooley Mooresville NC; firm Lake Wylie and Marvin neighborhood guides sit near Mooresville lake-market buyers.",
        "research_notes": "Mooresville desk, not Rock Hill HQ. Lake market tours.",
    },
    {
        "csv_index": 285,
        "first_name": "James",
        "last_name": "Kopecky",
        "title": "Real Estate Agent",
        "company": "Red Tree Real Estate",
        "email": "james@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/jameskopecky",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "James Kopecky is Sales and Leasing Manager at Red Tree per site byline; published Renting vs Buying in Boston May 2026 guide on redtreeboston.com.",
        "research_notes": "CSV title agent but site says Sales and Leasing Manager. Samuel Mataev leasing batch 13.",
    },
    {
        "csv_index": 286,
        "first_name": "Ioana",
        "last_name": "Mindrean",
        "title": "Real Estate Agent",
        "company": "Red Tree Real Estate",
        "email": "ioana@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/ioana-mindrean-6905b3175",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Agent at Red Tree Real Estate Medford MA; site neighborhood coverage includes Medford alongside Somerville and Cambridge for renters and buyers.",
        "research_notes": "Medford market. Off-campus and rental content on parent site.",
    },
]

COPY = {
    "moshe@redtreeboston.com": [
        [
            "Agent Brookline Red Tree",
            "Hi Moshe,\n\nYou agent at Red Tree Real Estate Brookline where redtreeboston.com lists you on the team founded in 2013 with two trees planted per transaction.\n\nBrookline listings compete on polish; hooks should feel as local as the neighborhood guide you share.\n\nWe polish supplied tour footage.\n\nWorth a sample?",
        ],
        [
            "Greater Boston 2013",
            "Hi Moshe,\n\nBuyers scrolling Commonwealth Ave inventory decide in seconds whether video looks brokerage-grade.\n\nWe batch variants from one shoot you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Steve batch 13 separate",
            "Hi Moshe,\n\nSteve McAvenia may have seen broker notes in batch 13; yours is Moshe-led Brookline listings.\n\nOpen to a listing reel spec?",
        ],
    ],
    "zach@stephencooley.com": [
        [
            "Agent Rock Hill Cooley",
            "Hi Zach,\n\nYou agent at Stephen Cooley Rock Hill where stephencooley.com sells for the highest price on your timeline with cash-offer and instant-value funnels.\n\nRock Hill agents win when listing reels match the HQ brand on Ebenezer Road.\n\nWe polish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Cash offer funnel",
            "Hi Zach,\n\nCash-offer pages convert better when video explains seller options in under sixty seconds.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Stephen namesake separate",
            "Hi Zach,\n\nStephen Cooley may have seen namesake notes in batch 13; yours is Zach-led Rock Hill media.\n\nWant an agent reel outline?",
        ],
    ],
    "toby@stephencooley.com": [
        [
            "Consultant Charlotte",
            "Hi Toby,\n\nYou real estate consultant at Stephen Cooley Charlotte where the site maps Concord, Huntersville, and Ballantyne neighborhood guides.\n\nConsultants win when advisory clips look as sharp as the listing media agents post.\n\nWe polish supplied client education footage.\n\nWorth a sample?",
        ],
        [
            "Buyer education shorts",
            "Hi Toby,\n\nCharlotte buyers need forty-five second explainers they forward before scheduling consults.\n\nWe engineer retention on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Kim realtor separate",
            "Hi Toby,\n\nKim Johnson may get Charlotte realtor notes this batch; yours is Toby-led consultant media.\n\nOpen to a buyer-advisory reel plan?",
        ],
    ],
    "sherry@stephencooley.com": [
        [
            "Realtor Rock Hill",
            "Hi Sherry,\n\nYou realtor at Stephen Cooley Rock Hill with Fort Mill, Gastonia, and Waxhaw coverage on stephencooley.com.\n\nRealtors win when each market gets its own hook from one master walkthrough.\n\nWe polish supplied listing footage.\n\nWorth a sample?",
        ],
        [
            "Instant home value",
            "Hi Sherry,\n\nInstant valuation funnels should pair with video that sets price expectations before the call.\n\nWe batch cuts from footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Amanda parallel separate",
            "Hi Sherry,\n\nAmanda Ballog may get parallel Rock Hill notes; yours is Sherry-led listing story.\n\nWant a seller-reel spec?",
        ],
    ],
    "eric@redtreeboston.com": [
        [
            "Eric open houses May",
            "Hi Eric,\n\nYou licensed professional at Red Tree Boston where redtreeboston.com ran May 2026 open-house roundups across Newton, Dedham, and Brighton.\n\nAgents win when weekend tour clips are ready for Instagram the same day.\n\nWe polish supplied open-house footage.\n\nWorth a sample?",
        ],
        [
            "Featured listings",
            "Hi Eric,\n\nFeatured inventory up to $2.2M in Newton needs hooks that signal layout and light in three seconds.\n\nPost-production on footage you supply.\n\nCurious?",
        ],
        [
            "Nick batch 13 separate",
            "Hi Eric,\n\nNick Burnes may have seen open-house notes in batch 13; yours is Eric-led licensed professional media.\n\nOpen to a weekend tour reel outline?",
        ],
    ],
    "dan@redtreeboston.com": [
        [
            "Agent Daniel Bedjanov",
            "Hi Dan,\n\nYou agent at Red Tree Real Estate Boston on the team carousel with premium Newton and Back Bay style listings on redtreeboston.com.\n\nLuxury tours fail when pacing feels like unedited phone video.\n\nWe polish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Newton Commonwealth Ave",
            "Hi Dan,\n\nHigh-price buyers judge production quality before they judge square footage.\n\nWe engineer cinematic pacing on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Eric open house separate",
            "Hi Dan,\n\nEric Anderson may get open-house notes; yours is Dan-led premium listing media.\n\nWant a luxury reel spec?",
        ],
    ],
    "alexandra@redtreeboston.com": [
        [
            "Alexandra Boston team",
            "Hi Alexandra,\n\nYou real estate professional at Red Tree on the Boston team carousel serving Greater Boston since 2013 on redtreeboston.com.\n\nProfessionals win when every listing shares one brokerage-grade finishing template.\n\nWe polish supplied tour footage.\n\nWorth a sample?",
        ],
        [
            "Team carousel polish",
            "Hi Alexandra,\n\nYour profile should match the production quality of the firm's May 2026 market articles.\n\nWe batch hook variants from one shoot you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Brandyn buyers separate",
            "Hi Alexandra,\n\nBrandyn Huynh may get first-time buyer notes; yours is Alexandra-led general listing media.\n\nCurious about a team-template outline?",
        ],
    ],
    "julie@stephencooley.com": [
        [
            "Fort Mill Tega Cay",
            "Hi Julie,\n\nYou agent at Stephen Cooley Fort Mill where stephencooley.com highlights Tega Cay and Baxter Village neighborhoods.\n\nFort Mill listings need hooks that feel suburban-premium, not generic MLS stills.\n\nWe polish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Baxter Village tours",
            "Hi Julie,\n\nMaster-planned community tours should surface schools and amenities in the first three seconds.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Kellee broker separate",
            "Hi Julie,\n\nKellee Wilson may get broker notes; yours is Julie-led Fort Mill agent media.\n\nOpen to a neighborhood reel plan?",
        ],
    ],
    "amanda@stephencooley.com": [
        [
            "Realtor Rock Hill investing",
            "Hi Amanda,\n\nYou professional realtor at Stephen Cooley Rock Hill with Charlotte investing and buyer-negotiation keywords in the firm CSV.\n\nInvestor-facing listings need timeline and ROI hooks fast.\n\nWe polish supplied property footage.\n\nWorth a sample?",
        ],
        [
            "CooleyTeam social",
            "Hi Amanda,\n\nCooleyTeam Twitter needs shorts agents actually post, not raw tour uploads.\n\nWe batch cuts from footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Sherry parallel separate",
            "Hi Amanda,\n\nSherry Avant may get parallel Rock Hill notes; yours is Amanda-led investor buyer media.\n\nWant an agent reel outline?",
        ],
    ],
    "lee@redtreeboston.com": [
        [
            "Agent Dedham Red Tree",
            "Hi Lee,\n\nYou agent at Red Tree Real Estate Dedham where neighborhood guides on redtreeboston.com include Dedham beside Brookline and Jamaica Plain.\n\nDedham buyers decide on commute and layout; video should show both in three seconds.\n\nWe polish supplied tour footage.\n\nWorth a sample?",
        ],
        [
            "Suburban Boston hooks",
            "Hi Lee,\n\nSuburban listings need distinct hooks from urban condo reels on the same team.\n\nWe batch variants from one shoot you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Ioana Medford separate",
            "Hi Lee,\n\nIoana Mindrean may get Medford notes; yours is Lee-led Dedham listings.\n\nOpen to a suburban reel spec?",
        ],
    ],
    "kellee@stephencooley.com": [
        [
            "Broker NC SC Cooley",
            "Hi Kellee,\n\nYou NC and SC broker and realtor at Stephen Cooley Fort Mill matching the firm Charlotte-to-Rock Hill footprint on stephencooley.com.\n\nBrokers set whether dual-state agents send the same listing reel quality.\n\nWe polish supplied team and listing footage.\n\nWorth a sample?",
        ],
        [
            "Dual license brand",
            "Hi Kellee,\n\nNC and SC clips should share one template so the Cooley brand feels unified.\n\nWe standardize on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Sharon broker separate",
            "Hi Kellee,\n\nSharon Salisbury may have seen Clover broker notes in batch 13; yours is Kellee-led Fort Mill broker media.\n\nWant a broker enablement outline?",
        ],
    ],
    "brandyn@redtreeboston.com": [
        [
            "First time buyers Red Tree",
            "Hi Brandyn,\n\nYou licensed professional at Red Tree Boston where redtreeboston.com promotes first-time home buyer programs and free market analysis.\n\nFirst-time buyer funnels convert when explainer video matches the clarity of your comps report.\n\nWe polish supplied education footage.\n\nWorth a sample?",
        ],
        [
            "Market insights video",
            "Hi Brandyn,\n\nMarket insights pages should pair with forty-five second hooks renters and buyers actually watch.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Adam owner separate",
            "Hi Brandyn,\n\nAdam Kotkin may get owner notes; yours is Brandyn-led buyer education media.\n\nOpen to a first-time buyer reel plan?",
        ],
    ],
    "kim@stephencooley.com": [
        [
            "Realtor Charlotte Cooley",
            "Hi Kim,\n\nYou professional realtor at Stephen Cooley Charlotte with Ballantyne, Matthews, and Pineville guides on stephencooley.com.\n\nCharlotte agents compete on speed; listing hooks should surface price and neighborhood in three seconds.\n\nWe polish supplied tour footage.\n\nWorth a sample?",
        ],
        [
            "Ballantyne listings",
            "Hi Kim,\n\nBallantyne luxury expects production-grade walkthroughs, not phone footage left unedited.\n\nWe batch variants from one shoot you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Toby consultant separate",
            "Hi Kim,\n\nToby Stephens may get consultant notes; yours is Kim-led Charlotte listing media.\n\nWant an agent reel spec?",
        ],
    ],
    "jackson@stephencooley.com": [
        [
            "Agent HQ Rock Hill",
            "Hi Jackson,\n\nYou agent at Stephen Cooley Rock Hill HQ market where the site searches listings across Rock Hill, Fort Mill, and Charlotte.\n\nHQ agents should set the video bar for the whole roster.\n\nWe polish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Multi-corridor search",
            "Hi Jackson,\n\nOne master tour should become distinct hooks for Rock Hill vs Fort Mill buyers.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Zach agent separate",
            "Hi Jackson,\n\nZach Willis may get parallel Rock Hill notes; yours is Jackson-led HQ corridor media.\n\nOpen to a listing reel outline?",
        ],
    ],
    "denis@redtreeboston.com": [
        [
            "Creative director Red Tree",
            "Hi Denis,\n\nYou creative director at Red Tree Real Estate while the site publishes agent market articles and May 2026 open-house media on redtreeboston.com.\n\nCreative leads feel the gap when agent raw footage never matches the brand articles you oversee.\n\nWe finish supplied tours and events with retention pacing and hooks.\n\nWorth a sample?",
        ],
        [
            "Agent content scale",
            "Hi Denis,\n\nScaling forty agents means one finishing template, not forty different edit styles.\n\nWe standardize post-production on footage your team supplies.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Adam founder separate",
            "Hi Denis,\n\nAdam Kotkin may get founder notes; yours is Denis-led creative systems.\n\nWant a brokerage content pipeline outline?",
        ],
    ],
    "adam@redtreeboston.com": [
        [
            "Founder Red Tree 2013",
            "Hi Adam,\n\nYou owner and co-founder of Red Tree Real Estate; redtreeboston.com says you and Jerome Bibuld started the Brookline firm in 2013 serving Greater Boston.\n\nFounders set whether two trees per deal is backed by video that feels as intentional as the sustainability story.\n\nWe finish supplied brand and listing footage.\n\nWorth a sample?",
        ],
        [
            "Team production standard",
            "Hi Adam,\n\nDenis and the agent roster scale faster when finishing is a black-box post partner, not desk-by-desk edits.\n\nWe engineer hooks on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Denis creative separate",
            "Hi Adam,\n\nDenis Cruz may get creative director notes; yours is Adam-led founder brand standard.\n\nOpen to a firm-wide reel plan?",
        ],
    ],
    "chris@stephencooley.com": [
        [
            "Realtor Rock Hill Hood",
            "Hi Chris,\n\nYou realtor at Stephen Cooley Rock Hill with CooleyTeam social and cash-offer funnels on stephencooley.com.\n\nSeller reels should explain traditional vs cash paths without a twenty-minute call.\n\nWe polish supplied seller footage.\n\nWorth a sample?",
        ],
        [
            "Seller education video",
            "Hi Chris,\n\nSeller education cuts listing confusion when pacing is built for mobile.\n\nWe engineer shorts from footage you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Wendi leadership separate",
            "Hi Chris,\n\nWendi Canty may have seen leadership notes in batch 13; yours is Chris-led Rock Hill seller media.\n\nWant a seller FAQ reel outline?",
        ],
    ],
    "alex@stephencooley.com": [
        [
            "Mooresville lake market",
            "Hi Alex,\n\nYou agent at Stephen Cooley Mooresville near Lake Wylie and Marvin neighborhood guides on stephencooley.com.\n\nLake-market buyers want waterfront and commute hooks in the first frame.\n\nWe polish supplied tour footage.\n\nWorth a sample?",
        ],
        [
            "Lake Wylie tours",
            "Hi Alex,\n\nMooresville listings should not reuse Rock Hill hooks; water views need their own three-second open.\n\nWe batch variants from one shoot you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Julie Fort Mill separate",
            "Hi Alex,\n\nJulie Gaines may get Fort Mill notes; yours is Alex-led Mooresville lake media.\n\nOpen to a lake-market reel spec?",
        ],
    ],
    "james@redtreeboston.com": [
        [
            "Sales leasing mgr Kopecky",
            "Hi James,\n\nYou Sales and Leasing Manager at Red Tree per your May 2026 Renting vs Buying in Boston article on redtreeboston.com.\n\nLeasing leaders win when rental and sales clips share one polished template.\n\nWe polish supplied unit and market footage.\n\nWorth a sample?",
        ],
        [
            "Renting vs buying guide",
            "Hi James,\n\nThat guide should spawn forty-five second hooks for Instagram, not live only as a long blog post.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Samuel leasing separate",
            "Hi James,\n\nSamuel Mataev may have seen leasing agent notes in batch 13; yours is James-led sales and leasing management media.\n\nWant a rental content kit outline?",
        ],
    ],
    "ioana@redtreeboston.com": [
        [
            "Agent Medford Red Tree",
            "Hi Ioana,\n\nYou agent at Red Tree Real Estate Medford where neighborhood coverage includes Medford with Somerville and Cambridge on redtreeboston.com.\n\nMedford renters and buyers compare units fast; tours need commuter and layout hooks immediately.\n\nWe polish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Rental market shorts",
            "Hi Ioana,\n\nSeptember-lease and off-campus content on the parent site should become agent-forwardable Medford cuts.\n\nWe batch variants from footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Lee Dedham separate",
            "Hi Ioana,\n\nLee Kennon may get Dedham notes; yours is Ioana-led Medford listings.\n\nOpen to a rental reel plan?",
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

    (ROOT / "campaigns" / "pilot-20-batch14-research.json").write_text(
        json.dumps(research_out, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "campaigns" / "pilot-20-batch14-copy.json").write_text(
        json.dumps(COPY, indent=2) + "\n", encoding="utf-8"
    )
    print("OK: 20 leads, 60 emails, QA pre-check passed")


if __name__ == "__main__":
    main()
