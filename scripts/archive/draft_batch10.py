#!/usr/bin/env python3
"""Draft batch 10 research + copy JSON with inline QA."""
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
        "row": 188,
        "csv_index": 187,
        "first_name": "Jackie",
        "last_name": "Barrett",
        "title": "General Counsel",
        "company": "Vesta Settlements, LLC",
        "email": "jbarrett@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/jackie-barrett-ba45a7a0",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "General counsel at Vesta Settlements; firm lists eight VA and MD offices, Closings Elevated, and realtor education on YouTube.",
        "research_notes": "Keith Barrett president same firm likely related. Batches 9-10 heavy Vesta coverage. Legal policy and compliance video angle.",
    },
    {
        "row": 189,
        "csv_index": 188,
        "first_name": "Melissa",
        "last_name": "Fones",
        "title": "Owner| Vice President of Business Development",
        "company": "Vesta Settlements, LLC",
        "email": "mfones@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/melissafones",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Owner and VP of business development at Vesta Settlements Leesburg; dual title sets firm growth and partner media standard.",
        "research_notes": "Sarah McKeone owner post closer batch 9. Melissa is owner plus BD. Keith Barrett president.",
    },
    {
        "row": 190,
        "csv_index": 189,
        "first_name": "Emma",
        "last_name": "Lowery",
        "title": "Buyer Specialist",
        "company": "Spencer Properties",
        "email": "emma@spencerprop.com",
        "website": "https://spencerprop.com",
        "linkedin": "http://www.linkedin.com/in/emma-lowery-8a1552143",
        "twitter": "https://twitter.com/spencerprops",
        "facebook": "https://facebook.com/spencerprop",
        "research_signal": "Buyer specialist at Spencer Properties Raleigh; site sold a Wakefield home sight unseen in one day using Matterport 3D tours during COVID restrictions.",
        "research_notes": "Website fetched May 2026. Sold portfolio includes Bedford Charleston full-price offer after holiday open house. Twitter spencerprops.",
    },
    {
        "row": 191,
        "csv_index": 190,
        "first_name": "Cris",
        "last_name": "Blanch",
        "title": "Escrow Typist",
        "company": "Lawyers Title of Cincinnati",
        "email": "cblanch@ltcincy.com",
        "website": "https://ltcincy.com",
        "linkedin": "http://www.linkedin.com/in/cris-blanch-30a79180",
        "twitter": "",
        "facebook": "",
        "research_signal": "Escrow typist at Lawyers Title of Cincinnati; ltcincy.com cites largest independent southwestern Ohio shop since 1936.",
        "research_notes": "Batch 9 had seven ltcincy contacts. Cris production desk angle. Mike Fletcher VP.",
    },
    {
        "row": 192,
        "csv_index": 191,
        "first_name": "Cheryl",
        "last_name": "Esquer",
        "title": "Account Executive",
        "company": "Lawyers Title Los Angeles",
        "email": "cheryl.esquer@ltic.com",
        "website": "https://ltic.com",
        "linkedin": "http://www.linkedin.com/in/cheryl-esquer-0b7384111",
        "twitter": "",
        "facebook": "",
        "research_signal": "Account executive at Lawyers Title Los Angeles Burbank on national ltic.com with title insurance and escrow services.",
        "research_notes": "LA branch first in campaign. AE referral and builder partnership angle.",
    },
    {
        "row": 193,
        "csv_index": 192,
        "first_name": "Bridgett",
        "last_name": "Jackson",
        "title": "Post Closer",
        "company": "Vesta Settlements, LLC",
        "email": "bjackson@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/bridgett-jackson-56289b1a4",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Post closer at Vesta Settlements; firm markets hybrid and full e-closing plus digital EMD delivery in CSV keywords.",
        "research_notes": "Sterling VA. Parallel Sarah, Soo, Bridgett post-close roles across batches 9-10.",
    },
    {
        "row": 194,
        "csv_index": 193,
        "first_name": "Brandi",
        "last_name": "Dosser",
        "title": "Director Of Operations",
        "company": "Lawyers Title DFW",
        "email": "brandi.dosser@ltic.com",
        "website": "https://ltic.com",
        "linkedin": "http://www.linkedin.com/in/brandi-dosser-27964a43",
        "twitter": "",
        "facebook": "",
        "research_signal": "Director of operations at Lawyers Title DFW Addison; batch 9 had Tatum escrow and Tamera host at same branch.",
        "research_notes": "Ops director owns branch training consistency. Lindsay Buzbee escrow same batch.",
    },
    {
        "row": 195,
        "csv_index": 194,
        "first_name": "Angie",
        "last_name": "Horton",
        "title": "Sales & Marketing at TitleQuest",
        "company": "TitleQuest",
        "email": "ahorton@titlequest.net",
        "website": "https://titlequest.net",
        "linkedin": "http://www.linkedin.com/in/angie-edmondson-horton-5a060a8b",
        "twitter": "https://twitter.com/titlequestllc",
        "facebook": "https://facebook.com/TitleQuest",
        "research_signal": "Sales and marketing at TitleQuest Chesapeake; site mission is lasting relationships through exceptional service with 25+ years average experience.",
        "research_notes": "LinkedIn slug angie-edmondson-horton. Brian Clements owner same firm batch.",
    },
    {
        "row": 196,
        "csv_index": 195,
        "first_name": "Mark",
        "last_name": "Macuk",
        "title": "Business Development Executive",
        "company": "TitleQuest",
        "email": "mmacuk@titlequest.net",
        "website": "https://titlequest.net",
        "linkedin": "http://www.linkedin.com/in/mark-macuk-6a137b156",
        "twitter": "https://twitter.com/titlequestllc",
        "facebook": "https://facebook.com/TitleQuest",
        "research_signal": "Business development executive at TitleQuest VA/NC markets; ALTA member with TitleCom examination affiliate on titlequest.net.",
        "research_notes": "BD growth angle distinct from Angie marketing and Brian owner.",
    },
    {
        "row": 197,
        "csv_index": 196,
        "first_name": "Karen",
        "last_name": "Franz",
        "title": "Front Desk Administrator",
        "company": "Vesta Settlements, LLC",
        "email": "kfranz@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/franzkc",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Front desk administrator at Vesta Settlements; first client touch should match Closings Elevated brand on vestasettlements.com.",
        "research_notes": "Harrisonburg VA. Client experience and intake video consistency.",
    },
    {
        "row": 198,
        "csv_index": 197,
        "first_name": "Diane",
        "last_name": "Bedinghaus",
        "title": "Controller at Lawyers Title",
        "company": "Lawyers Title of Cincinnati",
        "email": "dbedinghaus@ltcincy.com",
        "website": "https://ltcincy.com",
        "linkedin": "http://www.linkedin.com/in/diane-bedinghaus-b3446913",
        "twitter": "",
        "facebook": "",
        "research_signal": "Controller at Lawyers Title of Cincinnati independent agency since 1936 with Fidelity, First American, and Stewart ties.",
        "research_notes": "Sandy Holton bookkeeper batch 9. Diane controller finance ops enablement.",
    },
    {
        "row": 199,
        "csv_index": 198,
        "first_name": "Catherine",
        "last_name": "Flora",
        "title": "Processing Team Lead/Closing Administrator",
        "company": "TitleQuest",
        "email": "cflora@titlequest.net",
        "website": "https://titlequest.net",
        "linkedin": "http://www.linkedin.com/in/catherine-flora-5347a318a",
        "twitter": "https://twitter.com/titlequestllc",
        "facebook": "https://facebook.com/TitleQuest",
        "research_signal": "Processing team lead and closing administrator at TitleQuest; oversees closing pipeline for ALTA-compliant VA and NC transactions.",
        "research_notes": "Ops lead between processors and closers. Brian owner sets standard.",
    },
    {
        "row": 200,
        "csv_index": 199,
        "first_name": "Mai",
        "last_name": "Tran",
        "title": "Escrow Officer",
        "company": "Lawyers Title Company Bay Area",
        "email": "mai.tran1@ltic.com",
        "website": "https://lawyerstitlebayarea.com",
        "linkedin": "http://www.linkedin.com/in/mai-tran-bb65bb21",
        "twitter": "",
        "facebook": "",
        "research_signal": "Escrow officer at Lawyers Title Bay Area Burlingame; lawyerstitlebayarea.com leads with Own Your Future and Agent ONE net sheets.",
        "research_notes": "Karen Anderson AVP ops batch 9 same branch. Mai escrow table trust.",
    },
    {
        "row": 201,
        "csv_index": 200,
        "first_name": "John",
        "last_name": "Maghamez",
        "title": "Branch Manager and Attorney",
        "company": "Vesta Settlements, LLC",
        "email": "jmaghamez@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/john-a-maghamez-esq-96b36336",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Branch manager and attorney at Vesta Richmond office per CSV; LinkedIn slug john-a-maghamez-esq confirms ESQ.",
        "research_notes": "Andrea Turner branch manager batch 9 Ashburn. John attorney-led Richmond branch.",
    },
    {
        "row": 202,
        "csv_index": 201,
        "first_name": "Kelsey",
        "last_name": "Iles",
        "title": "Leasing Consultant",
        "company": "Nexus Property Management",
        "email": "crossings@nexuspm.com",
        "website": "https://nexri.com",
        "linkedin": "http://www.linkedin.com/in/kelsey-iles-0746bb162",
        "twitter": "https://twitter.com/NexusPropertyMg",
        "facebook": "https://facebook.com/NexusPropertyManagement",
        "research_signal": "Leasing consultant at Nexus Property Management Pawtucket; nexri.com cites 700+ units, video walkthroughs, and Property Management Authority positioning.",
        "research_notes": "Website fetched May 2026. Email crossings@nexuspm.com. New firm for campaign. RI and SE Massachusetts.",
    },
    {
        "row": 203,
        "csv_index": 202,
        "first_name": "Lindsay",
        "last_name": "Buzbee",
        "title": "Escrow Officer",
        "company": "Lawyers Title DFW",
        "email": "lindsay.buzbee@ltic.com",
        "website": "https://ltic.com",
        "linkedin": "http://www.linkedin.com/in/lindsay-buzbee-b47a775",
        "twitter": "",
        "facebook": "",
        "research_signal": "Escrow officer at Lawyers Title DFW Dallas; Addison office on national ltic.com with builder and lender services.",
        "research_notes": "Tatum Vanderpool escrow batch 9. Brandi Dosser ops director same branch batch 10.",
    },
    {
        "row": 204,
        "csv_index": 203,
        "first_name": "Brian",
        "last_name": "Clements",
        "title": "Managing Member/Owner",
        "company": "TitleQuest",
        "email": "brianc@titlequest.net",
        "website": "https://titlequest.net",
        "linkedin": "http://www.linkedin.com/in/brian-m-clements-6212352",
        "twitter": "https://twitter.com/titlequestllc",
        "facebook": "https://facebook.com/TitleQuest",
        "research_signal": "Managing member and owner at TitleQuest Chesapeake; site says 24+ years serving VA and NC with mission of exceptional service and ALTA standards.",
        "research_notes": "Owner sets firm-wide agent and lender media. Five TitleQuest contacts across batches 9-10.",
    },
    {
        "row": 205,
        "csv_index": 204,
        "first_name": "Laura",
        "last_name": "Tubridy",
        "title": "Settlement Agent",
        "company": "Vesta Settlements, LLC",
        "email": "ltubridy@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/laura-heap-tubridy-jd-b1a24327",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Settlement agent at Vesta; LinkedIn laura-heap-tubridy-jd shows JD credentials for table-side legal precision.",
        "research_notes": "Chantilly VA. Distinct from Alyson Readen settlement agent same batch.",
    },
    {
        "row": 206,
        "csv_index": 205,
        "first_name": "Keith",
        "last_name": "Barrett",
        "title": "President",
        "company": "Vesta Settlements, LLC",
        "email": "kbarrett@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/keith-barrett-594122",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "President at Vesta Settlements with eight offices and YouTube realtor education; Jackie Barrett general counsel same firm.",
        "research_notes": "President-level partner media standard. Melissa Fones owner VP BD. Heavy Vesta batch 9-10.",
    },
    {
        "row": 207,
        "csv_index": 206,
        "first_name": "Alyson",
        "last_name": "Readen",
        "title": "Settlement Agent",
        "company": "Vesta Settlements, LLC",
        "email": "areaden@vestasettlements.com",
        "website": "https://vestasettlements.com",
        "linkedin": "http://www.linkedin.com/in/alyson-readen-0876911a4",
        "twitter": "",
        "facebook": "http://www.facebook.com/vestasettlements",
        "research_signal": "Settlement agent at Vesta Settlements; firm Closings Elevated positioning and contracts@vestasettlements.com intake on site.",
        "research_notes": "Laura Tubridy JD settlement agent same batch. Differentiate consumer trust angles.",
    },
]

COPY = {
    "jbarrett@vestasettlements.com": [
        [
            "General counsel Vesta",
            "Hi Jackie,\n\nYou general counsel at Vesta Settlements with eight VA and MD offices and Closings, Elevated on vestasettlements.com.\n\nCounsel sets the standard for wire-fraud and policy clips every branch must follow.\n\nWe finish supplied training and legal-update footage.\n\nWorth a sample?",
        ],
        [
            "YouTube realtor channel",
            "Hi Jackie,\n\nThe firm educates realtors on YouTube; legal precision should match that tone in short compliance cuts.\n\nWe engineer captions and grade on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Keith president separate",
            "Hi Jackie,\n\nKeith may get president notes; yours is counsel-led risk and policy enablement.\n\nOpen to a compliance reel outline?",
        ],
    ],
    "mfones@vestasettlements.com": [
        [
            "Owner VP BD Vesta",
            "Hi Melissa,\n\nYou owner and VP of business development at Vesta in Leesburg with eight offices and realtor education on YouTube.\n\nOwners scale when every market sends the same partner and growth clip quality.\n\nWe finish supplied event and webinar footage.\n\nWorth a sample?",
        ],
        [
            "Not a file number",
            "Hi Melissa,\n\nVesta says clients are not just another file number; BD video should prove that before the first referral.\n\nWe batch hooks from one master you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Sarah owner separate",
            "Hi Melissa,\n\nSarah McKeone may have seen owner post-closer notes in batch 9; yours is firm-wide growth.\n\nWant an owner BD reel plan?",
        ],
    ],
    "emma@spencerprop.com": [
        [
            "Matterport sight unseen",
            "Hi Emma,\n\nYou buyer specialist at Spencer Properties Raleigh; spencerprop.com sold a Wakefield home sight unseen in one day using Matterport 3D tours during COVID restrictions.\n\nBuyer specialists win when listing media looks as sharp as that marketing story.\n\nWe finish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Bedford holiday open house",
            "Hi Emma,\n\nYour sold portfolio describes a Bedford Charleston listing that drew a full-price offer after a holiday open house with live music and neighbor invites.\n\nWe batch hook variants from one showing you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "spencerprops Twitter",
            "Hi Emma,\n\nFirm Twitter spencerprops and Facebook should match your buyer-facing reel library.\n\nOpen to a buyer-specialist tour spec?",
        ],
    ],
    "cblanch@ltcincy.com": [
        [
            "Escrow typist Cincinnati",
            "Hi Cris,\n\nYou escrow typist at Lawyers Title of Cincinnati, largest independent residential closer in southwestern Ohio since 1936 on ltcincy.com.\n\nTypists reduce repeat calls when timeline clips match every closer desk.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "1936 independent",
            "Hi Cris,\n\nHigh volume breaks down when one branch sends a different quality wire-safety explainer.\n\nWe standardize finishing on footage you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Mike VP separate",
            "Hi Cris,\n\nMike Fletcher may have seen VP notes in batch 9; yours is production-desk consistency.\n\nWant a typist-led timeline outline?",
        ],
    ],
    "cheryl.esquer@ltic.com": [
        [
            "AE Lawyers Title LA",
            "Hi Cheryl,\n\nYou account executive at Lawyers Title Los Angeles on ltic.com with title insurance and escrow for Burbank-area partners.\n\nAEs win when referral partners get short clips they actually forward.\n\nWe finish supplied partner and event footage.\n\nWorth a sample?",
        ],
        [
            "LA branch growth",
            "Hi Cheryl,\n\nNational brand power only helps if your personal outreach looks as polished as the parent site.\n\nWe batch shorts from one master you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Bay Area separate",
            "Hi Cheryl,\n\nMai and Karen may get Bay Area notes; yours is Los Angeles AE growth.\n\nOpen to a builder lunch reel plan?",
        ],
    ],
    "bjackson@vestasettlements.com": [
        [
            "Post closer Vesta",
            "Hi Bridgett,\n\nYou post closer at Vesta with hybrid and full e-closing plus digital EMD in the firm keywords.\n\nPost-close specialists cut repeat calls when payoff explainers look clear on mobile.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Sterling desk rhythm",
            "Hi Bridgett,\n\nClosings, Elevated should sound the same from your Sterling desk as every other Vesta office.\n\nWe engineer shorts from narration you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Soo parallel role",
            "Hi Bridgett,\n\nSoo and Sarah may get parallel post-close notes; yours is Bridgett-led follow-through.\n\nWant a post-close education kit?",
        ],
    ],
    "brandi.dosser@ltic.com": [
        [
            "DFW ops director",
            "Hi Brandi,\n\nYou director of operations at Lawyers Title DFW in Addison on ltic.com with builder and lender services in the keywords.\n\nOps directors scale when every escrow desk sends the same training quality.\n\nWe finish supplied webinar footage.\n\nWorth a sample?",
        ],
        [
            "Tatum host batch 9",
            "Hi Brandi,\n\nTatum and Tamera may have seen escrow and host notes in batch 9; yours is branch-wide ops enablement.\n\nWe standardize finishing on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Lindsay escrow separate",
            "Hi Brandi,\n\nLindsay may get escrow notes; you set the DFW finishing template.\n\nOpen to an ops onboarding reel outline?",
        ],
    ],
    "ahorton@titlequest.net": [
        [
            "Sales marketing TitleQuest",
            "Hi Angie,\n\nYou sales and marketing at TitleQuest where titlequest.net promises lasting relationships through exceptional service and 25+ years average team experience.\n\nMarketing feels it when every closer sends a different quality social clip.\n\nWe standardize finishing on supplied event footage.\n\nWorth a sample?",
        ],
        [
            "ALTA exceptional service",
            "Hi Angie,\n\nALTA compliance is a trust signal; campaigns should show that in two seconds on mobile.\n\nWe batch hooks from one master you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Brian owner separate",
            "Hi Angie,\n\nBrian may get owner notes; yours is sales and marketing campaigns.\n\nWant a TitleQuest growth kit outline?",
        ],
    ],
    "mmacuk@titlequest.net": [
        [
            "BD exec TitleQuest",
            "Hi Mark,\n\nYou business development executive at TitleQuest with TitleCom examination affiliate and Quest Insurance on titlequest.net.\n\nBD wins when lender and investor partners get portfolio story video, not PDFs alone.\n\nWe finish supplied partner footage.\n\nWorth a sample?",
        ],
        [
            "VA NC relationships",
            "Hi Mark,\n\nThe site says it does not treat parties as one-time transactions; BD video should match that relationship promise.\n\nPost-production on footage you supply.\n\nCurious?",
        ],
        [
            "Angie marketing separate",
            "Hi Mark,\n\nAngie may get marketing notes; yours is net-new partner development.\n\nOpen to a BD spotlight reel plan?",
        ],
    ],
    "kfranz@vestasettlements.com": [
        [
            "Front desk Vesta",
            "Hi Karen,\n\nYou front desk administrator at Vesta; first-touch client experience should match Closings, Elevated on vestasettlements.com.\n\nIntake teams win when welcome and wire-instruction clips sound identical office to office.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Harrisonburg touchpoint",
            "Hi Karen,\n\nYour Harrisonburg desk is often the first voice buyers hear; video should match that warmth on mobile.\n\nWe engineer shorts from narration you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Eight offices scale",
            "Hi Karen,\n\nKeith and Melissa may get executive notes; yours is front-line client experience.\n\nWant an intake reel outline?",
        ],
    ],
    "dbedinghaus@ltcincy.com": [
        [
            "Controller ltcincy",
            "Hi Diane,\n\nYou controller at Lawyers Title of Cincinnati, independent since 1936 with national underwriter relationships on ltcincy.com.\n\nControllers align when internal training video matches agent-facing clip quality.\n\nWe finish supplied webinar footage.\n\nWorth a sample?",
        ],
        [
            "Finance ops scale",
            "Hi Diane,\n\nSandy may have seen bookkeeper notes in batch 9; yours is controller-led ops and reporting clarity.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Mike VP separate",
            "Hi Diane,\n\nMike may get VP notes; yours is finance and compliance enablement.\n\nOpen to an internal training reel outline?",
        ],
    ],
    "cflora@titlequest.net": [
        [
            "Processing lead TitleQuest",
            "Hi Catherine,\n\nYou processing team lead and closing administrator at TitleQuest with ALTA-compliant VA and NC pipeline on titlequest.net.\n\nLeads scale when every processor sends the same timeline and wire clip quality.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Closing admin pipeline",
            "Hi Catherine,\n\nClosing administrators own throughput; inconsistent explainers create repeat agent calls.\n\nWe standardize finishing on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Brian owner separate",
            "Hi Catherine,\n\nBrian may get owner notes; yours is processing and closing ops.\n\nWant a pipeline training kit outline?",
        ],
    ],
    "mai.tran1@ltic.com": [
        [
            "Escrow officer Bay Area",
            "Hi Mai,\n\nYou escrow officer at Lawyers Title Bay Area where lawyerstitlebayarea.com leads with Own Your Future and Agent ONE net sheets.\n\nEscrow officers need wire-safety clips agents actually forward before funding.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Burlingame closings",
            "Hi Mai,\n\nBay Area volume breaks down when one desk sends a different quality table-side explainer.\n\nWe engineer from screen recordings you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Karen ops separate",
            "Hi Mai,\n\nKaren Anderson may have seen AVP ops notes in batch 9; yours is escrow-led trust.\n\nWant a wire-instruction reel spec?",
        ],
    ],
    "jmaghamez@vestasettlements.com": [
        [
            "Branch mgr attorney RVA",
            "Hi John,\n\nYou branch manager and attorney at Vesta with LinkedIn john-a-maghamez-esq and Richmond market focus in the CSV.\n\nAttorney-led branches win when pre-close video sounds as precise as table-side counsel.\n\nWe finish supplied client and lender footage.\n\nWorth a sample?",
        ],
        [
            "Richmond Vesta office",
            "Hi John,\n\nEight offices mean Richmond needs its own credible cuts, not generic national templates.\n\nWe batch shorts from one master you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Andrea branch separate",
            "Hi John,\n\nAndrea may have seen Ashburn branch notes in batch 9; yours is Richmond attorney-manager leadership.\n\nOpen to a branch reel plan?",
        ],
    ],
    "crossings@nexuspm.com": [
        [
            "Leasing consultant Nexus",
            "Hi Kelsey,\n\nYou leasing consultant at Nexus Property Management; nexri.com cites 700+ units, video walkthroughs, and Property Management Authority in RI and SE Massachusetts.\n\nLeasing wins when vacancy marketing and tour video share one finishing template.\n\nWe finish supplied property footage.\n\nWorth a sample?",
        ],
        [
            "crossings email domain",
            "Hi Kelsey,\n\nYour crossings@nexuspm.com address fits multi-property leasing; shorts should read distinct per asset from one master walkthrough.\n\nWe batch hooks on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "24/7 maintenance line",
            "Hi Kelsey,\n\nNexus markets 24/7 response and in-house maintenance; owner-facing clips should match that reliability.\n\nWant a leasing reel kit outline?",
        ],
    ],
    "lindsay.buzbee@ltic.com": [
        [
            "Escrow officer DFW",
            "Hi Lindsay,\n\nYou escrow officer at Lawyers Title DFW Addison on ltic.com with builder and lender services in the firm keywords.\n\nEscrow officers need wire-safety clips agents actually forward.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Brandi ops separate",
            "Hi Lindsay,\n\nBrandi may get ops director notes; yours is table-side consumer trust.\n\nWe engineer from screen recordings you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Tatum batch 9",
            "Hi Lindsay,\n\nTatum Vanderpool may have seen parallel escrow notes in batch 9; yours is Lindsay-branded DFW cuts.\n\nOpen to a wire-instruction outline?",
        ],
    ],
    "brianc@titlequest.net": [
        [
            "Owner TitleQuest",
            "Hi Brian,\n\nYou managing member and owner at TitleQuest, serving VA and NC 24+ years with exceptional service and ALTA standards on titlequest.net.\n\nOwners set agent and lender media standard for the whole firm.\n\nWe finish supplied partner and training footage.\n\nWorth a sample?",
        ],
        [
            "25 year team average",
            "Hi Brian,\n\n25+ years average experience is a trust story worth short agent campaigns, not a footer line.\n\nWe batch hooks from one master you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Five firm contacts",
            "Hi Brian,\n\nAngie, Mark, Catherine, and Madeline may get role notes across batches 9-10; you can align one TitleQuest template.\n\nWant an owner enablement reel plan?",
        ],
    ],
    "ltubridy@vestasettlements.com": [
        [
            "Settlement agent JD",
            "Hi Laura,\n\nYou settlement agent at Vesta; LinkedIn laura-heap-tubridy-jd shows JD credentials for table-side legal precision.\n\nSettlement agents own trust when complex topics look clear on mobile.\n\nWe finish supplied consumer explainers.\n\nWorth a sample?",
        ],
        [
            "Chantilly closings",
            "Hi Laura,\n\nClosings, Elevated should match your Chantilly desk tone in every buyer and seller clip.\n\nWe handle grade and captions on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Alyson agent separate",
            "Hi Laura,\n\nAlyson may get parallel settlement notes; yours leads with JD credibility.\n\nWant a settlement-officer outline?",
        ],
    ],
    "kbarrett@vestasettlements.com": [
        [
            "President Vesta",
            "Hi Keith,\n\nYou president at Vesta Settlements with eight offices, YouTube realtor education, and Jackie Barrett as general counsel on the team.\n\nPresidents scale when every market sends the same partner and compliance clip quality.\n\nWe finish supplied leadership and training footage.\n\nWorth a sample?",
        ],
        [
            "Closings elevated",
            "Hi Keith,\n\nClosings, Elevated is the public promise; president-level video should prove it before agents pick up the phone.\n\nWe standardize finishing on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Melissa owner separate",
            "Hi Keith,\n\nMelissa may get owner VP BD notes; yours is president-led firm standard.\n\nOpen to an executive partner reel plan?",
        ],
    ],
    "areaden@vestasettlements.com": [
        [
            "Settlement agent Vesta",
            "Hi Alyson,\n\nYou settlement agent at Vesta; vestasettlements.com uses Closings, Elevated and contracts@vestasettlements.com for intake.\n\nAgents and buyers judge you on how clear pre-close video is, not PDFs alone.\n\nWe finish supplied explainers with captions and grade.\n\nWorth a sample?",
        ],
        [
            "Consumer trust mobile",
            "Hi Alyson,\n\nWire and timeline clips should look credible on mobile before the file hits your desk.\n\nWe engineer retention pacing on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Laura JD separate",
            "Hi Alyson,\n\nLaura Tubridy may get JD-forward notes; yours is Alyson-branded table-side trust.\n\nWant a buyer-guide video outline?",
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

    (ROOT / "campaigns" / "pilot-20-batch10-research.json").write_text(
        json.dumps(RESEARCH, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "campaigns" / "pilot-20-batch10-copy.json").write_text(
        json.dumps(COPY, indent=2) + "\n", encoding="utf-8"
    )
    print("OK: 60/60 QA passed in draft")


if __name__ == "__main__":
    main()
