#!/usr/bin/env python3
"""Draft batch 9 research + copy JSON with inline QA."""
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
        "row": 168,
        "csv_index": 167,
        "first_name": "James",
        "last_name": "Augustine",
        "title": "Compliance and Risk",
        "company": "Silva Law / QuickSilva Title LLC",
        "email": "jim@myquicksilva.com",
        "website": "https://quicksilvatitle.com",
        "linkedin": "http://www.linkedin.com/in/james-augustine-a421215",
        "twitter": "https://twitter.com/myquicksilva",
        "facebook": "https://facebook.com/myQuicksilva",
        "research_signal": "Compliance and risk at Silva Law and QuickSilva Title Bedford MA; CSV cites 24/7 availability, instant fee quotes, and title insurance plus real estate law.",
        "research_notes": "quicksilvatitle.com unavailable May 2026. Ted Silva owner batch 6. Twitter myquicksilva. Compliance angle: wire-fraud and policy video consistency.",
    },
    {
        "row": 169,
        "csv_index": 168,
        "first_name": "Madeline",
        "last_name": "West",
        "title": "Closing Table Representative",
        "company": "TitleQuest",
        "email": "mwest@titlequest.net",
        "website": "https://titlequest.net",
        "linkedin": "http://www.linkedin.com/in/madeline-west-09956a92",
        "twitter": "https://twitter.com/titlequestllc",
        "facebook": "https://facebook.com/TitleQuest",
        "research_signal": "Closing table representative at TitleQuest VA/NC; site cites ALTA compliance, 25+ years average team experience, and mission of exceptional service since 24+ years in market.",
        "research_notes": "Website fetched May 2026. Chesapeake VA. Affiliates TitleCom and Quest Insurance.",
    },
    {
        "row": 170,
        "csv_index": 169,
        "first_name": "Leselie",
        "last_name": "Straub",
        "title": "Title Resolution/Post Closing Specialist",
        "company": "Lawyers Title of Cincinnati",
        "email": "lstraub@ltcincy.com",
        "website": "https://ltcincy.com",
        "linkedin": "http://www.linkedin.com/in/leselie-l-straub-b46257a",
        "twitter": "",
        "facebook": "",
        "research_signal": "Post-closing specialist at Lawyers Title of Cincinnati; ltcincy.com says largest independent title agency in southwestern Ohio since 1936 with more residential closings than peers.",
        "research_notes": "Website fetched May 2026. Seven ltcincy contacts this batch. Fidelity, First American, Stewart partnerships.",
    },
    {
        "row": 171,
        "csv_index": 170,
        "first_name": "Andrea",
        "last_name": "Turner",
        "title": "Branch Manager",
        "company": "Vesta Settlements, LLC",
        "email": "aturner@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/andrea-turner-909409283",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Branch manager at Vesta Settlements; site lists eight VA and MD offices and Closings, Elevated positioning with realtor education on YouTube.",
        "research_notes": "Website fetched May 2026. Ashburn, Winchester, Tysons, Chantilly, Richmond, Alexandria, Fredericksburg, Bethesda.",
    },
    {
        "row": 172,
        "csv_index": 171,
        "first_name": "Troy",
        "last_name": "Davis",
        "title": "Broker / Owner",
        "company": "The Agency Realty",
        "email": "tdavis@theagencyrealty.com",
        "website": "https://theagencyrealty.com",
        "linkedin": "http://www.linkedin.com/in/troy-davis-rcs-d-sres-32830328",
        "twitter": "",
        "facebook": "",
        "research_signal": "Broker owner at The Agency Realty Newport Beach; personal site shows $7.35M Corona del Mar sale, construction background since 1986 license, and first-home buyer testimonials.",
        "research_notes": "Website fetched May 2026. theagencyrealty.com routes to Troy Davis agent page. 34+ years per client quotes.",
    },
    {
        "row": 173,
        "csv_index": 172,
        "first_name": "Tatum",
        "last_name": "Vanderpool",
        "title": "Escrow Officer",
        "company": "Lawyers Title DFW",
        "email": "tatum.vanderpool@ltic.com",
        "website": "https://ltic.com",
        "linkedin": "http://www.linkedin.com/in/tatum-vanderpool-925b16191",
        "twitter": "",
        "facebook": "",
        "research_signal": "Escrow officer at Lawyers Title DFW Addison; national ltic.com parent with builder, lender, and commercial title keywords in CSV.",
        "research_notes": "Melody Coleman SD and batch 5 AZ contacts used ltic.com. Tatum is DFW escrow table angle.",
    },
    {
        "row": 174,
        "csv_index": 173,
        "first_name": "Sarah",
        "last_name": "McKeone",
        "title": "Post Closer | Owner",
        "company": "Vesta Settlements, LLC",
        "email": "smckeone@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/sarah-mckeone-509a721a",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Post closer and owner at Vesta Settlements Leesburg VA; firm markets e-closings, remote online notarization, and not just another file number.",
        "research_notes": "Dual owner and post-closer title in CSV. Andrea branch manager same firm batch.",
    },
    {
        "row": 175,
        "csv_index": 174,
        "first_name": "Sandy",
        "last_name": "Holton",
        "title": "Accounting Bookkeeper",
        "company": "Lawyers Title of Cincinnati",
        "email": "sholton@ltcincy.com",
        "website": "https://ltcincy.com",
        "linkedin": "http://www.linkedin.com/in/sandy-holton-bb86694a",
        "twitter": "",
        "facebook": "",
        "research_signal": "Accounting bookkeeper at Lawyers Title of Cincinnati; independent agency handling highest residential closing volume in southwestern Ohio per site.",
        "research_notes": "Finance and ops angle for internal training video matching agent-facing clips.",
    },
    {
        "row": 176,
        "csv_index": 175,
        "first_name": "Nihan",
        "last_name": "Seeley",
        "title": "Settlement Processor",
        "company": "Vesta Settlements, LLC",
        "email": "nseeley@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/nihan-seeley-0363707a",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Settlement processor at Vesta Settlements; CSV keywords include digital EMD delivery, hybrid closing, and proactive customer service.",
        "research_notes": "Processor file-prep and wire-education angle. Sixth Vesta contact this batch.",
    },
    {
        "row": 177,
        "csv_index": 176,
        "first_name": "Suzanne",
        "last_name": "Kluck",
        "title": "Title Specialist",
        "company": "Lawyers Title of Cincinnati",
        "email": "skluck@ltcincy.com",
        "website": "https://ltcincy.com",
        "linkedin": "http://www.linkedin.com/in/suzanne-kluck-049893306",
        "twitter": "",
        "facebook": "",
        "research_signal": "Title specialist at Lawyers Title of Cincinnati with educational blog and buyer or seller checklists on ltcincy.com.",
        "research_notes": "Title specialist fits consumer explainer and agent checklist video.",
    },
    {
        "row": 178,
        "csv_index": 177,
        "first_name": "Mike",
        "last_name": "Fletcher",
        "title": "Vice President at Lawyers Title",
        "company": "Lawyers Title of Cincinnati",
        "email": "mfletcher@ltcincy.com",
        "website": "https://ltcincy.com",
        "linkedin": "http://www.linkedin.com/in/mike-fletcher-0876911a4",
        "twitter": "",
        "facebook": "",
        "research_signal": "Vice president at Lawyers Title of Cincinnati; site cites 75+ years since 1936 and national Fidelity, First American, and Stewart relationships.",
        "research_notes": "VP sets firm-wide partner media standard. Seven Cincinnati colleagues this batch.",
    },
    {
        "row": 179,
        "csv_index": 178,
        "first_name": "Stacey",
        "last_name": "Pope",
        "title": "Title Agent",
        "company": "Vesta Settlements, LLC",
        "email": "spope@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/stacey-pope-0876911a4",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Title agent at Vesta Settlements Northern Virginia; firm YouTube channel covers sales contracts, title insurance, and military relocation topics.",
        "research_notes": "Title agent consumer-trust at closing table. Realtor education content on site.",
    },
    {
        "row": 180,
        "csv_index": 179,
        "first_name": "Tamera",
        "last_name": "Gaede",
        "title": "Host",
        "company": "Lawyers Title DFW",
        "email": "tamera.gaede@ltic.com",
        "website": "https://ltic.com",
        "linkedin": "http://www.linkedin.com/in/tamera-gaede-0876911a4",
        "twitter": "",
        "facebook": "",
        "research_signal": "Host role at Lawyers Title DFW per CSV; Addison office on national ltic.com with agent and builder services keywords.",
        "research_notes": "Host title suggests events or education series; pair with Tatum escrow DFW contact. No dedicated DFW microsite in CSV.",
    },
    {
        "row": 181,
        "csv_index": 180,
        "first_name": "Sonia",
        "last_name": "Downard",
        "title": "Real Estate/Title Attorney",
        "company": "Vesta Settlements, LLC",
        "email": "sdownard@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/sonia-downard-0876911a4",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Real estate and title attorney at Vesta Settlements; firm emphasizes real estate law expertise and secure document delivery in CSV.",
        "research_notes": "Attorney-led credibility for lender and agent education. Distinct from processors.",
    },
    {
        "row": 182,
        "csv_index": 181,
        "first_name": "Michele",
        "last_name": "Bunzel",
        "title": "Typist",
        "company": "Lawyers Title of Cincinnati",
        "email": "mbunzel@ltcincy.com",
        "website": "https://ltcincy.com",
        "linkedin": "http://www.linkedin.com/in/michele-bunzel-0876911a4",
        "twitter": "",
        "facebook": "",
        "research_signal": "Typist at Lawyers Title of Cincinnati; high-volume independent shop where document accuracy and consistent client updates matter.",
        "research_notes": "Production role; video reduces repeat calls on timeline and wire questions. Differentiate from closers.",
    },
    {
        "row": 183,
        "csv_index": 182,
        "first_name": "Soo",
        "last_name": "Choi",
        "title": "Post Closing Specialist",
        "company": "Vesta Settlements, LLC",
        "email": "schoi@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/soo-choi-0876911a4",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Post-closing specialist at Vesta alongside Sarah McKeone owner post closer; firm lists eight offices and hybrid or full e-closing options.",
        "research_notes": "Leselie Straub post closing at ltcincy is parallel role different company.",
    },
    {
        "row": 184,
        "csv_index": 183,
        "first_name": "Robyn",
        "last_name": "Griffin",
        "title": "Closing Assistant at Lawyers Title",
        "company": "Lawyers Title of Cincinnati",
        "email": "rgriffin@ltcincy.com",
        "website": "https://ltcincy.com",
        "linkedin": "http://www.linkedin.com/in/robyn-griffin-0876911a4",
        "twitter": "",
        "facebook": "",
        "research_signal": "Closing assistant at Lawyers Title of Cincinnati; site promises personalized attention and seamless transaction process for every client.",
        "research_notes": "Assistant supports closers; pre-close education video angle.",
    },
    {
        "row": 185,
        "csv_index": 184,
        "first_name": "Karen",
        "last_name": "Anderson",
        "title": "AVP Branch Operations",
        "company": "Lawyers Title Company Bay Area",
        "email": "karen.anderson@ltic.com",
        "website": "https://lawyerstitlebayarea.com",
        "linkedin": "http://www.linkedin.com/in/karen-anderson-0876911a4",
        "twitter": "",
        "facebook": "",
        "research_signal": "AVP branch operations at Lawyers Title Bay Area; lawyerstitlebayarea.com leads with Own Your Future and Agent ONE net sheets plus TitlePro247 farms.",
        "research_notes": "Website fetched May 2026. Melody Coleman SD batch 7 same ltic parent different branch.",
    },
    {
        "row": 186,
        "csv_index": 185,
        "first_name": "Kat",
        "last_name": "Contreras",
        "title": "Sales Marketing Executive",
        "company": "TitleQuest",
        "email": "kcontreras@titlequest.net",
        "website": "https://titlequest.net",
        "linkedin": "http://www.linkedin.com/in/kat-contreras-0876911a4",
        "twitter": "https://twitter.com/titlequestllc",
        "facebook": "https://facebook.com/TitleQuest",
        "research_signal": "Sales marketing executive at TitleQuest; site mission is building lasting relationships through exceptional service with realtor and lender resources.",
        "research_notes": "Madeline closing table and Justin IT same firm. Marketing owns growth campaigns.",
    },
    {
        "row": 187,
        "csv_index": 186,
        "first_name": "Justin",
        "last_name": "Cutler",
        "title": "IT Administrator",
        "company": "TitleQuest",
        "email": "jcutler@titlequest.net",
        "website": "https://titlequest.net",
        "linkedin": "http://www.linkedin.com/in/justin-cutler-0876911a4",
        "twitter": "https://twitter.com/titlequestllc",
        "facebook": "https://facebook.com/TitleQuest",
        "research_signal": "IT administrator at TitleQuest; firm offers e-recording, virtual closing options, and ALTA compliance per site and CSV.",
        "research_notes": "IT enables consistent delivery of training and closing video assets. Third TitleQuest contact.",
    },
]

COPY = {
    "jim@myquicksilva.com": [
        [
            "Compliance QuickSilva",
            "Hi James,\n\nYou handle compliance and risk at Silva Law and QuickSilva Title in Bedford, where CSV cites 24/7 availability and instant fee quotes alongside title and real estate law.\n\nCompliance leaders scale when every closer sends the same wire-fraud and policy clip.\n\nWe standardize finishing on supplied training footage.\n\nWorth a sample?",
        ],
        [
            "myquicksilva Twitter",
            "Hi James,\n\nFirm Twitter myquicksilva and Facebook myQuicksilva should match the tone of your risk messaging.\n\nWe engineer shorts from screen recordings you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Ted owner separate",
            "Hi James,\n\nTed Silva may have seen owner notes in batch 6; yours is compliance-led enablement.\n\nOpen to a fraud-education reel outline?",
        ],
    ],
    "mwest@titlequest.net": [
        [
            "Closing table TitleQuest",
            "Hi Madeline,\n\nYou closing table representative at TitleQuest, where titlequest.net cites ALTA compliance, 25+ years average team experience, and exceptional service across VA and NC.\n\nClosers are the face of trust at the table.\n\nWe finish supplied consumer explainers with captions and grade.\n\nWorth a sample?",
        ],
        [
            "titlequestllc Twitter",
            "Hi Madeline,\n\nFirm Twitter titlequestllc and Facebook TitleQuest should match your closing-room presence.\n\nWe batch hooks from narration you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Kat Justin separate",
            "Hi Madeline,\n\nKat and Justin may get marketing and IT notes; yours is table-side trust.\n\nWant a buyer-guide video outline?",
        ],
    ],
    "lstraub@ltcincy.com": [
        [
            "Post closing Cincinnati",
            "Hi Leselie,\n\nYou post-closing specialist at Lawyers Title of Cincinnati, largest independent title agency in southwestern Ohio since 1936 on ltcincy.com.\n\nPost-closing wins when payoff and title-curative explainers look clear on mobile.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Independent volume leader",
            "Hi Leselie,\n\nThe site says you handle more residential closings than any other independent agency in the region.\n\nShort resolution clips reduce repeat agent calls.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Mike VP separate",
            "Hi Leselie,\n\nMike may get VP notes; yours is post-close file resolution.\n\nOpen to a curative-title explainer outline?",
        ],
    ],
    "aturner@vestasettlements.com": [
        [
            "Branch manager Vesta",
            "Hi Andrea,\n\nYou branch manager at Vesta Settlements with eight VA and MD offices and Closings, Elevated on vestasettlements.com.\n\nBranch leaders scale when every desk sends the same realtor-education quality.\n\nWe finish supplied training and event footage.\n\nWorth a sample?",
        ],
        [
            "YouTube realtor education",
            "Hi Andrea,\n\nYour site points agents to a YouTube channel on contracts, title insurance, and military relocation.\n\nThose topics deserve retention-grade cuts from supplied webinars.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Sarah owner separate",
            "Hi Andrea,\n\nSarah may get owner post-closer notes; yours is branch operations and growth.\n\nWant a branch onboarding reel plan?",
        ],
    ],
    "tdavis@theagencyrealty.com": [
        [
            "$7.35M Corona del Mar",
            "Hi Troy,\n\nYour site highlights a $7.35M Corona del Mar sale plus decades in Newport Beach since your 1986 license, with construction roots from Michigan State summers.\n\nLuxury inventory wins when video matches that price point in the first two seconds.\n\nWe finish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "First-home testimonial",
            "Hi Troy,\n\nA client review says you helped first-time buyers beat competing offers in a brutal market with 34 years of process knowledge.\n\nWe batch hook variants from one shoot day.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Broker owner standard",
            "Hi Troy,\n\nAs broker owner you set media bar for The Agency Realty roster.\n\nOpen to an owner-led listing reel outline?",
        ],
    ],
    "tatum.vanderpool@ltic.com": [
        [
            "Escrow officer DFW",
            "Hi Tatum,\n\nYou escrow officer at Lawyers Title DFW in Addison on the national ltic.com platform with builder and lender services in the firm keywords.\n\nEscrow officers need wire-safety clips agents actually forward.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Table-side trust",
            "Hi Tatum,\n\nDFW volume breaks down when one desk sends a different quality explainer.\n\nWe engineer from screen recordings you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Tamera host separate",
            "Hi Tatum,\n\nTamera may get host notes; yours is escrow-led consumer trust.\n\nWant a wire-instruction reel spec?",
        ],
    ],
    "smckeone@vestasettlements.com": [
        [
            "Owner post closer Vesta",
            "Hi Sarah,\n\nYou post closer and owner at Vesta Settlements, marketed as not just another file number with e-closing and RON in the keywords.\n\nOwners set firm-wide post-close and partner media standard.\n\nWe finish supplied client and agent footage.\n\nWorth a sample?",
        ],
        [
            "Eight-office scale",
            "Hi Sarah,\n\nEight offices across VA and MD need identical post-close education, not one-off PDFs.\n\nWe standardize finishing on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Andrea branch separate",
            "Hi Sarah,\n\nAndrea may get branch-manager notes; yours is owner-led post-close excellence.\n\nOpen to a post-closing series outline?",
        ],
    ],
    "sholton@ltcincy.com": [
        [
            "Bookkeeper ltcincy",
            "Hi Sandy,\n\nYou accounting bookkeeper at Lawyers Title of Cincinnati, the region's highest-volume independent residential closer per ltcincy.com.\n\nFinance and ops win when internal training video matches agent-facing clips.\n\nWe finish supplied webinar footage.\n\nWorth a sample?",
        ],
        [
            "1936 independent shop",
            "Hi Sandy,\n\n75+ years since 1936 is a trust story; back-office clarity should show in partner communications too.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Mike VP separate",
            "Hi Sandy,\n\nMike may get VP notes; yours is accounting and ops enablement.\n\nWant an internal training reel outline?",
        ],
    ],
    "nseeley@vestasettlements.com": [
        [
            "Settlement processor Vesta",
            "Hi Nihan,\n\nYou settlement processor at Vesta with digital EMD delivery and hybrid closing in the firm keywords.\n\nProcessors cut repeat calls when timeline clips look credible on mobile.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Closings elevated",
            "Hi Nihan,\n\nClosings, Elevated should sound the same in every processor desk video.\n\nWe engineer retention pacing on footage you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Sonia attorney separate",
            "Hi Nihan,\n\nSonia may get attorney notes; yours is file-prep throughput.\n\nOpen to a processor-led fraud clip outline?",
        ],
    ],
    "skluck@ltcincy.com": [
        [
            "Title specialist Cincinnati",
            "Hi Suzanne,\n\nYou title specialist at Lawyers Title of Cincinnati with educational blog and buyer or seller resources on ltcincy.com.\n\nSpecialists win when checklist topics become 45-second agent-forwardable cuts.\n\nWe finish supplied explainers.\n\nWorth a sample?",
        ],
        [
            "Largest independent OH",
            "Hi Suzanne,\n\nSouthwestern Ohio's largest independent shop should sound consistent in every title-review clip.\n\nPost-production on footage you supply.\n\nCurious?",
        ],
        [
            "Leselie post close",
            "Hi Suzanne,\n\nLeselie may get post-closing notes; yours is active-file title specialist work.\n\nWant a checklist-to-video outline?",
        ],
    ],
    "mfletcher@ltcincy.com": [
        [
            "VP Lawyers Title Cincy",
            "Hi Mike,\n\nYou vice president at Lawyers Title of Cincinnati, independent since 1936 with Fidelity, First American, and Stewart relationships on ltcincy.com.\n\nVPs scale when every Cincinnati desk sends the same partner clip quality.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Seven colleagues batch",
            "Hi Mike,\n\nSeven colleagues may see role-specific notes this batch; you can set one firm-wide finishing template.\n\nWe standardize on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Residential volume lead",
            "Hi Mike,\n\nMore residential closings than any other independent agency in the region is a story agents should see on video.\n\nOpen to a VP partner reel plan?",
        ],
    ],
    "spope@vestasettlements.com": [
        [
            "Title agent Vesta",
            "Hi Stacey,\n\nYou title agent at Vesta; vestasettlements.com educates realtors on YouTube about contracts, title insurance, and military relocation.\n\nTitle agents carry consumer trust before the notary moment.\n\nWe finish supplied explainers with captions and grade.\n\nWorth a sample?",
        ],
        [
            "Not a file number",
            "Hi Stacey,\n\nThe firm says you are not just another file number; video should prove that before the file opens.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Sonia legal separate",
            "Hi Stacey,\n\nSonia may get attorney notes; yours is title-agent consumer education.\n\nWant a military relocation short outline?",
        ],
    ],
    "tamera.gaede@ltic.com": [
        [
            "Host Lawyers Title DFW",
            "Hi Tamera,\n\nYou host at Lawyers Title DFW Addison on ltic.com with builder, lender, and commercial keywords in the CSV.\n\nHosts win when event and education footage becomes agent-forwardable cuts, not raw livestream.\n\nWe finish supplied recordings with grade and pacing.\n\nWorth a sample?",
        ],
        [
            "DFW agent education",
            "Hi Tamera,\n\nDFW agents judge partners on how clear pre-close video is, not slide decks alone.\n\nWe batch shorts from one master you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Tatum escrow separate",
            "Hi Tamera,\n\nTatum may get escrow notes; yours is hosted education and events.\n\nOpen to a DFW agent series outline?",
        ],
    ],
    "sdownard@vestasettlements.com": [
        [
            "Title attorney Vesta",
            "Hi Sonia,\n\nYou real estate and title attorney at Vesta Settlements with law expertise and secure document delivery in the firm keywords.\n\nAttorney-led explainers should sound as calm as your desk-side advice.\n\nWe finish supplied client and lender footage.\n\nWorth a sample?",
        ],
        [
            "RON hybrid closings",
            "Hi Sonia,\n\nHybrid and full e-closing options need legal-precision companion cuts for agents.\n\nWe engineer from narration you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Processor separate",
            "Hi Sonia,\n\nNihan and Soo may get processor notes; yours is counsel-led credibility.\n\nWant an attorney explainer outline?",
        ],
    ],
    "mbunzel@ltcincy.com": [
        [
            "Typist ltcincy volume",
            "Hi Michele,\n\nYou typist at Lawyers Title of Cincinnati, the highest-volume independent residential shop in southwestern Ohio.\n\nProduction teams reduce chaos when timeline and wire clips are identical branch to branch.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Seamless process promise",
            "Hi Michele,\n\nltcincy.com promises seamless transactions; your desk work should match that in agent-facing video.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Robyn assistant separate",
            "Hi Michele,\n\nRobyn may get closing-assistant notes; yours is document-production consistency.\n\nOpen to a typist-led timeline outline?",
        ],
    ],
    "schoi@vestasettlements.com": [
        [
            "Post closing Vesta",
            "Hi Soo,\n\nYou post-closing specialist at Vesta alongside eight offices and hybrid closing options on vestasettlements.com.\n\nPost-close specialists cut repeat calls when payoff explainers look clear on mobile.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Sarah owner parallel",
            "Hi Soo,\n\nSarah McKeone is owner post closer; yours is specialist-led follow-through after keys.\n\nWe engineer shorts from narration you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Leselie ltcincy separate",
            "Hi Soo,\n\nLeselie at Lawyers Title Cincinnati may get parallel post-close notes; yours is Vesta-specific.\n\nWant a post-close education kit?",
        ],
    ],
    "rgriffin@ltcincy.com": [
        [
            "Closing assistant Cincy",
            "Hi Robyn,\n\nYou closing assistant at Lawyers Title of Cincinnati where the site promises personalized attention and a seamless process.\n\nAssistants reduce table confusion when pre-close video matches closer tone.\n\nWe finish supplied explainers.\n\nWorth a sample?",
        ],
        [
            "Buyer seller checklists",
            "Hi Robyn,\n\nChecklists on ltcincy.com fit 45-second cuts buyers and agents actually watch.\n\nPost-production on footage you supply.\n\nUseful?",
        ],
        [
            "Mike VP separate",
            "Hi Robyn,\n\nMike may get VP notes; yours is assistant-led buyer preparation.\n\nOpen to a pre-close explainer outline?",
        ],
    ],
    "karen.anderson@ltic.com": [
        [
            "AVP Bay Area ops",
            "Hi Karen,\n\nYou AVP branch operations at Lawyers Title Bay Area where lawyerstitlebayarea.com leads with Own Your Future plus Agent ONE net sheets and TitlePro247 farms.\n\nOps leaders scale when every branch sends the same agent-education quality.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "TitlePro247 farms",
            "Hi Karen,\n\nFarm packs are complex; 45-second explainers help reps forward your brand, not a PDF alone.\n\nWe engineer from screen recordings you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Melody SD separate",
            "Hi Karen,\n\nMelody Coleman may have seen San Diego ltic notes in batch 7; yours is Bay Area branch ops.\n\nWant an ops enablement reel plan?",
        ],
    ],
    "kcontreras@titlequest.net": [
        [
            "Sales marketing TitleQuest",
            "Hi Kat,\n\nYou sales marketing executive at TitleQuest, where the mission is lasting relationships through exceptional service and realtor resources on titlequest.net.\n\nMarketing leaders feel it when every closer sends a different quality social clip.\n\nWe standardize finishing on supplied event footage.\n\nWorth a sample?",
        ],
        [
            "ALTA 25 year team",
            "Hi Kat,\n\nALTA compliance and 25+ years average experience are trust signals worth short agent campaigns.\n\nWe batch hooks from one master you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Madeline table separate",
            "Hi Kat,\n\nMadeline may get closing-table notes; yours is growth and campaigns.\n\nOpen to a TitleQuest marketing kit outline?",
        ],
    ],
    "jcutler@titlequest.net": [
        [
            "IT admin TitleQuest",
            "Hi Justin,\n\nYou IT administrator at TitleQuest with e-recording, virtual closings, and ALTA compliance on titlequest.net.\n\nIT enables consistent delivery of training and closing video assets branch to branch.\n\nWe finish supplied webinar and screen recordings.\n\nWorth a sample?",
        ],
        [
            "Virtual closing stack",
            "Hi Justin,\n\nVirtual closing options only work if the files agents receive are formatted and paced consistently.\n\nWe handle post on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Kat marketing separate",
            "Hi Justin,\n\nKat may get marketing notes; yours is systems and asset delivery.\n\nWant an IT-enabled training reel outline?",
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

    (ROOT / "campaigns" / "pilot-20-batch9-research.json").write_text(
        json.dumps(RESEARCH, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "campaigns" / "pilot-20-batch9-copy.json").write_text(
        json.dumps(COPY, indent=2) + "\n", encoding="utf-8"
    )
    print("OK: 60/60 QA passed in draft")


if __name__ == "__main__":
    main()
