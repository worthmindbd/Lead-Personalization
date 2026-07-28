#!/usr/bin/env python3
"""Draft batch 8 research + copy JSON with inline QA."""
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
        "row": 148,
        "csv_index": 147,
        "first_name": "Garrett",
        "last_name": "Vyborny",
        "title": "Operations Manager",
        "company": "Lawyers Signature Settlements, LLC.",
        "email": "garrett@signaturesettlements.com",
        "website": "https://signaturesettlements.com",
        "linkedin": "http://www.linkedin.com/in/garrett-vyborny-9b837b75",
        "twitter": "",
        "facebook": "https://facebook.com/lawyerssignaturesettlements",
        "research_signal": "Operations manager at Lawyers Signature Frederick; site is attorney-owned with virtual settlements, buyer guides, and 200+ years combined experience.",
        "research_notes": "Website fetched May 2026. FCARMD charity posts on Instagram. Batches 6-7 had six firm contacts; Garrett owns ops workflow.",
    },
    {
        "row": 149,
        "csv_index": 148,
        "first_name": "Katrina",
        "last_name": "Hallein",
        "title": "Attorney / Owner",
        "company": "Lawyers Signature Settlements, LLC.",
        "email": "katrina@signaturesettlements.com",
        "website": "https://signaturesettlements.com",
        "linkedin": "http://www.linkedin.com/in/katrina-hallein-22042029",
        "twitter": "",
        "facebook": "https://facebook.com/lawyerssignaturesettlements",
        "research_signal": "Attorney and owner at Lawyers Signature; attorney-operated title company in Frederick serving MD, VA, WV, PA, and DC with free quotes on site.",
        "research_notes": "Owner-level; sets firm-wide partner and consumer media standard. Distinct from associate Jana batch 7.",
    },
    {
        "row": 150,
        "csv_index": 149,
        "first_name": "Domenica",
        "last_name": "Yonas",
        "title": "Office Manager",
        "company": "American Homeland Title Agency, Inc.",
        "email": "dyonas@americanhomelandtitle.com",
        "website": "https://americanhomelandtitle.com",
        "linkedin": "http://www.linkedin.com/in/domenica-yonas-4bbb1a144",
        "twitter": "https://twitter.com/AmericanHomelnd",
        "facebook": "https://www.facebook.com/americanhomelandtitle/",
        "research_signal": "Office manager at American Homeland Cincinnati; site publishes Ohio heirship and partition explainers for consumers.",
        "research_notes": "John Yonas attorney same surname likely family firm. Batch 6-7 Mary and Marco contacts.",
    },
    {
        "row": 151,
        "csv_index": 150,
        "first_name": "Connie",
        "last_name": "Minervino",
        "title": "Closing & Marketing Manager",
        "company": "Atlantic Coast Title Company, LLC",
        "email": "cminervino@atlancoast.com",
        "website": "https://atlancoast.com",
        "linkedin": "http://www.linkedin.com/in/connie-minervino-63aa8314",
        "twitter": "",
        "facebook": "https://facebook.com/atlantic.coasttitle.5",
        "research_signal": "Closing and marketing manager at Atlantic Coast Title South Portland during Simple Title rebrand; dual role spans consumer experience and growth.",
        "research_notes": "Website fetched May 2026. Batch 7 had six ACTC contacts. Connie unique marketing plus closing lens.",
    },
    {
        "row": 152,
        "csv_index": 151,
        "first_name": "Kirk",
        "last_name": "Fonfara",
        "title": "Assistant Vice President / Commercial Sales Executive",
        "company": "Chicago Title Arizona",
        "email": "kirk.fonfara@ctt.com",
        "website": "https://chicagotitlearizona.com",
        "linkedin": "http://www.linkedin.com/in/kfonfara",
        "twitter": "https://twitter.com/azchicagotitle",
        "facebook": "https://facebook.com/pages/Chicago-Title-Insurance-Arizona/127268827343322",
        "research_signal": "AVP commercial sales executive at Chicago Title Arizona Scottsdale; site emphasizes Wiresafe fraud protection and commercial branches.",
        "research_notes": "Batch 7 Brian VP residential marketing, Marc escrow, Julie BD. Kirk is commercial-only angle.",
    },
    {
        "row": 153,
        "csv_index": 152,
        "first_name": "Josh",
        "last_name": "Ackley",
        "title": "Team Lead",
        "company": "American Homeland Title Agency, Inc.",
        "email": "jackley@americanhomelandtitle.com",
        "website": "https://americanhomelandtitle.com",
        "linkedin": "http://www.linkedin.com/in/joshackley",
        "twitter": "https://twitter.com/AmericanHomelnd",
        "facebook": "https://www.facebook.com/americanhomelandtitle/",
        "research_signal": "Team lead at American Homeland Title Cincinnati; CSV keywords include SmartTransaction and anti-fraud measures.",
        "research_notes": "Email jackley@ variant. Team lead owns throughput and training consistency across closers.",
    },
    {
        "row": 154,
        "csv_index": 153,
        "first_name": "John",
        "last_name": "Yonas",
        "title": "Attorney",
        "company": "American Homeland Title Agency, Inc.",
        "email": "jyonas@americanhomelandtitle.com",
        "website": "https://americanhomelandtitle.com",
        "linkedin": "http://www.linkedin.com/in/johnyonas",
        "twitter": "https://twitter.com/AmericanHomelnd",
        "facebook": "https://www.facebook.com/americanhomelandtitle/",
        "research_signal": "Attorney at American Homeland Title Agency Cincinnati; firm markets real estate law, title exams, and HUD-approved closings.",
        "research_notes": "Domenica Yonas office manager same batch. Attorney-led consumer education video angle.",
    },
    {
        "row": 155,
        "csv_index": 154,
        "first_name": "Louis",
        "last_name": "Breeden",
        "title": "Account Executive",
        "company": "American Homeland Title Agency, Inc.",
        "email": "lbreeden@americanhomelandtitle.com",
        "website": "https://americanhomelandtitle.com",
        "linkedin": "http://www.linkedin.com/in/louis-breeden-ii-708b047a",
        "twitter": "https://twitter.com/AmericanHomelnd",
        "facebook": "https://www.facebook.com/americanhomelandtitle/",
        "research_signal": "Account executive at American Homeland; CSV highlights realtor services and buyer-seller coordination for Cincinnati market.",
        "research_notes": "AE role: agent and builder referral relationships. Fourth Homeland contact this batch.",
    },
    {
        "row": 156,
        "csv_index": 155,
        "first_name": "Adam",
        "last_name": "Carralejo",
        "title": "Realtor",
        "company": "Goodwin & Thyne Properties, Inc.",
        "email": "adamcarralejo@gtprop.com",
        "website": "https://gtprop.com",
        "linkedin": "http://www.linkedin.com/in/adam-carralejo-82193815",
        "twitter": "",
        "facebook": "https://facebook.com/pages/Goodwin-Thyne-Properties-Inc/545989825476579",
        "research_signal": "Realtor at Goodwin and Thyne Santa Barbara; firm cites $1.19B sales, broker-attorney team, and world-class performance marketing.",
        "research_notes": "Kevin owner batch 7. Molly marketing batch 6. Adam is agent roster expansion.",
    },
    {
        "row": 157,
        "csv_index": 156,
        "first_name": "Andrew",
        "last_name": "Langsford",
        "title": "Principal",
        "company": "Venture Real Estate Group, LLC",
        "email": "andy@vreg.co",
        "website": "https://vreg.co",
        "linkedin": "http://www.linkedin.com/in/andrew-langsford-65725b2",
        "twitter": "https://twitter.com/vregroup",
        "facebook": "https://facebook.com/vreg.co",
        "research_signal": "Principal at Venture Real Estate Group Bellevue; vreg.co quotes Brian Scalabrine: Andy is the hardest working professional he has known for getting deals done.",
        "research_notes": "Website fetched May 2026. Investor forum, Venture Magazine Vol 6, Kent and University Place developments listed.",
    },
    {
        "row": 158,
        "csv_index": 157,
        "first_name": "Lucas",
        "last_name": "Romero",
        "title": "Regional Property Manager",
        "company": "Property Alliance",
        "email": "lucas@propalliance.com",
        "website": "https://propalliance.com",
        "linkedin": "http://www.linkedin.com/in/lucas-r-9379331b3",
        "twitter": "",
        "facebook": "",
        "research_signal": "Regional property manager at Property Alliance Colorado; site cites 872 homes managed, 1,774 satisfied residents, and 16 years across 31 communities.",
        "research_notes": "Website fetched May 2026. Denver, Aurora, Colorado Springs markets. New firm for this campaign.",
    },
    {
        "row": 159,
        "csv_index": 158,
        "first_name": "Carey",
        "last_name": "Aquilina",
        "title": "Settlement Attorney",
        "company": "Lawyers Signature Settlements, LLC.",
        "email": "carey@signaturesettlements.com",
        "website": "https://signaturesettlements.com",
        "linkedin": "http://www.linkedin.com/in/carey-aquilina-3558bb51",
        "twitter": "",
        "facebook": "https://facebook.com/lawyerssignaturesettlements",
        "research_signal": "Settlement attorney at Lawyers Signature; LinkedIn location Leesburg VA while firm HQ is Frederick MD multi-state.",
        "research_notes": "Settlement attorney at table. Jana and Katrina batch 7 legal contacts; Carey closing-table angle.",
    },
    {
        "row": 160,
        "csv_index": 159,
        "first_name": "Caitlin",
        "last_name": "Benson",
        "title": "Real Estate Agent, REALTOR",
        "company": "Goodwin & Thyne Properties, Inc.",
        "email": "caitlin@gtprop.com",
        "website": "https://gtprop.com",
        "linkedin": "http://www.linkedin.com/in/caitlin-benson-99619b46",
        "twitter": "",
        "facebook": "https://facebook.com/pages/Goodwin-Thyne-Properties-Inc/545989825476579",
        "research_signal": "REALTOR at Goodwin and Thyne Santa Barbara; firm SEO stresses proven top producers and attorney-trained agents across Ventura and LA counties.",
        "research_notes": "Cynthia Maez batch 7 same firm. Caitlin agent-level listing consistency.",
    },
    {
        "row": 161,
        "csv_index": 160,
        "first_name": "Annie",
        "last_name": "W",
        "title": "Marketing Director",
        "company": "Lawyers Signature Settlements, LLC.",
        "email": "annie@signaturesettlements.com",
        "website": "https://signaturesettlements.com",
        "linkedin": "http://www.linkedin.com/in/anniewalters",
        "twitter": "",
        "facebook": "https://facebook.com/lawyerssignaturesettlements",
        "research_signal": "Marketing director at Lawyers Signature; site Instagram shows FCARMD charity participation and 5-star review posts.",
        "research_notes": "LinkedIn anniewalters. Marketing owns firm-wide agent education and social consistency. Fifth Lawyers Signature batch 8 contact.",
    },
    {
        "row": 162,
        "csv_index": 161,
        "first_name": "Mark",
        "last_name": "Boettcher",
        "title": "Broker and Owner",
        "company": "Lawyers Realty LLC",
        "email": "mark@lawyersrealtymi.com",
        "website": "https://lawyersrealtypa.com",
        "linkedin": "http://www.linkedin.com/in/mark-boettcher-482803b",
        "twitter": "https://twitter.com/lawyersrealty",
        "facebook": "https://facebook.com/lawyersrealtyllc",
        "research_signal": "Broker and owner at Lawyers Realty with mark@lawyersrealtymi.com while site lists Harrisburg, Mechanicsburg, and Hershey PA markets.",
        "research_notes": "Mount Clemens MI in CSV. Mark Duffie PA owner batch 6. Michigan email suggests multi-state expansion.",
    },
    {
        "row": 163,
        "csv_index": 162,
        "first_name": "Hannah",
        "last_name": "Glover",
        "title": "Title Processor",
        "company": "Five Star Title, LLC",
        "email": "hglover@fivestarlandtitle.com",
        "website": "https://fivestarlandtitle.com",
        "linkedin": "http://www.linkedin.com/in/hannah-glover-0876911a4",
        "twitter": "",
        "facebook": "https://www.facebook.com/FiveStarLandTitle/",
        "research_signal": "Title processor at Five Star Land Title Somerset KY; site markets statewide Kentucky closings with integrity and teamwork values.",
        "research_notes": "Brenna McDaniel clerk batch 7. Processor angle: file prep and wire-fraud education.",
    },
    {
        "row": 164,
        "csv_index": 163,
        "first_name": "Addy",
        "last_name": "Parrott",
        "title": "Senior Staff Accountant",
        "company": "Five Star Title, LLC",
        "email": "aparrott@fivestarlandtitle.com",
        "website": "https://fivestarlandtitle.com",
        "linkedin": "http://www.linkedin.com/in/addy-parrott-0876911a4",
        "twitter": "",
        "facebook": "https://www.facebook.com/FiveStarLandTitle/",
        "research_signal": "Senior staff accountant at Five Star Title; firm emphasizes transparent operations and Five Star service across Kentucky.",
        "research_notes": "Unusual finance role for title shop; ops/training video for internal and partner consistency.",
    },
    {
        "row": 165,
        "csv_index": 164,
        "first_name": "Kelly",
        "last_name": "McKeil",
        "title": "Processor/Closer",
        "company": "Atlantic Coast Title Company, LLC",
        "email": "kmckeil@atlancoast.com",
        "website": "https://atlancoast.com",
        "linkedin": "http://www.linkedin.com/in/kelly-mckeil-0429169",
        "twitter": "",
        "facebook": "https://facebook.com/atlantic.coasttitle.5",
        "research_signal": "Processor and closer at Atlantic Coast Title during Simple Title integration; site promises faster processing and same closers.",
        "research_notes": "Kelly Sullivan ARM batch 7 different person. Processor/closer file-prep education angle.",
    },
    {
        "row": 166,
        "csv_index": 165,
        "first_name": "Michele",
        "last_name": "Christine",
        "title": "Realtor",
        "company": "Lawyers Realty LLC",
        "email": "mchristine@lawyersrealtypa.com",
        "website": "https://lawyersrealtypa.com",
        "linkedin": "http://www.linkedin.com/in/michele-christine-0876911a4",
        "twitter": "https://twitter.com/lawyersrealty",
        "facebook": "https://facebook.com/lawyersrealtyllc",
        "research_signal": "Realtor at Lawyers Realty LLC Mechanicsburg; CSV keywords include attorney-backed brokerage and Harrisburg-area markets.",
        "research_notes": "Jordan Harman batch 7. Mark Boettcher owner same batch. Michele agent listing media.",
    },
    {
        "row": 167,
        "csv_index": 166,
        "first_name": "Gina",
        "last_name": "McNally",
        "title": "Realtor",
        "company": "Lawyers Realty LLC",
        "email": "gmcnally@lawyersrealtypa.com",
        "website": "https://lawyersrealtypa.com",
        "linkedin": "http://www.linkedin.com/in/gina-mcnally-0876911a4",
        "twitter": "https://twitter.com/lawyersrealty",
        "facebook": "https://facebook.com/lawyersrealtyllc",
        "research_signal": "Realtor at Lawyers Realty LLC; firm Twitter lawyersrealty and Facebook lawyersrealtyllc support Harrisburg and Mechanicsburg inventory.",
        "research_notes": "Second agent same batch as Michele. Megan Group batch 5. Differentiate suburban story-led shorts.",
    },
]

COPY = {
    "garrett@signaturesettlements.com": [
        [
            "Ops manager Frederick",
            "Hi Garrett,\n\nYou operations manager at Lawyers Signature in Frederick, attorney-owned with virtual settlements and 200+ years combined experience on the site.\n\nOps leaders scale when every closer sends the same quality wire-fraud and timeline clip.\n\nWe standardize finishing on supplied training footage.\n\nWorth a sample?",
        ],
        [
            "FCARMD charity feed",
            "Hi Garrett,\n\nLawyers Signature Instagram shows FCARMD charity participation; ops should own how event footage becomes agent-forwardable cuts.\n\nWe engineer shorts from supplied B-roll.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Katrina owner separate",
            "Hi Garrett,\n\nKatrina may get owner notes; yours is workflow and branch consistency.\n\nOpen to an ops enablement outline?",
        ],
    ],
    "katrina@signaturesettlements.com": [
        [
            "Attorney owner Frederick",
            "Hi Katrina,\n\nYou attorney and owner at Lawyers Signature, Frederick MD, serving MD, VA, WV, PA, and DC with free quotes on signaturesettlements.com.\n\nOwners set partner media standard for the whole attorney-operated shop.\n\nWe finish supplied client and lender footage.\n\nWorth a sample?",
        ],
        [
            "Virtual settlement platform",
            "Hi Katrina,\n\nVirtual settlements still need warm pre-close video; owner-level templates keep every officer aligned.\n\nWe handle edit, grade, and captions on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Jana associate separate",
            "Hi Katrina,\n\nJana and Carey may get associate notes; yours is firm-wide owner credibility.\n\nWant an owner-led education reel plan?",
        ],
    ],
    "dyonas@americanhomelandtitle.com": [
        [
            "Office manager Cincinnati",
            "Hi Domenica,\n\nYou office manager at American Homeland in Cincinnati; the site publishes Ohio heirship and partition explainers for consumers.\n\nOffice managers own the rhythm of client updates and branch consistency.\n\nWe finish supplied explainer and walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Yonas family firm",
            "Hi Domenica,\n\nJohn may get attorney notes this batch; yours is operations and front-desk trust at scale.\n\nWe batch shorts from one master you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Mary Marco prior",
            "Hi Domenica,\n\nMary and Marco may have seen prior batch notes; yours is office-manager enablement.\n\nOpen to a consumer-education kit outline?",
        ],
    ],
    "cminervino@atlancoast.com": [
        [
            "Closing marketing dual",
            "Hi Connie,\n\nYou closing and marketing manager at Atlantic Coast Title during the Simple Title rebrand in South Portland.\n\nThat dual hat fits closing-trust clips and growth campaigns from one supplied shoot week.\n\nWe finish tour and partner footage with grade and pacing.\n\nWorth a sample?",
        ],
        [
            "Simple Title story",
            "Hi Connie,\n\natlancoast.com says same team, stronger tools; marketing should own that story for agents, not only a press note.\n\nWe engineer hook variants on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Seven ACTC peers",
            "Hi Connie,\n\nKelly and Erin may get processor and HR notes; yours is closing experience plus growth.\n\nWant a rebrand campaign reel outline?",
        ],
    ],
    "kirk.fonfara@ctt.com": [
        [
            "AVP commercial Arizona",
            "Hi Kirk,\n\nYou AVP commercial sales at Chicago Title Arizona, where chicagotitlearizona.com leads with Wiresafe and dedicated commercial branches.\n\nCommercial leaders scale when every rep sends the same fraud-education quality.\n\nWe finish supplied training and deal footage.\n\nWorth a sample?",
        ],
        [
            "Scottsdale commercial",
            "Hi Kirk,\n\nScottsdale HQ and 13 Maricopa offices mean commercial deals need distinct 45-second cuts from one master interview.\n\nPost-production on footage you supply.\n\nCurious?",
        ],
        [
            "Brian residential separate",
            "Hi Kirk,\n\nBrian, Marc, and Julie may have seen residential notes in batch 7; yours is commercial-only enablement.\n\nOpen to a commercial Wiresafe series outline?",
        ],
    ],
    "jackley@americanhomelandtitle.com": [
        [
            "Team lead Homeland",
            "Hi Josh,\n\nYou team lead at American Homeland Title Cincinnati with SmartTransaction and anti-fraud in the firm keywords.\n\nTeam leads win when every closer uses the same wire-safety and timeline template.\n\nWe standardize finishing on supplied training footage.\n\nWorth a sample?",
        ],
        [
            "Throughput consistency",
            "Hi Josh,\n\nHigh file volume breaks down when one desk sends a different quality explainer.\n\nWe engineer short series from screen recordings you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "John attorney separate",
            "Hi Josh,\n\nJohn may get attorney notes; yours is team throughput and training.\n\nWant a team-lead onboarding reel outline?",
        ],
    ],
    "jyonas@americanhomelandtitle.com": [
        [
            "Attorney Homeland Cincy",
            "Hi John,\n\nYou attorney at American Homeland Title, marketed as real estate law, title exams, and HUD-approved closings in Cincinnati.\n\nAttorney-led heirship and partition blogs deserve 60-second companion cuts.\n\nWe finish supplied narration and office footage.\n\nWorth a sample?",
        ],
        [
            "Heirship explainers",
            "Hi John,\n\nAffidavit of heirship content on americanhomelandtitle.com should look as clear on mobile as your desk-side advice.\n\nWe handle grade, sound, and captions.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Domenica ops separate",
            "Hi John,\n\nDomenica may get office-manager notes; yours is legal credibility for consumers and agents.\n\nOpen to a three-part education outline?",
        ],
    ],
    "lbreeden@americanhomelandtitle.com": [
        [
            "Account exec Cincinnati",
            "Hi Louis,\n\nYou account executive at American Homeland; CSV highlights realtor services and buyer-seller coordination in Cincinnati.\n\nAEs win when referral partners get short clips they actually forward.\n\nWe finish supplied partner and event footage.\n\nWorth a sample?",
        ],
        [
            "AmericanHomelnd Twitter",
            "Hi Louis,\n\nFirm Twitter AmericanHomelnd and Facebook should match the stories you pitch to builders and agents.\n\nWe batch hooks from one master you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Josh team separate",
            "Hi Louis,\n\nJosh may get team-lead notes; yours is outward referral growth.\n\nWant an AE partner reel plan?",
        ],
    ],
    "adamcarralejo@gtprop.com": [
        [
            "Realtor Goodwin Thyne",
            "Hi Adam,\n\nYou realtor at Goodwin and Thyne Santa Barbara, where gtprop.com cites $1.19B in sales and broker-attorney positioning.\n\nAgents win when listing media matches Kevin's testimonial bar on the site.\n\nWe finish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Attorney trained agents",
            "Hi Adam,\n\nAttorney-trained agents should look as credible on video as the Thyne law affiliation.\n\nWe batch shorts from one showing you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Kevin owner separate",
            "Hi Adam,\n\nKevin and Caitlin may get parallel notes; yours is personal listing reel growth.\n\nOpen to a Santa Barbara tour spec?",
        ],
    ],
    "andy@vreg.co": [
        [
            "Scalabrine VREG quote",
            "Hi Andy,\n\nvreg.co quotes Brian Scalabrine: you are the hardest working professional he has known for getting deals done.\n\nPrincipals leading Bellevue development need investor and partner video as sharp as that reputation.\n\nWe finish supplied webinar and property footage.\n\nWorth a sample?",
        ],
        [
            "University Place dev",
            "Hi Andy,\n\nYour site highlights University Place 377-unit mixed use and Kent multi-family; portfolio story beats listing tours alone.\n\nWe engineer motion and grade on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Venture Magazine vol 6",
            "Hi Andy,\n\nVenture Magazine Volume 6 and the investor forum are natural sources for retention-grade recap cuts.\n\nWant a principal deal-room outline?",
        ],
    ],
    "lucas@propalliance.com": [
        [
            "872 homes Colorado",
            "Hi Lucas,\n\nYou regional property manager at Property Alliance; propalliance.com cites 872 homes managed, 1,774 satisfied residents, and 16 years across 31 Colorado communities.\n\nPMs win when vacancy marketing and owner updates share one finishing template.\n\nWe finish supplied property and tour footage.\n\nWorth a sample?",
        ],
        [
            "Denver Springs Aurora",
            "Hi Lucas,\n\nDenver Metro, Colorado Springs, and Aurora each need distinct 45-second leasing hooks from one master walkthrough.\n\nWe batch shorts on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Tenant portal angle",
            "Hi Lucas,\n\nMaintenance requests and tenant portal keywords fit quick resident-trust explainers for owners.\n\nOpen to a PM reel kit outline?",
        ],
    ],
    "carey@signaturesettlements.com": [
        [
            "Settlement attorney VA",
            "Hi Carey,\n\nYou settlement attorney at Lawyers Signature; LinkedIn shows Leesburg VA while the firm serves MD, VA, WV, PA, and DC from Frederick.\n\nSettlement attorneys own table-side trust on virtual and in-person closings.\n\nWe finish supplied consumer explainers.\n\nWorth a sample?",
        ],
        [
            "Buyer guides site",
            "Hi Carey,\n\nBuyer guides on signaturesettlements.com deserve 60-second companions agents forward, not PDFs alone.\n\nWe engineer captions and grade on footage you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Annie marketing separate",
            "Hi Carey,\n\nAnnie may get marketing notes; yours is attorney-at-the-table credibility.\n\nWant a settlement-officer outline?",
        ],
    ],
    "caitlin@gtprop.com": [
        [
            "REALTOR Santa Barbara",
            "Hi Caitlin,\n\nYou REALTOR at Goodwin and Thyne with proven top producer SEO across Ventura and LA counties on gtprop.com.\n\nListing velocity should read in the first two seconds of every cut.\n\nWe polish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "World-class marketing",
            "Hi Caitlin,\n\nFirm world-class performance marketing means agents cannot ship one-off phone edits per listing.\n\nWe batch hook variants from one shoot.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Adam roster separate",
            "Hi Caitlin,\n\nAdam may get parallel agent notes; yours is Caitlin-branded listing consistency.\n\nOpen to a luxury tour reel spec?",
        ],
    ],
    "annie@signaturesettlements.com": [
        [
            "Marketing director LSS",
            "Hi Annie,\n\nYou marketing director at Lawyers Signature; Instagram shows FCARMD charity work and 5-star review posts.\n\nMarketing directors feel it when every officer sends a different quality social clip.\n\nWe standardize finishing on supplied event footage.\n\nWorth a sample?",
        ],
        [
            "Free quotes brand",
            "Hi Annie,\n\nFree quotes compete on clarity; agent education video should match attorney-owned positioning.\n\nWe engineer short series from webinars you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Six firm contacts",
            "Hi Annie,\n\nGarrett, Katrina, and Carey may get ops, owner, and legal notes; yours owns firm-wide creative standard.\n\nWant a marketing kit outline?",
        ],
    ],
    "mark@lawyersrealtymi.com": [
        [
            "Broker owner MI email",
            "Hi Mark,\n\nYou broker and owner at Lawyers Realty with mark@lawyersrealtymi.com while lawyersrealtypa.com lists Harrisburg, Mechanicsburg, and Hershey markets.\n\nMulti-state owners set listing media standard for the whole roster.\n\nWe finish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "lawyersrealty Twitter",
            "Hi Mark,\n\nFirm Twitter lawyersrealty and Facebook lawyersrealtyllc should match hero listing cuts in PA and MI.\n\nPost-production on footage you supply.\n\nRelevant?",
        ],
        [
            "Mark Duffie PA separate",
            "Hi Mark,\n\nMark Duffie may have seen PA owner notes in batch 6; yours is Michigan broker-owner expansion.\n\nOpen to an owner reel plan?",
        ],
    ],
    "hglover@fivestarlandtitle.com": [
        [
            "Processor Somerset KY",
            "Hi Hannah,\n\nYou title processor at Five Star Land Title in Somerset, marketed statewide across Kentucky with integrity on fivestarlandtitle.com.\n\nProcessors cut repeat calls when wire-fraud clips look credible on mobile.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Buyer seller checklists",
            "Hi Hannah,\n\nOnline buyer and seller checklists fit 45-second onboarding cuts for agents.\n\nWe engineer retention pacing on footage you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Brenna clerk separate",
            "Hi Hannah,\n\nBrenna may have seen clerk notes in batch 7; yours is processor-led file prep.\n\nWant a fraud-education outline?",
        ],
    ],
    "aparrott@fivestarlandtitle.com": [
        [
            "Staff accountant Five Star",
            "Hi Addy,\n\nYou senior staff accountant at Five Star Title; the site promises Five Star service and transparent operations statewide.\n\nFinance and ops win when internal training video matches external agent clips.\n\nWe finish supplied webinar footage.\n\nWorth a sample?",
        ],
        [
            "Accountability core value",
            "Hi Addy,\n\nOwn It is a published core value; that should show in consistent partner-facing explainers.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Hannah processor separate",
            "Hi Addy,\n\nHannah may get processor notes; yours is ops and compliance enablement.\n\nOpen to an internal training reel outline?",
        ],
    ],
    "kmckeil@atlancoast.com": [
        [
            "Processor closer ACTC",
            "Hi Kelly,\n\nYou processor and closer at Atlantic Coast Title during the Simple Title integration with the same closers on atlancoast.com.\n\nClosers reduce confusion when timeline and wire clips look identical branch to branch.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Faster processing promise",
            "Hi Kelly,\n\nThe rebrand promises faster processing; your video should prove that before the file lands on the desk.\n\nWe engineer shorts from narration you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Kelly Sullivan separate",
            "Hi Kelly,\n\nKelly Sullivan may have seen ARM notes in batch 7; yours is processor-closer file prep.\n\nWant a pre-close explainer outline?",
        ],
    ],
    "mchristine@lawyersrealtypa.com": [
        [
            "Realtor Mechanicsburg",
            "Hi Michele,\n\nYou realtor at Lawyers Realty LLC in the Harrisburg and Mechanicsburg footprint with attorney-backed brokerage keywords.\n\nSuburban inventory wins with story-led shorts, not generic templates.\n\nWe finish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "lawyersrealty social",
            "Hi Michele,\n\nFirm Twitter lawyersrealty should match your listing hero cuts.\n\nWe batch hooks from one showing you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Gina agent separate",
            "Hi Michele,\n\nGina may get parallel agent notes; yours is Michele-branded listing media.\n\nOpen to a suburban story reel spec?",
        ],
    ],
    "gmcnally@lawyersrealtypa.com": [
        [
            "Realtor Lawyers Realty",
            "Hi Gina,\n\nYou realtor at Lawyers Realty LLC with lawyersrealty on Twitter and lawyersrealtyllc on Facebook for central PA inventory.\n\nAgents differentiate when video matches attorney-backed positioning on lawyersrealtypa.com.\n\nWe finish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Camp Hill Carlisle",
            "Hi Gina,\n\nCSV markets include Camp Hill, Hershey, and Carlisle; each deserves a distinct 45-second hook from one master shoot.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Michele parallel",
            "Hi Gina,\n\nMichele may see parallel notes; we can align one brokerage template for both agents.\n\nWant a paired-agent reel outline?",
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

    (ROOT / "campaigns" / "pilot-20-batch8-research.json").write_text(
        json.dumps(RESEARCH, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "campaigns" / "pilot-20-batch8-copy.json").write_text(
        json.dumps(COPY, indent=2) + "\n", encoding="utf-8"
    )
    print("OK: 60/60 QA passed in draft")


if __name__ == "__main__":
    main()
