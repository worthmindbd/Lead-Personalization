#!/usr/bin/env python3
"""Draft batch 11 research + copy JSON with inline QA."""
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


def wc(text):
    return len(re.findall(r"\b\w+\b", text))


def qa(subject, body):
    issues = []
    n = wc(body)
    if n > 100:
        issues.append(f"words {n}")
    if len(subject) > 60:
        issues.append(f"subj {len(subject)}")
    low = (subject + body).lower()
    for b in BANNED:
        if b in low:
            issues.append(b)
    if "calendly" in low or "book 15" in low or "free tuesday" in low:
        issues.append("hard CTA")
    return issues


RESEARCH = [
    {
        "row": 208,
        "csv_index": 207,
        "first_name": "Jenny",
        "last_name": "Romero",
        "title": "Settlement Processor",
        "company": "Vesta Settlements, LLC",
        "email": "jromero@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/jenny-romero-0876911a4",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Settlement processor at Vesta Settlements; firm lists eight offices, Closings Elevated, and YouTube realtor education per prior site research.",
        "research_notes": "Many Vesta contacts batches 9-10. Jenny Romero processor angle. Distinct from Vesta Settlements LLC row elsewhere in CSV.",
    },
    {
        "row": 209,
        "csv_index": 208,
        "first_name": "Christina",
        "last_name": "Yevoli-Crabtree",
        "title": "Contract Manager",
        "company": "Vesta Settlements, LLC",
        "email": "cyevoli@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/christina-yevoli-crabtree-0876911a4",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Contract manager at Vesta Settlements; CSV keywords include contract execution and digital EMD delivery for Northern Virginia title.",
        "research_notes": "Contract manager owns timeline accuracy before closers. Legal-ops hybrid role.",
    },
    {
        "row": 210,
        "csv_index": 209,
        "first_name": "John",
        "last_name": "Spencer",
        "title": "Owner / Broker at Spencer Properties",
        "company": "Spencer Properties",
        "email": "john@spencerprop.com",
        "website": "https://spencerprop.com",
        "linkedin": "http://www.linkedin.com/in/john-spencer-0876911a4",
        "twitter": "https://twitter.com/spencerprops",
        "facebook": "https://facebook.com/spencerprop",
        "research_signal": "Owner and broker at Spencer Properties Raleigh; spencerprop.com highlights Matterport tours, sold portfolio, and Raleigh trusted experts positioning.",
        "research_notes": "Jennifer Spencer broker owner same firm batch. Emma buyer specialist batch 10. Website fetched prior batches.",
    },
    {
        "row": 211,
        "csv_index": 210,
        "first_name": "Lauren",
        "last_name": "Jin",
        "title": "Post Closer",
        "company": "Vesta Settlements, LLC",
        "email": "ljin@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/lauren-jin-0876911a4",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Post closer at Vesta Settlements with hybrid and e-closing keywords in firm CSV data.",
        "research_notes": "Parallel Bridgett, Soo, Sarah post-close roles batches 9-10.",
    },
    {
        "row": 212,
        "csv_index": 211,
        "first_name": "Mike",
        "last_name": "Beltz",
        "title": "Agent",
        "company": "Spencer Properties",
        "email": "mike@spencerprop.com",
        "website": "https://spencerprop.com",
        "linkedin": "http://www.linkedin.com/in/mike-beltz-0876911a4",
        "twitter": "https://twitter.com/spencerprops",
        "facebook": "https://facebook.com/spencerprop",
        "research_signal": "Agent at Spencer Properties Raleigh; firm site reviews cite Paula, Cori, and Andrea for buyer support and 90-day buy-sell wins.",
        "research_notes": "John and Jennifer owners same batch. Agent-level listing media.",
    },
    {
        "row": 213,
        "csv_index": 212,
        "first_name": "Matt",
        "last_name": "Grainger",
        "title": "Vice President - Sales",
        "company": "Lawyers Title Los Angeles",
        "email": "mattgrainger@ltic.com",
        "website": "https://ltic.com",
        "linkedin": "http://www.linkedin.com/in/matt-grainger-60953612",
        "twitter": "",
        "facebook": "",
        "research_signal": "VP sales at Lawyers Title Los Angeles Burbank on national ltic.com platform.",
        "research_notes": "Cheryl and Kris AE same office batch 10. Matt sets LA sales media standard.",
    },
    {
        "row": 214,
        "csv_index": 213,
        "first_name": "Kris",
        "last_name": "Cayton",
        "title": "Account Executive",
        "company": "Lawyers Title Los Angeles",
        "email": "kcayton@ltic.com",
        "website": "https://ltic.com",
        "linkedin": "http://www.linkedin.com/in/kris-cayton-92a45b127",
        "twitter": "",
        "facebook": "",
        "research_signal": "Account executive at Lawyers Title Los Angeles; Burbank office on ltic.com with title insurance and escrow services.",
        "research_notes": "AE referral growth. Matt VP separate angle.",
    },
    {
        "row": 215,
        "csv_index": 214,
        "first_name": "Michael",
        "last_name": "Gabriel",
        "title": "Agent",
        "company": "Spencer Properties",
        "email": "michael.gabriel@spencergifts.com",
        "website": "https://spencerprop.com",
        "linkedin": "http://www.linkedin.com/in/michael-gabriel-0876911a4",
        "twitter": "https://twitter.com/spencerprops",
        "facebook": "https://facebook.com/spencerprop",
        "research_signal": "Agent at Spencer Properties per CSV; email domain spencergifts.com but website and firm are spencerprop.com Raleigh brokerage.",
        "research_notes": "Use spencerprop.com for research. Likely CRM email mismatch. Do not reference Spencer Gifts retail.",
    },
    {
        "row": 216,
        "csv_index": 215,
        "first_name": "Lisa",
        "last_name": "Semans",
        "title": "Business Development Executive",
        "company": "Lawyers Advantage Title Group",
        "email": "lisa@cftitle.com",
        "website": "https://lawyersadvantage.com",
        "linkedin": "http://www.linkedin.com/in/lisa-semans-575a38156",
        "twitter": "https://twitter.com/LawyersAdv",
        "facebook": "https://facebook.com/LawyersAdvantage",
        "research_signal": "Licensed title agent at Central Florida Title Center per cftitle.com; 23 years as SunTrust mortgage loan officer before title, Seminole County since 2019.",
        "research_notes": "Website cftitle.com fetched May 2026. Altamonte Springs office April 2022. CSV company name Lawyers Advantage; public site is Central Florida Title Center.",
    },
    {
        "row": 217,
        "csv_index": 216,
        "first_name": "Jennifer",
        "last_name": "Spencer",
        "title": "Real Estate Broker/Owner",
        "company": "Spencer Properties",
        "email": "jennifer@spencerprop.com",
        "website": "https://spencerprop.com",
        "linkedin": "http://www.linkedin.com/in/jennifer-spencer-0876911a4",
        "twitter": "https://twitter.com/spencerprops",
        "facebook": "https://facebook.com/spencerprop",
        "research_signal": "Broker and owner at Spencer Properties Raleigh alongside John Spencer; firm promotes instant home valuation and video-forward listing marketing.",
        "research_notes": "Family-named brokerage. Ellie listing broker same batch.",
    },
    {
        "row": 218,
        "csv_index": 217,
        "first_name": "Melissa",
        "last_name": "Ostmann",
        "title": "Loan Arranger",
        "company": "Lawyers Title of Cincinnati",
        "email": "mostmann@ltcincy.com",
        "website": "https://ltcincy.com",
        "linkedin": "http://www.linkedin.com/in/melissa-ostmann-0876911a4",
        "twitter": "",
        "facebook": "",
        "research_signal": "Loan arranger at Lawyers Title of Cincinnati; independent agency since 1936 with highest residential closing volume in southwestern Ohio per ltcincy.com.",
        "research_notes": "Unique title Loan Arranger. Lender coordination and timeline video angle.",
    },
    {
        "row": 219,
        "csv_index": 218,
        "first_name": "Lisa",
        "last_name": "Fitzpatrick",
        "title": "Marketing Director",
        "company": "TitleQuest",
        "email": "lfitzpatrick@titlequest.net",
        "website": "https://titlequest.net",
        "linkedin": "http://www.linkedin.com/in/lisa-fitzpatrick-0876911a4",
        "twitter": "https://twitter.com/titlequestllc",
        "facebook": "https://facebook.com/TitleQuest",
        "research_signal": "Marketing director at TitleQuest; site cites ALTA compliance, 25+ years average experience, and exceptional service across VA and NC.",
        "research_notes": "Brian Clements owner batch 10. Angie Horton sales marketing batch 10. Lisa owns marketing director lane.",
    },
    {
        "row": 220,
        "csv_index": 219,
        "first_name": "Curtis",
        "last_name": "Takemoto",
        "title": "Title Officer/Settlement Agent",
        "company": "Vesta Settlements, LLC",
        "email": "ctakemoto@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/curtis-takemoto-0876911a4",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Title officer and settlement agent at Vesta; dual role spans examination and table-side closing for Northern Virginia files.",
        "research_notes": "Table trust and title exam education video angle.",
    },
    {
        "row": 221,
        "csv_index": 220,
        "first_name": "Arturo",
        "last_name": "Fuenzalida",
        "title": "Branch Manager",
        "company": "Lawyers Title Company Bay Area",
        "email": "art.fuenzalida@ltic.com",
        "website": "https://lawyerstitlebayarea.com",
        "linkedin": "http://www.linkedin.com/in/arturo-fuenzalida-791674104",
        "twitter": "",
        "facebook": "",
        "research_signal": "Branch manager at Lawyers Title Bay Area San Mateo; lawyerstitlebayarea.com Own Your Future with Agent ONE and TitlePro247 tools.",
        "research_notes": "Mai Tran escrow and Karen Anderson AVP ops batch 10. Arturo branch leadership.",
    },
    {
        "row": 222,
        "csv_index": 221,
        "first_name": "Alexandra",
        "last_name": "Keller",
        "title": "Business Development Associate",
        "company": "Vesta Settlements, LLC",
        "email": "akeller@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/alexandra-keller-2aa008125",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Business development associate at Vesta Settlements Baltimore market per LinkedIn location; firm Closings Elevated and eight-office footprint.",
        "research_notes": "Junior BD vs Melissa Fones owner VP BD batch 10.",
    },
    {
        "row": 223,
        "csv_index": 222,
        "first_name": "Ellie",
        "last_name": "Spencer",
        "title": "Real Estate Listing Broker",
        "company": "Spencer Properties",
        "email": "ellie@spencerprop.com",
        "website": "https://spencerprop.com",
        "linkedin": "http://www.linkedin.com/in/ellie-spencer-a1887217b",
        "twitter": "https://twitter.com/spencerprops",
        "facebook": "https://facebook.com/spencerprop",
        "research_signal": "Listing broker at Spencer Properties; site A Video Is Worth a Thousand Pictures section and tailored marketing strategy keywords in CSV.",
        "research_notes": "Spencer surname. John and Jennifer owners. Listing-focused reel angle.",
    },
    {
        "row": 224,
        "csv_index": 223,
        "first_name": "Summer",
        "last_name": "Allen",
        "title": "Software Administrator/Order Entry",
        "company": "CentraLand Title Company",
        "email": "sallen@centralandtitle.com",
        "website": "https://centralandtitle.com",
        "linkedin": "http://www.linkedin.com/in/summer-allen-08564579",
        "twitter": "",
        "facebook": "https://www.facebook.com/CentraLand/",
        "research_signal": "Software administrator and order entry at CentraLand Title Temple TX; centralandtitle.com promises surprise-free closings with 30+ years serving Central Texas.",
        "research_notes": "Website fetched May 2026. Founded Jerry Secrest era. Clients-first positioning.",
    },
    {
        "row": 225,
        "csv_index": 224,
        "first_name": "Stacey",
        "last_name": "Dennison",
        "title": "AVP/Escrow Officer",
        "company": "Lawyers Title",
        "email": "stacey.dennison@ltic.com",
        "website": "https://ltic.com",
        "linkedin": "http://www.linkedin.com/in/stacey-dennison-aa3428103",
        "twitter": "",
        "facebook": "https://facebook.com/Lawyers-Title-111713535507208/",
        "research_signal": "AVP and escrow officer at Lawyers Title Phoenix on national ltic.com with digital escrow and smooth closing keywords in CSV.",
        "research_notes": "National brand Jacksonville HQ in CSV. Tina branch manager same batch Phoenix.",
    },
    {
        "row": 226,
        "csv_index": 225,
        "first_name": "Tina",
        "last_name": "Rynhard",
        "title": "Branch Manager at Lawyers Title",
        "company": "Lawyers Title",
        "email": "tina.rynhard@ltic.com",
        "website": "https://ltic.com",
        "linkedin": "http://www.linkedin.com/in/tina-rynhard-52b1502b",
        "twitter": "",
        "facebook": "https://facebook.com/Lawyers-Title-111713535507208/",
        "research_signal": "Branch manager at Lawyers Title; Phoenix market per CSV with national ltic.com escrow and title insurance platform.",
        "research_notes": "Stacey Dennison AVP escrow same market. Branch manager training consistency angle.",
    },
    {
        "row": 227,
        "csv_index": 226,
        "first_name": "Samantha",
        "last_name": "McCoy",
        "title": "Escrow Officer",
        "company": "Texas Premier Title",
        "email": "smccoy@txprem.com",
        "website": "https://txprem.com",
        "linkedin": "http://www.linkedin.com/in/samantha-r-mccoy",
        "twitter": "",
        "facebook": "https://web.facebook.com/texaspremiertitle/",
        "research_signal": "Escrow officer at Texas Premier Title Dallas; CSV SEO cites secure transactions and Northwest Highway office, Facebook texaspremiertitle active.",
        "research_notes": "txprem.com landing page unavailable May 2026. Use CSV and LinkedIn. New firm for campaign.",
    },
]

COPY = {
    "jromero@vestasettlements.com": [
        [
            "Processor Vesta",
            "Hi Jenny,\n\nYou settlement processor at Vesta with eight offices and Closings, Elevated on vestasettlements.com.\n\nProcessors cut repeat calls when wire and timeline clips look identical desk to desk.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "YouTube realtor edu",
            "Hi Jenny,\n\nThe firm educates realtors on YouTube; processor-owned explainers should match that tone.\n\nWe engineer retention pacing on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Nihan batch 9",
            "Hi Jenny,\n\nNihan may have seen processor notes in batch 9; yours is Jenny-led file prep.\n\nOpen to a fraud-education outline?",
        ],
    ],
    "cyevoli@vestasettlements.com": [
        [
            "Contract manager Vesta",
            "Hi Christina,\n\nYou contract manager at Vesta with digital EMD delivery and contract execution in the firm keywords.\n\nContract managers win when timeline and amendment clips look precise before closers touch the file.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Hybrid e-closing",
            "Hi Christina,\n\nHybrid and e-closing options need contract-stage video that agents actually forward.\n\nWe batch shorts from screen recordings you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Lauren post close",
            "Hi Christina,\n\nLauren may get post-closer notes; yours is pre-close contract accuracy.\n\nWant a contract-timeline reel spec?",
        ],
    ],
    "john@spencerprop.com": [
        [
            "Owner broker Raleigh",
            "Hi John,\n\nYou owner and broker at Spencer Properties Raleigh, where spencerprop.com sells with Matterport tours and a strong sold portfolio.\n\nOwners set listing media standard for Mike, Ellie, and the roster.\n\nWe finish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Video worth thousand",
            "Hi John,\n\nYour site says a video is worth a thousand pictures; that should show in every listing hook.\n\nWe batch variants from one shoot day.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Jennifer owner separate",
            "Hi John,\n\nJennifer may get parallel owner notes; yours is John-led brokerage brand.\n\nOpen to an owner reel plan?",
        ],
    ],
    "ljin@vestasettlements.com": [
        [
            "Post closer Vesta",
            "Hi Lauren,\n\nYou post closer at Vesta with hybrid and e-closing in the firm keywords.\n\nPost-close specialists cut repeat calls when payoff explainers look clear on mobile.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Closings elevated",
            "Hi Lauren,\n\nClosings, Elevated should sound the same from your desk as every Vesta office.\n\nWe engineer shorts from narration you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Bridgett batch 10",
            "Hi Lauren,\n\nBridgett may have seen parallel post-close notes in batch 10; yours is Lauren-branded follow-through.\n\nWant a post-close kit outline?",
        ],
    ],
    "mike@spencerprop.com": [
        [
            "Agent Spencer Raleigh",
            "Hi Mike,\n\nYou agent at Spencer Properties where reviews praise Paula, Cori, and Andrea for buyer patience and 90-day buy-sell wins on spencerprop.com.\n\nAgents win when listing cuts match the Matterport and video-forward standard John sets.\n\nWe polish supplied tour footage.\n\nWorth a sample?",
        ],
        [
            "Raleigh neighborhoods",
            "Hi Mike,\n\nFirm neighborhood guides and buyer resources should become 45-second hooks from one master walkthrough.\n\nPost-production on footage you supply.\n\nCurious?",
        ],
        [
            "Ellie listing separate",
            "Hi Mike,\n\nEllie may get listing-broker notes; yours is buyer-agent story media.\n\nOpen to an agent reel spec?",
        ],
    ],
    "mattgrainger@ltic.com": [
        [
            "VP sales LA ltic",
            "Hi Matt,\n\nYou VP sales at Lawyers Title Los Angeles on ltic.com in Burbank.\n\nVPs scale when every AE sends the same partner and builder clip quality.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Cheryl Kris team",
            "Hi Matt,\n\nCheryl and Kris may get AE notes this batch; you can set one LA finishing template.\n\nWe standardize on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "National platform",
            "Hi Matt,\n\nNational ltic brand power only helps if local outreach looks as polished as the parent site.\n\nWant a VP sales enablement outline?",
        ],
    ],
    "kcayton@ltic.com": [
        [
            "AE Lawyers Title LA",
            "Hi Kris,\n\nYou account executive at Lawyers Title Los Angeles on ltic.com with title insurance and escrow for Burbank-area partners.\n\nAEs win when referral partners get short clips they actually forward.\n\nWe finish supplied partner footage.\n\nWorth a sample?",
        ],
        [
            "Builder lender mix",
            "Hi Kris,\n\nBuilder and lender audiences each need distinct 45-second cuts from one master interview.\n\nWe batch hooks on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Matt VP separate",
            "Hi Kris,\n\nMatt may get VP sales notes; yours is Kris-branded AE growth.\n\nOpen to a partner lunch reel plan?",
        ],
    ],
    "michael.gabriel@spencergifts.com": [
        [
            "Agent Spencer Properties",
            "Hi Michael,\n\nYou agent at Spencer Properties Raleigh on spencerprop.com with Matterport tours and video-forward listing marketing.\n\nYour CRM may use a different email domain; the brokerage story is still Triangle inventory and client reviews on the site.\n\nWe finish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Buyer resources site",
            "Hi Michael,\n\nFirm buyer guides and instant valuation tools should become shorts that read credible on mobile.\n\nWe batch hooks from one showing you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Mike agent separate",
            "Hi Michael,\n\nMike Beltz may get parallel agent notes; yours is Michael-branded listing media.\n\nWant a tour reel spec?",
        ],
    ],
    "lisa@cftitle.com": [
        [
            "SunTrust 23 years",
            "Hi Lisa,\n\nYour cftitle.com bio says you were a SunTrust mortgage loan officer 23 years before becoming licensed title agent at Central Florida Title Center in Altamonte Springs.\n\nThat lender fluency fits agent-forward explainers on timing and wire safety.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Seminole County roots",
            "Hi Lisa,\n\nRaised in Seminole County 50+ years; local trust should show in short educational cuts, not PDFs alone.\n\nWe engineer captions and grade on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Lawyers Advantage path",
            "Hi Lisa,\n\nYou grew through Lawyers Advantage into agency license in 2019; BD video should match that credibility arc.\n\nOpen to a Florida agent education outline?",
        ],
    ],
    "jennifer@spencerprop.com": [
        [
            "Broker owner Spencer",
            "Hi Jennifer,\n\nYou broker and owner at Spencer Properties Raleigh with John Spencer and a site built on Matterport, sold stories, and instant valuations.\n\nOwners scale when every listing broker ships the same quality hero cut.\n\nWe finish supplied property footage.\n\nWorth a sample?",
        ],
        [
            "Ellie listing team",
            "Hi Jennifer,\n\nEllie may get listing-broker notes; you set firm-wide creative standard for the Spencer team.\n\nWe batch hook variants from one shoot.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Emma buyer batch 10",
            "Hi Jennifer,\n\nEmma may have seen buyer-specialist notes in batch 10; yours is owner-led brand performance.\n\nWant a brokerage reel plan?",
        ],
    ],
    "mostmann@ltcincy.com": [
        [
            "Loan arranger Cincinnati",
            "Hi Melissa,\n\nYou loan arranger at Lawyers Title of Cincinnati, largest independent residential closer in southwestern Ohio since 1936 on ltcincy.com.\n\nLender-facing timelines should look as clear on video as your file coordination.\n\nWe finish supplied explainers.\n\nWorth a sample?",
        ],
        [
            "Lender agent bridge",
            "Hi Melissa,\n\nLoan arranger is the bridge role; 45-second cuts help agents understand funding milestones before the table.\n\nWe engineer from screen recordings you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Mike VP separate",
            "Hi Melissa,\n\nMike Fletcher may have seen VP notes in batch 9; yours is lender coordination media.\n\nOpen to a loan-timeline outline?",
        ],
    ],
    "lfitzpatrick@titlequest.net": [
        [
            "Marketing director TQ",
            "Hi Lisa,\n\nYou marketing director at TitleQuest where titlequest.net cites ALTA compliance, 25+ years average experience, and exceptional service in VA and NC.\n\nMarketing directors feel it when every closer sends a different quality campaign clip.\n\nWe standardize finishing on supplied event footage.\n\nWorth a sample?",
        ],
        [
            "titlequestllc social",
            "Hi Lisa,\n\nFirm Twitter titlequestllc and Facebook should match campaign cuts, not one-off phone video.\n\nWe batch hooks from one master you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Brian owner separate",
            "Hi Lisa,\n\nBrian may get owner notes from batch 10; yours is director-level brand campaigns.\n\nWant a TitleQuest marketing kit outline?",
        ],
    ],
    "ctakemoto@vestasettlements.com": [
        [
            "Title officer Vesta",
            "Hi Curtis,\n\nYou title officer and settlement agent at Vesta, spanning exam and table-side closing in Northern Virginia.\n\nDual roles win when exam findings and table trust share one visual template.\n\nWe finish supplied consumer explainers.\n\nWorth a sample?",
        ],
        [
            "Table plus exam",
            "Hi Curtis,\n\nAgents need short cuts that explain both clear title and calm closing-room presence.\n\nWe handle grade and captions on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Laura settlement separate",
            "Hi Curtis,\n\nLaura may get settlement-agent notes; yours combines title officer precision.\n\nOpen to a dual-role explainer outline?",
        ],
    ],
    "art.fuenzalida@ltic.com": [
        [
            "Branch mgr Bay Area",
            "Hi Arturo,\n\nYou branch manager at Lawyers Title Bay Area where lawyerstitlebayarea.com leads with Own Your Future plus Agent ONE and TitlePro247 farms.\n\nBranch managers scale when every escrow desk sends the same agent-education quality.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "San Mateo leadership",
            "Hi Arturo,\n\nMai may get escrow notes; you set San Mateo branch media standard.\n\nWe standardize on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Karen AVP batch 10",
            "Hi Arturo,\n\nKaren Anderson may have seen AVP ops notes in batch 10; yours is branch leadership.\n\nWant a Bay Area enablement reel plan?",
        ],
    ],
    "akeller@vestasettlements.com": [
        [
            "BD associate Vesta",
            "Hi Alexandra,\n\nYou business development associate at Vesta with Closings, Elevated and an eight-office footprint across VA and MD.\n\nBD associates win when partner outreach video looks as sharp as Melissa Fones sets at owner level.\n\nWe finish supplied event footage.\n\nWorth a sample?",
        ],
        [
            "Baltimore market",
            "Hi Alexandra,\n\nYour LinkedIn market is Baltimore; shorts should read local while matching firm-wide templates.\n\nWe batch hooks from one master you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Melissa owner separate",
            "Hi Alexandra,\n\nMelissa may get owner VP BD notes; yours is associate-led partner development.\n\nOpen to a BD spotlight outline?",
        ],
    ],
    "ellie@spencerprop.com": [
        [
            "Listing broker Spencer",
            "Hi Ellie,\n\nYou listing broker at Spencer Properties; spencerprop.com leans on video, sold portfolio stories, and tailored marketing per CSV keywords.\n\nListing brokers win when hero cuts match the Matterport standard in the first two seconds.\n\nWe polish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Marketing strategy",
            "Hi Ellie,\n\nTailored marketing strategy should not mean one-off phone edits per listing.\n\nWe batch hook variants from one shoot you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Jennifer owner separate",
            "Hi Ellie,\n\nJennifer and John may get owner notes; yours is Ellie-branded listing media.\n\nWant a luxury listing reel spec?",
        ],
    ],
    "sallen@centralandtitle.com": [
        [
            "Order entry CentraLand",
            "Hi Summer,\n\nYou software administrator and order entry at CentraLand Title in Temple; centralandtitle.com promises surprise-free closings with 30+ years in Central Texas.\n\nOrder entry owns the first digital impression agents and lenders see.\n\nWe finish supplied training and screen recordings.\n\nWorth a sample?",
        ],
        [
            "Clients first 2023",
            "Hi Summer,\n\nThe site leads with clients-first positioning; internal and external clips should match that promise.\n\nWe engineer shorts from narration you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Temple area focus",
            "Hi Summer,\n\nCentral Texas market knowledge on the site fits localized explainer cuts for realtor partners.\n\nOpen to an order-entry education outline?",
        ],
    ],
    "stacey.dennison@ltic.com": [
        [
            "AVP escrow ltic",
            "Hi Stacey,\n\nYou AVP and escrow officer at Lawyers Title on ltic.com with digital escrow and smooth closing in the CSV keywords.\n\nAVPs scale when Phoenix desks send the same wire-safety and timeline quality.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Phoenix table trust",
            "Hi Stacey,\n\nEscrow officers need clips agents forward before funding instructions go out.\n\nWe engineer from screen recordings you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Tina branch separate",
            "Hi Stacey,\n\nTina may get branch-manager notes; yours is AVP escrow leadership.\n\nWant a wire-instruction reel spec?",
        ],
    ],
    "tina.rynhard@ltic.com": [
        [
            "Branch manager ltic",
            "Hi Tina,\n\nYou branch manager at Lawyers Title in Phoenix on the national ltic.com platform.\n\nBranch managers win when every escrow and sales desk uses the same training video template.\n\nWe finish supplied partner footage.\n\nWorth a sample?",
        ],
        [
            "Digital escrow scale",
            "Hi Tina,\n\nDigital escrow only works if clips are formatted and paced consistently branch-wide.\n\nWe standardize finishing on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Stacey AVP separate",
            "Hi Tina,\n\nStacey may get AVP escrow notes; yours is branch operations and growth.\n\nOpen to a branch onboarding reel plan?",
        ],
    ],
    "smccoy@txprem.com": [
        [
            "Escrow Dallas txprem",
            "Hi Samantha,\n\nYou escrow officer at Texas Premier Title in Dallas; CSV cites secure transactions and the Northwest Highway office with active Facebook texaspremiertitle.\n\nEscrow officers need wire-safety clips agents actually forward.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Site unavailable note",
            "Hi Samantha,\n\nPublic site was unavailable when checked; your LinkedIn and firm social still support credible table-side trust video for Texas partners.\n\nWe engineer from screen recordings you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "New firm campaign",
            "Hi Samantha,\n\nFirst txprem contact in this pilot; we can align a Texas-specific template as you scale partner outreach.\n\nWant an escrow-led fraud clip outline?",
        ],
    ],
}


def main():
    fails = []
    for email, seq in COPY.items():
        for i, (subj, body) in enumerate(seq, 1):
            issues = qa(subj, body)
            if issues:
                fails.append((email, i, issues, wc(body), len(subj)))

    if fails:
        print("QA FAILURES:")
        for f in fails:
            print(f)
        raise SystemExit(1)

    (ROOT / "campaigns" / "pilot-20-batch11-research.json").write_text(
        json.dumps(RESEARCH, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "campaigns" / "pilot-20-batch11-copy.json").write_text(
        json.dumps(COPY, indent=2) + "\n", encoding="utf-8"
    )
    print("OK: 60/60 QA passed in draft")


if __name__ == "__main__":
    main()
