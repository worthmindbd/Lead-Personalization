#!/usr/bin/env python3
"""Draft batch 7 research + copy JSON with inline QA."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "leads" / "Real-Estate-USA-500.csv"

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
        "row": 128,
        "csv_index": 127,
        "first_name": "Jana",
        "last_name": "Gantt",
        "title": "Attorney",
        "company": "Lawyers Signature Settlements, LLC.",
        "email": "jana@signaturesettlements.com",
        "website": "https://signaturesettlements.com",
        "linkedin": "http://www.linkedin.com/in/jana-gantt-83109722",
        "twitter": "",
        "facebook": "https://facebook.com/lawyerssignaturesettlements",
        "research_signal": "Attorney at Lawyers Signature Frederick MD; firm is attorney-operated with virtual settlements, 200+ years combined experience, and FSBO, 1031, and construction loans on site.",
        "research_notes": "Batch 6 contacted Tiphanie, Nick, Shannon at same firm. Jana is attorney angle. Website from batch 6 fetch May 2026.",
    },
    {
        "row": 129,
        "csv_index": 128,
        "first_name": "Andrew",
        "last_name": "Braceras",
        "title": "Residential Staff Attorney",
        "company": "Atlantic Coast Title Company, LLC",
        "email": "dbraceras@atlancoast.com",
        "website": "https://atlancoast.com",
        "linkedin": "http://www.linkedin.com/in/andrew-braceras-5b0b2015",
        "twitter": "",
        "facebook": "https://facebook.com/atlantic.coasttitle.5",
        "research_signal": "Residential staff attorney at Atlantic Coast Title South Portland ME; site announces Feb 2026 integration with Simple Title Closing and Escrow while keeping the same closers and attorneys.",
        "research_notes": "Website fetched May 2026. 340+ years combined team experience cited. Five ACTC contacts this batch.",
    },
    {
        "row": 130,
        "csv_index": 129,
        "first_name": "Adam",
        "last_name": "Umina",
        "title": "Owner/Principal",
        "company": "Metro Realty Corp.",
        "email": "adam@metrorealtycorp.com",
        "website": "https://metrorealtycorp.com",
        "linkedin": "http://www.linkedin.com/in/adam-umina-0a17124",
        "twitter": "https://twitter.com/metrorealtycorp",
        "facebook": "https://facebook.com/pages/refname/8974053300",
        "research_signal": "President and principal broker at Metro Realty; site quotes a 20-year client saying Adam helped them rent several times and find contractors for updates.",
        "research_notes": "Website fetched May 2026. $850M+ sold, Best of Boston, leadership page. Cindy Katz testimonial pairs with Adam.",
    },
    {
        "row": 131,
        "csv_index": 130,
        "first_name": "Marisa",
        "last_name": "Cardone",
        "title": "Realtor",
        "company": "United Realty Partners",
        "email": "marisa@unitedlendingpartners.com",
        "website": "https://gounitedrealty.com",
        "linkedin": "http://www.linkedin.com/in/mcardone",
        "twitter": "",
        "facebook": "https://facebook.com/UnitedRealtyPartnersDarien",
        "research_signal": "Realtor at United Realty Partners Burr Ridge IL; site says independent brokerage delivering value with care since 2005 with 5.0 rating from 34 reviews.",
        "research_notes": "Website fetched May 2026. Reviews center on Sam Abunaser; Marisa uses unitedlendingpartners email. Chicago suburbs positioning.",
    },
    {
        "row": 132,
        "csv_index": 131,
        "first_name": "Brenna",
        "last_name": "McDaniel",
        "title": "Title Clerk",
        "company": "Five Star Title, LLC",
        "email": "bmcdaniel@fivestarlandtitle.com",
        "website": "https://fivestarlandtitle.com",
        "linkedin": "http://www.linkedin.com/in/brenna-r-mcdaniel-0876911a4",
        "twitter": "",
        "facebook": "https://www.facebook.com/FiveStarLandTitle/",
        "research_signal": "Title clerk at Five Star Land Title Somerset KY; site markets statewide Kentucky residential and commercial closings with integrity and teamwork core values.",
        "research_notes": "Website fetched May 2026. Buyer and seller checklists, title exams, realtor forms online.",
    },
    {
        "row": 133,
        "csv_index": 132,
        "first_name": "Martine",
        "last_name": "Sapp",
        "title": "Lawyers Signature Settlements, LLC.",
        "company": "Lawyers Signature Settlements, LLC.",
        "email": "martine@signaturesettlements.com",
        "website": "https://signaturesettlements.com",
        "linkedin": "http://www.linkedin.com/in/martine-sapp-a8842a148",
        "twitter": "",
        "facebook": "https://facebook.com/lawyerssignaturesettlements",
        "research_signal": "Team member at Lawyers Signature Frederick; CSV title repeats company name. Firm serves MD PA VA WV DC with attorney-operated settlements.",
        "research_notes": "Fourth Lawyers Signature contact after batch 6 trio. LinkedIn confirms firm affiliation.",
    },
    {
        "row": 134,
        "csv_index": 133,
        "first_name": "Jonathan",
        "last_name": "Smith",
        "title": "Director Of Business Development",
        "company": "Venture Real Estate Group, LLC",
        "email": "jsmith@vreg.co",
        "website": "https://vreg.co",
        "linkedin": "http://www.linkedin.com/in/jonathan-smith-140582213",
        "twitter": "https://twitter.com/vregroup",
        "facebook": "https://facebook.com/vreg.co",
        "research_signal": "Director of business development at Venture Real Estate Group Bellevue; firm keywords span investor representation, multi-family, and commercial brokerage.",
        "research_notes": "Fifth VREG contact. Batch 6 had Stephanie, Tammie, Shreya. BD role suits partner and referral video.",
    },
    {
        "row": 135,
        "csv_index": 134,
        "first_name": "Melody",
        "last_name": "Coleman",
        "title": "Account Manager",
        "company": "Lawyers Title - San Diego",
        "email": "melody.coleman@ltic.com",
        "website": "https://lticsd.com",
        "linkedin": "http://www.linkedin.com/in/melody-stoneburner",
        "twitter": "",
        "facebook": "",
        "research_signal": "Account manager at Lawyers Title San Diego; site headline Good people doing great work and highlights Agent ONE net sheets and TitlePro247 farms.",
        "research_notes": "Website fetched May 2026. Batch 5 had other ltic.com contacts. LinkedIn slug melody-stoneburner.",
    },
    {
        "row": 136,
        "csv_index": 135,
        "first_name": "Kevin",
        "last_name": "Goodwin",
        "title": "Owner, Broker, Realtor®",
        "company": "Goodwin & Thyne Properties, Inc.",
        "email": "kevin@gtprop.com",
        "website": "https://gtprop.com",
        "linkedin": "http://www.linkedin.com/in/kevin-goodwin-b16a083a",
        "twitter": "",
        "facebook": "https://facebook.com/pages/Goodwin-Thyne-Properties-Inc/545989825476579",
        "research_signal": "Owner broker at Goodwin and Thyne Santa Barbara; site cites $1.19B total sales, 1,409 transactions, and dozens of Kevin-led testimonials.",
        "research_notes": "Website fetched May 2026. Molly and Melani batch 6 same firm. Law Office of John J. Thyne III affiliation.",
    },
    {
        "row": 137,
        "csv_index": 136,
        "first_name": "Brian",
        "last_name": "Peitz",
        "title": "VP of Sales & Marketing",
        "company": "Chicago Title Arizona",
        "email": "brian.peitz@ctt.com",
        "website": "https://chicagotitlearizona.com",
        "linkedin": "http://www.linkedin.com/in/brianpeitz",
        "twitter": "https://twitter.com/azchicagotitle",
        "facebook": "https://facebook.com/pages/Chicago-Title-Insurance-Arizona/127268827343322",
        "research_signal": "VP of sales and marketing at Chicago Title Arizona; homepage pushes Wiresafe wire-fraud education and 13 Maricopa offices.",
        "research_notes": "Website fetched May 2026. inHere platform mentioned. Marc and Julie same firm this batch.",
    },
    {
        "row": 138,
        "csv_index": 137,
        "first_name": "Melissa",
        "last_name": "Donahue",
        "title": "Title Attorney",
        "company": "Atlantic Coast Title Company, LLC",
        "email": "mdonahue@atlancoast.com",
        "website": "https://atlancoast.com",
        "linkedin": "http://www.linkedin.com/in/melissa-donahue-1a2a59117",
        "twitter": "",
        "facebook": "https://facebook.com/atlantic.coasttitle.5",
        "research_signal": "Title attorney at Atlantic Coast Title; client review praises staff making refinancing paperwork understandable since 1998.",
        "research_notes": "Simple Title rebrand Feb 2026. Attorney-led credibility for lender and agent education video.",
    },
    {
        "row": 139,
        "csv_index": 138,
        "first_name": "Cindy",
        "last_name": "Katz",
        "title": "Sales Associate",
        "company": "Metro Realty Corp.",
        "email": "cindy@metrorealtycorp.com",
        "website": "https://metrorealtycorp.com",
        "linkedin": "http://www.linkedin.com/in/cindy-katz-34246865",
        "twitter": "https://twitter.com/metrorealtycorp",
        "facebook": "https://facebook.com/pages/refname/8974053300",
        "research_signal": "Metro site review from John G: Adam Umina and Cindy Katz helped buy a first home and rent a unit rapidly in a seamless process.",
        "research_notes": "Website fetched May 2026. Sales associate title. Adam owner same batch.",
    },
    {
        "row": 140,
        "csv_index": 139,
        "first_name": "Kelly",
        "last_name": "Sullivan",
        "title": "Account Relationship Manager and Closing Agent",
        "company": "Atlantic Coast Title Company, LLC",
        "email": "ksullivan@atlancoast.com",
        "website": "https://atlancoast.com",
        "linkedin": "http://www.linkedin.com/in/kelly-sullivan-0429169",
        "twitter": "",
        "facebook": "https://facebook.com/atlantic.coasttitle.5",
        "research_signal": "Account relationship manager and closing agent at Atlantic Coast; site testimonial highlights knowledgeable friendly timely communications through purchase closings.",
        "research_notes": "Dual ARM and closer role. Maine NH residential and commercial services.",
    },
    {
        "row": 141,
        "csv_index": 140,
        "first_name": "Jordan",
        "last_name": "Harman",
        "title": "Licensed Real Estate Agent",
        "company": "Lawyers Realty LLC",
        "email": "jflowers@lawyersrealtypa.com",
        "website": "https://lawyersrealtypa.com",
        "linkedin": "http://www.linkedin.com/in/jharmanthehomegirl",
        "twitter": "https://twitter.com/lawyersrealty",
        "facebook": "https://facebook.com/lawyersrealtyllc",
        "research_signal": "Licensed agent at Lawyers Realty LLC Mechanicsburg; LinkedIn brand jharmanthehomegirl and firm Twitter lawyersrealty for Harrisburg-area inventory.",
        "research_notes": "Mark Duffie owner batch 6. Megan Group batch 5. Site timeout; use CSV keywords and social handles.",
    },
    {
        "row": 142,
        "csv_index": 141,
        "first_name": "Dawna",
        "last_name": "Phillips",
        "title": "Paralegal",
        "company": "Atlantic Coast Title Company, LLC",
        "email": "dphillips@atlancoast.com",
        "website": "https://atlancoast.com",
        "linkedin": "http://www.linkedin.com/in/dawna-phillips-6a0ab01a",
        "twitter": "",
        "facebook": "https://facebook.com/atlantic.coasttitle.5",
        "research_signal": "Paralegal at Atlantic Coast Title; industry testimonial on site says ACTC stays top of list for calm professional 5-star service.",
        "research_notes": "Paralegal angle: file-prep and pre-close education. Simple Title transition Feb 2026.",
    },
    {
        "row": 143,
        "csv_index": 142,
        "first_name": "Marco",
        "last_name": "Potestio",
        "title": "Closing Agent",
        "company": "American Homeland Title Agency, Inc.",
        "email": "marco@americanhomelandtitle.com",
        "website": "https://americanhomelandtitle.com",
        "linkedin": "http://www.linkedin.com/in/marco-potestio-55b9a8263",
        "twitter": "https://twitter.com/AmericanHomelnd",
        "facebook": "https://www.facebook.com/americanhomelandtitle/",
        "research_signal": "Closing agent at American Homeland Cincinnati; site publishes Ohio heirship and partition consumer guides.",
        "research_notes": "Mary Lakes funder batch 6 same agency. Closing table trust video angle.",
    },
    {
        "row": 144,
        "csv_index": 143,
        "first_name": "Erin",
        "last_name": "Laplante",
        "title": "Director Of Operations & HR",
        "company": "Atlantic Coast Title Company, LLC",
        "email": "elaplante@atlancoast.com",
        "website": "https://atlancoast.com",
        "linkedin": "http://www.linkedin.com/in/erin-laplante-139a60",
        "twitter": "",
        "facebook": "https://facebook.com/atlantic.coasttitle.5",
        "research_signal": "Director of operations and HR at Atlantic Coast Title during Simple Title rebrand; site promises faster processing and smarter closing tools.",
        "research_notes": "Ops and HR owns internal training and partner onboarding consistency. Sixth ACTC contact.",
    },
    {
        "row": 145,
        "csv_index": 144,
        "first_name": "Cynthia",
        "last_name": "Maez",
        "title": "Licensed Realtor",
        "company": "Goodwin & Thyne Properties, Inc.",
        "email": "cynthiamaez@gtprop.com",
        "website": "https://gtprop.com",
        "linkedin": "http://www.linkedin.com/in/cynthia-maez-a3264458",
        "twitter": "",
        "facebook": "https://facebook.com/pages/Goodwin-Thyne-Properties-Inc/545989825476579",
        "research_signal": "Licensed realtor at Goodwin and Thyne Santa Barbara; firm integrates broker-attorney team with $1.19B sales and world-class performance marketing.",
        "research_notes": "Kevin owner and Molly marketing batch 6. Agent-level listing media consistency.",
    },
    {
        "row": 146,
        "csv_index": 145,
        "first_name": "Marc",
        "last_name": "Cousins",
        "title": "Escrow Officer",
        "company": "Chicago Title Arizona",
        "email": "marc.cousins@ctt.com",
        "website": "https://chicagotitlearizona.com",
        "linkedin": "http://www.linkedin.com/in/marc-cousins-b4739925",
        "twitter": "https://twitter.com/azchicagotitle",
        "facebook": "https://facebook.com/pages/Chicago-Title-Insurance-Arizona/127268827343322",
        "research_signal": "Escrow officer at Chicago Title Arizona; site testimonials praise teams handling 10-day escrows and smooth professional closings under pressure.",
        "research_notes": "Wire fraud Wiresafe positioning. Brian VP marketing same firm.",
    },
    {
        "row": 147,
        "csv_index": 146,
        "first_name": "Julie",
        "last_name": "Larraza",
        "title": "Business Develooment Manager",
        "company": "Chicago Title Arizona",
        "email": "julie.larraza@ctt.com",
        "website": "https://chicagotitlearizona.com",
        "linkedin": "http://www.linkedin.com/in/julie-larraza-b942457",
        "twitter": "https://twitter.com/azchicagotitle",
        "facebook": "https://facebook.com/pages/Chicago-Title-Insurance-Arizona/127268827343322",
        "research_signal": "Business development manager at Chicago Title Arizona Maricopa; site lists Deidre Krystek as BD peer and 13 offices across the valley.",
        "research_notes": "CSV typo Develooment. BD role: agent and builder referral partnerships. Brian Peitz VP sales separate angle.",
    },
]

COPY = {
    "jana@signaturesettlements.com": [
        [
            "Attorney Lawyers Signature",
            "Hi Jana,\n\nYou practice as an attorney at Lawyers Signature in Frederick, attorney-operated with virtual settlements and 200+ years combined team experience on the site.\n\nAttorney-led shops win when pre-close video sounds as precise as your contract review.\n\nWe finish supplied client and partner footage.\n\nWorth a sample?",
        ],
        [
            "1031 and construction",
            "Hi Jana,\n\nFSBO, 1031, and construction loans on signaturesettlements.com each need a distinct 45-second explainer from one master interview.\n\nWe engineer captions, grade, and retention pacing on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Batch 6 firm contacts",
            "Hi Jana,\n\nTiphanie, Nick, and Shannon may have seen parallel notes; yours is attorney credibility for agents.\n\nOpen to a legal-forward education outline?",
        ],
    ],
    "dbraceras@atlancoast.com": [
        [
            "Simple Title rebrand",
            "Hi Andrew,\n\nAtlantic Coast Title's site says the team is integrating with Simple Title Closing and Escrow in February 2026 while keeping the same attorneys and closers.\n\nStaff attorneys need partner video that matches that continuity story.\n\nWe finish supplied training and client footage.\n\nWorth a sample?",
        ],
        [
            "Maine 340 years",
            "Hi Andrew,\n\nSouth Portland positioning cites 340+ years of combined industry experience on atlancoast.com.\n\nShort residential closing explainers help agents trust the rebrand.\n\nPost-production on footage you supply.\n\nCurious?",
        ],
        [
            "Residential staff attorney",
            "Hi Andrew,\n\nMelissa and Kelly may get parallel notes; yours is residential legal review at the file level.\n\nWant a staff-attorney reel spec?",
        ],
    ],
    "adam@metrorealtycorp.com": [
        [
            "20-year client quote",
            "Hi Adam,\n\nMetro's site quotes a client saying you helped them rent their apartment several times over 20 years and connected contractors for updates.\n\nAs president and principal broker, that longevity should show in every listing reel.\n\nWe finish supplied tour and landlord footage.\n\nWorth a sample?",
        ],
        [
            "$850M Brookline",
            "Hi Adam,\n\nBest of Boston, 5,000+ rentals, and $850M+ sold is heavy proof; owners scale when media quality is consistent across agents.\n\nWe standardize finishing on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Cindy paired review",
            "Hi Adam,\n\nJohn G's review pairs you with Cindy Katz on a seamless first-home buy; we can align owner and agent cuts from one template.\n\nOpen to a leadership reel plan?",
        ],
    ],
    "marisa@unitedlendingpartners.com": [
        [
            "URP since 2005",
            "Hi Marisa,\n\nUnited Realty Partners in Burr Ridge has delivered value with care since 2005 with a 5.0 rating from 34 public reviews on gounitedrealty.com.\n\nChicago suburban inventory wins when your personal reel matches that brokerage standard.\n\nWe finish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Save on buy sell",
            "Hi Marisa,\n\nThe site markets save-when-you-buy and save-when-you-sell sliders; video should make that value obvious in two seconds.\n\nWe batch hook variants from one showing you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Darien independent",
            "Hi Marisa,\n\nReviews highlight Sam Abunaser heavily; yours can lead with independent brokerage positioning in the western suburbs.\n\nWant a first-time buyer reel outline?",
        ],
    ],
    "bmcdaniel@fivestarlandtitle.com": [
        [
            "Somerset KY title clerk",
            "Hi Brenna,\n\nYou title clerk at Five Star Land Title in Somerset, marketed statewide across Kentucky with integrity and teamwork as core values.\n\nClerks reduce repeat calls when buyer checklists look credible on mobile.\n\nWe finish supplied screen recordings and explainers.\n\nWorth a sample?",
        ],
        [
            "Five Star service",
            "Hi Brenna,\n\nfivestarlandtitle.com promises Five Star service on residential and commercial closings; that brand should sound the same in every county office.\n\nWe engineer short series from webinars you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Realtor forms online",
            "Hi Brenna,\n\nOnline realtor forms and title opinions fit a 60-second agent onboarding cut.\n\nOpen to a clerk-led education outline?",
        ],
    ],
    "martine@signaturesettlements.com": [
        [
            "Lawyers Signature team",
            "Hi Martine,\n\nYou are on the Lawyers Signature team in Frederick, attorney-operated across MD, VA, WV, PA, and DC.\n\nTeam members carry trust on Facebook and at local association events.\n\nWe finish supplied event and office footage.\n\nWorth a sample?",
        ],
        [
            "Clients more than file",
            "Hi Martine,\n\nThe site promises clients are more than just a file; short settlement explainers should match that tone.\n\nWe handle edit, grade, and captions on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Fourth firm contact",
            "Hi Martine,\n\nJana, Tiphanie, Nick, and Shannon may have parallel threads; we can align one firm template.\n\nCurious?",
        ],
    ],
    "jsmith@vreg.co": [
        [
            "VREG BD director",
            "Hi Jonathan,\n\nYou director of business development at Venture Real Estate Group in Bellevue.\n\nBD leaders win when partner and referral video looks as sharp as investor-facing decks.\n\nWe finish supplied property and webinar footage.\n\nWorth a sample?",
        ],
        [
            "vregroup channel",
            "Hi Jonathan,\n\nFirm Twitter vregroup and commercial keywords should match the stories you pitch to new partners.\n\nWe batch shorts from one master you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "IR batch 6 separate",
            "Hi Jonathan,\n\nShreya and Stephanie may have seen IR and broker notes; yours is net-new partner development.\n\nWant a BD spotlight reel plan?",
        ],
    ],
    "melody.coleman@ltic.com": [
        [
            "Good people LT SD",
            "Hi Melody,\n\nLawyers Title San Diego leads with Good people doing great work on lticsd.com, plus Agent ONE net sheets and TitlePro247 farms.\n\nAccount managers scale when every rep sends the same quality partner clip.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Account manager farms",
            "Hi Melody,\n\nFarm packs and net sheets are complex; 45-second explainers help agents forward your brand, not a PDF alone.\n\nWe engineer from screen recordings you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "ltic batch 5 peers",
            "Hi Melody,\n\nOther ltic.com contacts may have seen prior notes; yours is account-manager relationship growth.\n\nOpen to an agent-education kit outline?",
        ],
    ],
    "kevin@gtprop.com": [
        [
            "Owner $1.19B GT",
            "Hi Kevin,\n\nYou owner broker at Goodwin and Thyne where gtprop.com cites $1.19B in sales, 1,409 transactions, and a wall of testimonials naming you by name.\n\nOwners set the media bar for every agent on the roster.\n\nWe finish supplied luxury walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Broker attorney team",
            "Hi Kevin,\n\nBroker-attorney integration with the Law Office of John J. Thyne III wins when video matches that credibility.\n\nWe batch hook variants from one shoot day.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Molly Melani separate",
            "Hi Kevin,\n\nMolly and Melani may get parallel notes; yours is owner-led Santa Barbara brand standard.\n\nWant a firm-wide finishing template outline?",
        ],
    ],
    "brian.peitz@ctt.com": [
        [
            "VP Wiresafe Arizona",
            "Hi Brian,\n\nYou VP of sales and marketing at Chicago Title Arizona, where the homepage leads with Wiresafe wire-fraud protection and 13 Maricopa offices.\n\nMarketing leaders scale when every office sends the same fraud-education quality.\n\nWe finish supplied training and partner footage.\n\nWorth a sample?",
        ],
        [
            "inHere platform",
            "Hi Brian,\n\nThe inHere experience platform deserves short cuts agents actually watch before wire instructions go out.\n\nWe engineer retention pacing on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Marc Julie separate",
            "Hi Brian,\n\nMarc and Julie may get escrow and BD notes; yours is firm-wide sales and marketing enablement.\n\nOpen to a Wiresafe reel series outline?",
        ],
    ],
    "mdonahue@atlancoast.com": [
        [
            "Title attorney ACTC",
            "Hi Melissa,\n\nYou title attorney at Atlantic Coast Title; a site review says staff made refinancing paperwork understandable for clients since 1998.\n\nAttorney-led explainers should look as calm as that testimonial.\n\nWe finish supplied client and lender footage.\n\nWorth a sample?",
        ],
        [
            "Simple Title same team",
            "Hi Melissa,\n\nThe Simple Title rebrand promises the same attorneys; your video should reinforce that continuity for lenders.\n\nPost-production on footage you supply.\n\nUseful?",
        ],
        [
            "Andrew staff separate",
            "Hi Melissa,\n\nAndrew may get staff-attorney notes; yours is title counsel at the closing table.\n\nWant a refinance explainer outline?",
        ],
    ],
    "cindy@metrorealtycorp.com": [
        [
            "John G Metro review",
            "Hi Cindy,\n\nMetro's site quotes John G: you and Adam Umina helped them buy a first home and rent a unit rapidly in a seamless process.\n\nThat paired testimonial is strong sales-associate media fuel.\n\nWe polish supplied tour footage.\n\nWorth a sample?",
        ],
        [
            "Sales associate scale",
            "Hi Cindy,\n\n25,000 clients served and 5,000+ rentals mean agents win with consistent reel quality, not one-off phone edits.\n\nWe batch shorts from one walkthrough you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Adam owner angle",
            "Hi Cindy,\n\nAdam may get president notes; yours is the John G buy-and-rent success story.\n\nOpen to a sales-associate reel spec?",
        ],
    ],
    "ksullivan@atlancoast.com": [
        [
            "ARM closing agent",
            "Hi Kelly,\n\nYou account relationship manager and closing agent at Atlantic Coast; a purchase review praises knowledgeable, friendly, timely communications through closing.\n\nClosers are the face of trust at the table.\n\nWe finish supplied consumer explainers.\n\nWorth a sample?",
        ],
        [
            "Maine NH coverage",
            "Hi Kelly,\n\nResidential and commercial coverage across Maine and New Hampshire fits modular partner clips from one shoot.\n\nWe handle grade and captions on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "ACTC five contacts",
            "Hi Kelly,\n\nWe can align one Atlantic Coast template so Erin and Dawna do not get conflicting pitches.\n\nWant a closer-led buyer guide outline?",
        ],
    ],
    "jflowers@lawyersrealtypa.com": [
        [
            "jharmanthehomegirl",
            "Hi Jordan,\n\nYou licensed agent at Lawyers Realty LLC with LinkedIn jharmanthehomegirl and firm Twitter lawyersrealty for the Harrisburg-area market.\n\nAgent brands win when listing cuts match attorney-backed brokerage positioning.\n\nWe finish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Mechanicsburg markets",
            "Hi Jordan,\n\nCSV keywords span Camp Hill, Hershey, and Carlisle; suburban inventory needs story-led shorts, not generic templates.\n\nWe batch hooks from one showing you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Mark owner separate",
            "Hi Jordan,\n\nMark may have seen owner notes in a prior batch; yours is agent-level social and listing media.\n\nOpen to a personal brand reel plan?",
        ],
    ],
    "dphillips@atlancoast.com": [
        [
            "Paralegal ACTC 5-star",
            "Hi Dawna,\n\nYou paralegal at Atlantic Coast Title; an industry review on atlancoast.com calls ACTC top of the list for calm, professional 5-star service.\n\nProcessors and paralegals cut repeat calls when wire-fraud clips look credible on mobile.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Simple Title tools",
            "Hi Dawna,\n\nThe rebrand cites smarter closing tools; paralegal-owned explainers should match that upgrade story.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Kelly closer separate",
            "Hi Dawna,\n\nKelly may get closer notes; yours is file-prep and pre-close education.\n\nWant a paralegal-forward fraud clip outline?",
        ],
    ],
    "marco@americanhomelandtitle.com": [
        [
            "Closing agent Cincinnati",
            "Hi Marco,\n\nYou closing agent at American Homeland in Cincinnati; the site publishes Ohio heirship and partition guides for consumers.\n\nClosing agents own table-side trust when complex topics look clear on mobile.\n\nWe finish supplied explainer footage.\n\nWorth a sample?",
        ],
        [
            "AmericanHomelnd social",
            "Hi Marco,\n\nFirm Twitter AmericanHomelnd and Facebook should match the tone of your closing-room presence.\n\nWe engineer short educational cuts from narration you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Mary funder separate",
            "Hi Marco,\n\nMary may have seen funder notes in batch 6; yours is closing-agent consumer education.\n\nOpen to a table-side trust outline?",
        ],
    ],
    "elaplante@atlancoast.com": [
        [
            "Ops HR Simple Title",
            "Hi Erin,\n\nYou director of operations and HR at Atlantic Coast during the Simple Title integration, with the site promising faster processing and smarter tools.\n\nOps leaders scale when onboarding video is identical in every branch.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Same team message",
            "Hi Erin,\n\nSame team, stronger together is the public line; HR should own that story in internal and partner cuts.\n\nWe standardize finishing on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Six ACTC contacts",
            "Hi Erin,\n\nFive colleagues may see role-specific notes; yours is firm-wide ops and compliance enablement.\n\nWant an onboarding reel kit outline?",
        ],
    ],
    "cynthiamaez@gtprop.com": [
        [
            "Realtor Santa Barbara",
            "Hi Cynthia,\n\nYou licensed realtor at Goodwin and Thyne in Santa Barbara, where the site cites $1.19B in sales and world-class performance marketing.\n\nAgents win when listing media matches Kevin's testimonial standard on gtprop.com.\n\nWe finish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Ventura to LA markets",
            "Hi Cynthia,\n\nNeighborhood guides span Ventura, Ojai, and LA counties; one template keeps multi-market inventory consistent.\n\nWe batch shorts from one shoot you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Kevin owner separate",
            "Hi Cynthia,\n\nKevin and Molly may get owner and marketing notes; yours is agent-level listing reels.\n\nOpen to a luxury tour spec?",
        ],
    ],
    "marc.cousins@ctt.com": [
        [
            "Escrow officer Maricopa",
            "Hi Marc,\n\nYou escrow officer at Chicago Title Arizona; recent site testimonials praise teams handling 10-day escrows smoothly under pressure.\n\nEscrow officers need wire-safety clips agents actually forward.\n\nWe finish supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Wiresafe escrow",
            "Hi Marc,\n\nWiresafe positioning on chicagotitlearizona.com should match your table-side explanations.\n\nWe engineer from screen recordings you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Brian VP separate",
            "Hi Marc,\n\nBrian may get marketing notes; yours is escrow-led fraud education.\n\nWant a 10-day escrow story outline?",
        ],
    ],
    "julie.larraza@ctt.com": [
        [
            "BD manager Maricopa",
            "Hi Julie,\n\nYou business development manager at Chicago Title Arizona with 13 offices across Maricopa on chicagotitlearizona.com.\n\nBD wins when builder and agent referral video looks as polished as wire-fraud education.\n\nWe finish supplied partner and event footage.\n\nWorth a sample?",
        ],
        [
            "azchicagotitle Twitter",
            "Hi Julie,\n\nFirm Twitter azchicagotitle and valley testimonials should match the stories you pitch to new partners.\n\nWe batch shorts from one master you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Brian sales separate",
            "Hi Julie,\n\nBrian may get VP sales notes; yours is relationship development across offices.\n\nOpen to a BD partner reel plan?",
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

    (ROOT / "campaigns" / "pilot-20-batch7-research.json").write_text(
        json.dumps(RESEARCH, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "campaigns" / "pilot-20-batch7-copy.json").write_text(
        json.dumps(COPY, indent=2) + "\n", encoding="utf-8"
    )
    print("OK: 60/60 QA passed in draft")
    print(f"research: {len(RESEARCH)} leads")
    print(f"copy: {len(COPY)} leads")


if __name__ == "__main__":
    main()
