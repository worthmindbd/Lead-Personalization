#!/usr/bin/env python3
"""Draft and QA-check batch 15 research + copy."""

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
        "csv_index": 287,
        "first_name": "Angela",
        "last_name": "Mitchell",
        "title": "Realtor",
        "company": "Stephen Cooley Real Estate",
        "email": "angie@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/angela-mitchell-34a03530",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Realtor at Stephen Cooley Fort Mill SC; stephencooley.com promotes team selling at highest possible price with CooleyTeam social active on Twitter and Facebook.",
        "research_notes": "Fort Mill desk. Angela vs Angie email. Batch 13-14 had 16 Cooley contacts; differentiate on city and CooleyTeam social.",
    },
    {
        "csv_index": 288,
        "first_name": "Audrey",
        "last_name": "Fulp",
        "title": "Real Estate Agent",
        "company": "Stephen Cooley Real Estate",
        "email": "audrey@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/audrey-fulp-878a43ba",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Agent at Stephen Cooley based in Nashville TN; firm's Charlotte-to-Rock Hill footprint on stephencooley.com with cash-offer and instant-value funnels.",
        "research_notes": "Nashville agent with SC firm is unusual; remote or relocation specialist angle.",
    },
    {
        "csv_index": 289,
        "first_name": "Meg",
        "last_name": "Czaikowski",
        "title": "Realtor",
        "company": "Stephen Cooley Real Estate",
        "email": "meg@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/meg-czaikowski-22644a12",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Realtor at Stephen Cooley York SC; firm neighborhood guides include Lake Wylie and Clover adjacent to York County.",
        "research_notes": "York SC desk. Sharon Clover batch 13.",
    },
    {
        "csv_index": 290,
        "first_name": "Jerri-Lynn",
        "last_name": "Newell",
        "title": "Real Estate Broker",
        "company": "Stephen Cooley Real Estate",
        "email": "jerri-lynn@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/jerri-lynn-newell-a7190022a",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Real estate broker at Stephen Cooley Huntersville NC; firm's Huntersville neighborhood guide sits in the Lake Norman corridor.",
        "research_notes": "Huntersville broker. Lake Norman market. Kellee Wilson batch 14 broker different market.",
    },
    {
        "csv_index": 291,
        "first_name": "Dawn",
        "last_name": "Gilliam",
        "title": "Real Estate Agent",
        "company": "Stephen Cooley Real Estate",
        "email": "dawn@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/dawn-gilliam-934b4348",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Agent at Stephen Cooley Charlotte NC; firm maps Ballantyne and Waxhaw as buyer destinations with negotiating and investing keywords.",
        "research_notes": "Charlotte agent. Kim Johnson batch 14 same market.",
    },
    {
        "csv_index": 292,
        "first_name": "Leonardy",
        "last_name": "Ortiz",
        "title": "Licensed Real Estate Professional",
        "company": "Red Tree Real Estate",
        "email": "leonardy@redtreeboston.com",
        "website": "https://redtreeboston.com",
        "linkedin": "http://www.linkedin.com/in/leonardy-ortiz-105b40166",
        "twitter": "https://twitter.com/redtreeboston",
        "facebook": "https://www.facebook.com/redtreerealestateboston",
        "research_signal": "Licensed professional at Red Tree Real Estate Brookline; redtreeboston.com team carousel lists Leonardy Ortiz serving Greater Boston since 2013.",
        "research_notes": "Sole Red Tree contact batch 15. Moshe Rosenbloom also Brookline batch 14.",
    },
    {
        "csv_index": 293,
        "first_name": "Dale",
        "last_name": "Loftis",
        "title": "Broker in Charge",
        "company": "Stephen Cooley Real Estate",
        "email": "dale@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/dale-loftis-ab2b924",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Broker in Charge at Stephen Cooley Fort Mill SC; site highlights seasoned negotiation and sell-for-highest-price positioning from Ebenezer Road headquarters.",
        "research_notes": "Broker in Charge is the senior compliance and oversight role. Dale Loftis; Sarah Loftis batch 13 Charlotte realtor, different person.",
    },
    {
        "csv_index": 294,
        "first_name": "Josh",
        "last_name": "Smith",
        "title": "ISA",
        "company": "Stephen Cooley Real Estate",
        "email": "josh.smith@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/joshsmithsc",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Inside Sales Agent at Stephen Cooley Rock Hill; ISAs handle inbound leads from instant-value and cash-offer funnels on stephencooley.com.",
        "research_notes": "ISA role is lead-qualification, not listing. Video pitch angle for inbound follow-up clips.",
    },
    {
        "csv_index": 295,
        "first_name": "Joanna",
        "last_name": "Barella",
        "title": "Sr Property Manager",
        "company": "Premier Property Solutions",
        "email": "jb@premierpropertyma.com",
        "website": "https://premierpropertyma.com",
        "linkedin": "http://www.linkedin.com/in/joanna-barella-435789a1",
        "twitter": "https://twitter.com/PremierPropMA",
        "facebook": "https://www.facebook.com/PremierPropertySolutionsMA",
        "research_signal": "Senior property manager at Premier Property Solutions Somerville MA; premierpropertyma.com now serves Western MA from West Springfield alongside Boston.",
        "research_notes": "Somerville desk. Stephanie Capriulo batch 13 same firm. Joanna is fourth Premier contact.",
    },
    {
        "csv_index": 296,
        "first_name": "Debra",
        "last_name": "Best",
        "title": "Realtor",
        "company": "Stephen Cooley Real Estate",
        "email": "dbest@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/debra-best-5849b451",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Realtor at Stephen Cooley Rock Hill; firm's highest-price selling and negotiation keywords match buyer and seller listing media needs.",
        "research_notes": "Rock Hill realtor. Differentiate from Sherry, Amanda, Jackson Rock Hill.",
    },
    {
        "csv_index": 297,
        "first_name": "Eric",
        "last_name": "Mann",
        "title": "Realtor",
        "company": "Stephen Cooley Real Estate",
        "email": "eric@stephencooley.com",
        "website": "https://stephencooley.com",
        "linkedin": "http://www.linkedin.com/in/eric-mann-177877330",
        "twitter": "https://twitter.com/CooleyTeam",
        "facebook": "https://facebook.com/TheStephenCooleyTeam",
        "research_signal": "Realtor at Stephen Cooley Fort Mill SC; CooleyTeam social and cash-offer funnels support agent-led seller outreach.",
        "research_notes": "Fort Mill realtor. Eric Mann distinct from Eric Anderson Red Tree batch 14.",
    },
    {
        "csv_index": 298,
        "first_name": "Barri",
        "last_name": "Finlay",
        "title": "Title Processor",
        "company": "KVS TITLE",
        "email": "barri@kvstitle.com",
        "website": "https://kvstitle.com",
        "linkedin": "http://www.linkedin.com/in/barri-wood-finlay-b939716",
        "twitter": "",
        "facebook": "https://facebook.com/KVSTitle/",
        "research_signal": "Title processor at KVS Title Baltimore; kvstitle.com highlights 70,000+ settlements, attorney-staffed offices, and half-competitor caseloads for proactive client communication.",
        "research_notes": "Nine KVS contacts batch 15. First KVS cluster in campaign. Processor handles file prep before settlement.",
    },
    {
        "csv_index": 299,
        "first_name": "Camille",
        "last_name": "Wagner",
        "title": "Settlement Processor",
        "company": "KVS TITLE",
        "email": "cwagner@kvstitle.com",
        "website": "https://kvstitle.com",
        "linkedin": "http://www.linkedin.com/in/wagner-camille-b91777157",
        "twitter": "",
        "facebook": "https://facebook.com/KVSTitle/",
        "research_signal": "Settlement processor at KVS Title Kensington MD; firm promises proactive communication and twice-the-attention staffing with 7 MD/DC/VA offices.",
        "research_notes": "First name Camille per LinkedIn; CSV lists Wagner first. Processor angle same as Barri.",
    },
    {
        "csv_index": 300,
        "first_name": "Suzanne",
        "last_name": "Feinstein",
        "title": "Settlement Attorney",
        "company": "KVS TITLE",
        "email": "suzanne@kvstitle.com",
        "website": "https://kvstitle.com",
        "linkedin": "http://www.linkedin.com/in/suzanne-feinstein-a095721b",
        "twitter": "",
        "facebook": "https://facebook.com/KVSTitle/",
        "research_signal": "Settlement attorney at KVS Title Rockville MD; site cites attorneys averaging 14+ years experience and 70,000+ combined settlements.",
        "research_notes": "Attorney role distinct from processor. Client trust and education angle.",
    },
    {
        "csv_index": 301,
        "first_name": "Michelle",
        "last_name": "Mantilla",
        "title": "Settlement Processor",
        "company": "KVS TITLE",
        "email": "mmantilla@kvstitle.com",
        "website": "https://kvstitle.com",
        "linkedin": "http://www.linkedin.com/in/michellemantilla",
        "twitter": "",
        "facebook": "https://facebook.com/KVSTitle/",
        "research_signal": "Settlement processor at KVS Title Bethesda MD; firm's half-competitor caseload model means processors have more time for each file.",
        "research_notes": "Bethesda office. Differentiate from Barri Baltimore and Camille Kensington processor.",
    },
    {
        "csv_index": 302,
        "first_name": "Peter",
        "last_name": "Parente",
        "title": "Account Executive",
        "company": "KVS TITLE",
        "email": "pparente@kvstitle.com",
        "website": "https://kvstitle.com",
        "linkedin": "http://www.linkedin.com/in/peterparente",
        "twitter": "",
        "facebook": "https://facebook.com/KVSTitle/",
        "research_signal": "Account executive at KVS Title Washington DC; firm testimonial from Hans Wydler cites 500M career sales and decade-long partnership with KVS.",
        "research_notes": "AE in DC market. Partner relationship media angle. Facebook KVSTitle active.",
    },
    {
        "csv_index": 303,
        "first_name": "Noah",
        "last_name": "Cantor",
        "title": "Attorney",
        "company": "KVS TITLE",
        "email": "noah@kvstitle.com",
        "website": "https://kvstitle.com",
        "linkedin": "http://www.linkedin.com/in/noah-cantor-83015b43",
        "twitter": "",
        "facebook": "https://facebook.com/KVSTitle/",
        "research_signal": "Attorney at KVS Title Chevy Chase MD; firm's 70,000+ settlements and proactive communication standard rely on attorney-led closings.",
        "research_notes": "Chevy Chase office. Suzanne attorney same firm different location.",
    },
    {
        "csv_index": 304,
        "first_name": "Rikki",
        "last_name": "Woodall",
        "title": "Settlement Coordinator",
        "company": "KVS TITLE",
        "email": "rikki@kvstitle.com",
        "website": "https://kvstitle.com",
        "linkedin": "http://www.linkedin.com/in/rikki-woodall-2b17a6a7",
        "twitter": "",
        "facebook": "https://facebook.com/KVSTitle/",
        "research_signal": "Settlement coordinator at KVS Title Baltimore; firm's 7-office footprint means coordinators manage agent and lender communication across MD/DC/VA markets.",
        "research_notes": "Coordinator role owns scheduling and communication across parties.",
    },
    {
        "csv_index": 305,
        "first_name": "Norbert",
        "last_name": "Kupinski",
        "title": "Settlement Coordinator",
        "company": "KVS TITLE",
        "email": "nkupinski@kvstitle.com",
        "website": "https://kvstitle.com",
        "linkedin": "http://www.linkedin.com/in/norbert-w-kupinski-iii-3140047",
        "twitter": "",
        "facebook": "https://facebook.com/KVSTitle/",
        "research_signal": "Settlement coordinator at KVS Title; firm's proactive communication model positions coordinators as the primary point of contact through the closing process.",
        "research_notes": "No city in CSV. LinkedIn slug norbert-w-kupinski-iii. Differentiate from Rikki coordinator.",
    },
    {
        "csv_index": 306,
        "first_name": "Wendy",
        "last_name": "Silverman",
        "title": "Director",
        "company": "KVS TITLE",
        "email": "wendy@kvstitle.com",
        "website": "https://kvstitle.com",
        "linkedin": "http://www.linkedin.com/in/wendy-silverman-543b8a90",
        "twitter": "",
        "facebook": "https://facebook.com/KVSTitle/",
        "research_signal": "Director at KVS Title Gaithersburg MD; firm leads MD/DC/VA with seamless flawless closing promise and seven strategically located offices.",
        "research_notes": "Director sets firm brand standard. Facebook KVSTitle active.",
    },
]

COPY = {
    "angie@stephencooley.com": [
        [
            "Realtor Fort Mill Cooley",
            "Hi Angela,\n\nYou realtor at Stephen Cooley Fort Mill where the team sells for highest possible price and CooleyTeam stays active on social.\n\nFort Mill agents win when listing reels feel as polished as the brand's cash-offer landing pages.\n\nWe polish supplied tour footage.\n\nWorth a sample?",
        ],
        [
            "CooleyTeam social shorts",
            "Hi Angela,\n\nCooleyTeam Twitter needs listing cuts agents actually post, not raw walkthrough files.\n\nWe batch hooks from footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Julie Fort Mill separate",
            "Hi Angela,\n\nJulie Gaines may have seen Fort Mill notes in batch 14; yours is Angela-led listing media.\n\nOpen to a seller reel spec?",
        ],
    ],
    "audrey@stephencooley.com": [
        [
            "Nashville agent Cooley",
            "Hi Audrey,\n\nYou agent at Stephen Cooley based in Nashville, bridging the team's Charlotte and Rock Hill footprint on stephencooley.com.\n\nRelocation buyers decide on video before they schedule a showing.\n\nWe polish supplied property footage.\n\nWorth a sample?",
        ],
        [
            "Remote relocation reels",
            "Hi Audrey,\n\nNashville-to-Charlotte movers need visual proof of neighborhood and lifestyle before flying out.\n\nWe engineer retention pacing on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Cooley team standard",
            "Hi Audrey,\n\nThe Cooley team brand should look consistent whether you list in Tennessee or South Carolina.\n\nWant a remote-agent reel outline?",
        ],
    ],
    "meg@stephencooley.com": [
        [
            "Realtor York SC Cooley",
            "Hi Meg,\n\nYou realtor at Stephen Cooley York SC near Lake Wylie and Clover markets on stephencooley.com.\n\nYork listings need hooks that surface lake access and commute time in three seconds.\n\nWe polish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "York County buyers",
            "Hi Meg,\n\nYork County buyers compare neighborhoods visually before they call; listing reels should lead with what makes each pocket different.\n\nWe batch variants from one shoot you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Alex Mooresville separate",
            "Hi Meg,\n\nAlex Porfiris may have seen lake-market notes in batch 14; yours is Meg-led York County media.\n\nWant a neighborhood reel plan?",
        ],
    ],
    "jerri-lynn@stephencooley.com": [
        [
            "Broker Huntersville Cooley",
            "Hi Jerri-Lynn,\n\nYou real estate broker at Stephen Cooley Huntersville in the Lake Norman corridor with team negotiation keywords on stephencooley.com.\n\nBrokers set whether agent listing reels match the buy-for-highest-price brand.\n\nWe polish supplied tour footage.\n\nWorth a sample?",
        ],
        [
            "Lake Norman market",
            "Hi Jerri-Lynn,\n\nLake Norman waterfront listings need production-grade pacing, not unedited drone loops.\n\nWe engineer hooks on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Kellee broker separate",
            "Hi Jerri-Lynn,\n\nKellee Wilson may have seen broker notes in batch 14; yours is Jerri-Lynn-led Huntersville standards.\n\nOpen to a Lake Norman reel spec?",
        ],
    ],
    "dawn@stephencooley.com": [
        [
            "Charlotte agent Cooley",
            "Hi Dawn,\n\nYou agent at Stephen Cooley Charlotte with Ballantyne and Waxhaw neighborhood guides on the team site.\n\nCharlotte agents compete on first impressions; hooks should show price and location in three seconds.\n\nWe polish supplied listing footage.\n\nWorth a sample?",
        ],
        [
            "Waxhaw buyer hooks",
            "Hi Dawn,\n\nWaxhaw and Ballantyne buyers filter on lifestyle; one master tour should become distinct cuts per neighborhood.\n\nWe batch variants from footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Kim Charlotte separate",
            "Hi Dawn,\n\nKim Johnson may have seen Charlotte realtor notes in batch 14; yours is Dawn-led Charlotte listing media.\n\nWant an agent reel outline?",
        ],
    ],
    "leonardy@redtreeboston.com": [
        [
            "Brookline Red Tree",
            "Hi Leonardy,\n\nYou licensed professional at Red Tree Brookline where redtreeboston.com has served Greater Boston since 2013 and plants two trees per transaction.\n\nBrookline listings need hooks that match the premium brand Adam and Denis built.\n\nWe polish supplied tour footage.\n\nWorth a sample?",
        ],
        [
            "Team brand consistency",
            "Hi Leonardy,\n\nEvery agent on the Red Tree carousel should share one finishing standard, not forty different edit styles.\n\nWe batch cuts from footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Moshe Brookline separate",
            "Hi Leonardy,\n\nMoshe Rosenbloom may have seen Brookline notes in batch 14; yours is Leonardy-led listing media.\n\nOpen to an agent reel spec?",
        ],
    ],
    "dale@stephencooley.com": [
        [
            "Broker in Charge Cooley",
            "Hi Dale,\n\nYou broker in charge at Stephen Cooley Fort Mill where the firm sells for highest price and has moved through CooleyTeam social with cash-offer funnels.\n\nBrokers in charge set compliance and quality across every agent desk.\n\nWe finish supplied team and listing footage.\n\nWorth a sample?",
        ],
        [
            "Agent media standard",
            "Hi Dale,\n\nBroker-in-charge authority compounds when every agent listing reel matches the firm brand, not desk-by-desk styles.\n\nWe standardize on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Kellee broker separate",
            "Hi Dale,\n\nKellee Wilson may have seen NC/SC broker notes in batch 14; yours is Dale-led compliance and brand oversight.\n\nWant a broker-in-charge enablement outline?",
        ],
    ],
    "josh.smith@stephencooley.com": [
        [
            "ISA Rock Hill Cooley",
            "Hi Josh,\n\nYou inside sales agent at Stephen Cooley Rock Hill handling inbound leads from instant-value and cash-offer funnels on stephencooley.com.\n\nISAs convert faster when follow-up clips explain next steps in under forty-five seconds.\n\nWe polish supplied explainer footage.\n\nWorth a sample?",
        ],
        [
            "Inbound follow-up video",
            "Hi Josh,\n\nInstant-value leads go cold quickly; a short video follow-up can hold attention until the consult.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Jackson agent separate",
            "Hi Josh,\n\nJackson Burns may have seen Rock Hill agent notes in batch 14; yours is Josh-led ISA follow-up media.\n\nOpen to an inbound reel spec?",
        ],
    ],
    "jb@premierpropertyma.com": [
        [
            "Sr PM Somerville Premier",
            "Hi Joanna,\n\nYou senior property manager at Premier Property Solutions Somerville where premierpropertyma.com now serves Western MA alongside Greater Boston.\n\nSenior PMs retain owners when walkthrough updates look as clear as the maintenance logs.\n\nWe finish supplied property footage.\n\nWorth a sample?",
        ],
        [
            "Boston condo updates",
            "Hi Joanna,\n\nTrustees make capital decisions faster with video walkthroughs than written reports alone.\n\nWe polish supplied interior footage with captions and pacing.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Stephanie PM separate",
            "Hi Joanna,\n\nStephanie Capriulo may have seen senior PM notes in batch 13; yours is Joanna-led Somerville owner comms.\n\nWant a trustee update reel outline?",
        ],
    ],
    "dbest@stephencooley.com": [
        [
            "Realtor Rock Hill Best",
            "Hi Debra,\n\nYou realtor at Stephen Cooley Rock Hill with the team's highest-price selling and negotiation positioning on stephencooley.com.\n\nRock Hill agents win when listing hooks feel brokerage-grade, not unedited phone tours.\n\nWe polish supplied walkthrough footage.\n\nWorth a sample?",
        ],
        [
            "Seller negotiation reels",
            "Hi Debra,\n\nNegotiation stories should show in thirty seconds, not get buried in listing descriptions.\n\nWe batch cuts from footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Sherry Rock Hill separate",
            "Hi Debra,\n\nSherry Avant may have seen Rock Hill seller notes in batch 14; yours is Debra-led listing media.\n\nWant an agent reel outline?",
        ],
    ],
    "eric@stephencooley.com": [
        [
            "Fort Mill realtor Mann",
            "Hi Eric,\n\nYou realtor at Stephen Cooley Fort Mill where CooleyTeam social and cash-offer funnels support seller outreach on stephencooley.com.\n\nFort Mill sellers choose agents by what they see on social before they call.\n\nWe polish supplied listing footage.\n\nWorth a sample?",
        ],
        [
            "CooleyTeam content",
            "Hi Eric,\n\nCooleyTeam Facebook and Twitter need forty-five second seller reels agents actually share.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Angela Fort Mill separate",
            "Hi Eric,\n\nAngela Mitchell may get parallel Fort Mill notes; yours is Eric Mann-led seller media.\n\nOpen to a seller reel spec?",
        ],
    ],
    "barri@kvstitle.com": [
        [
            "Title processor KVS",
            "Hi Barri,\n\nYou title processor at KVS Title Baltimore where kvstitle.com cites 70,000+ settlements, attorney staff with 14+ years, and half the competitor caseload per processor.\n\nProcessors cut repeat calls when wire and timeline explainers look identical office to office.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Proactive comms standard",
            "Hi Barri,\n\nKVS promises proactive communication start to finish; short clips should reinforce that before the processor calls.\n\nWe engineer shorts from footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Camille processor separate",
            "Hi Barri,\n\nCamille Wagner may get parallel processor notes; yours is Barri-led Baltimore title media.\n\nWant a processor training reel outline?",
        ],
    ],
    "cwagner@kvstitle.com": [
        [
            "Settlement processor KVS",
            "Hi Camille,\n\nYou settlement processor at KVS Title Kensington MD where the firm promises proactive updates and twice-the-attention staffing across seven MD/DC/VA offices.\n\nProcessors win when timeline and funding clips match the seamless closing promise on kvstitle.com.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Seven offices one voice",
            "Hi Camille,\n\nSeven offices should sound like one firm on video, not seven different training styles.\n\nWe standardize on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Barri Baltimore separate",
            "Hi Camille,\n\nBarri Finlay may get Baltimore processor notes; yours is Camille-led Kensington settlement media.\n\nOpen to a training reel spec?",
        ],
    ],
    "suzanne@kvstitle.com": [
        [
            "Settlement attorney KVS",
            "Hi Suzanne,\n\nYou settlement attorney at KVS Title Rockville where attorneys average 14+ years experience and 70,000+ combined settlements on kvstitle.com.\n\nAttorneys build trust faster when client-education clips arrive before the signing table.\n\nWe finish supplied explainer footage.\n\nWorth a sample?",
        ],
        [
            "Client education video",
            "Hi Suzanne,\n\nAttorney-led closings earn more referrals when what to expect at settlement is explained in sixty seconds.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Noah attorney separate",
            "Hi Suzanne,\n\nNoah Cantor may get Chevy Chase attorney notes; yours is Suzanne-led Rockville client education.\n\nWant a settlement explainer outline?",
        ],
    ],
    "mmantilla@kvstitle.com": [
        [
            "Processor Bethesda KVS",
            "Hi Michelle,\n\nYou settlement processor at KVS Title Bethesda where the firm assigns half the caseload of competitors so processors have more time per file.\n\nBethesda clients expect the same proactive updates kvstitle.com promises.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Half caseload edge",
            "Hi Michelle,\n\nFewer files per processor should show in the video quality agents and lenders see, not just the email response time.\n\nWe polish supplied explainers with motion and captions.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Camille Kensington separate",
            "Hi Michelle,\n\nCamille Wagner may get Kensington notes; yours is Michelle-led Bethesda processor media.\n\nOpen to a workflow video spec?",
        ],
    ],
    "pparente@kvstitle.com": [
        [
            "AE KVS DC market",
            "Hi Peter,\n\nYou account executive at KVS Title Washington DC where kvstitle.com features a Hans Wydler testimonial citing 500M in career sales and a decade-long KVS partnership.\n\nAEs win when referral partners get partner-facing clips they actually forward.\n\nWe finish supplied event and training footage.\n\nWorth a sample?",
        ],
        [
            "Partner referral media",
            "Hi Peter,\n\nHigh-volume brokers trust firms whose video materials match their own production standard.\n\nWe batch hooks from footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Wendy director separate",
            "Hi Peter,\n\nWendy Silverman may get director-level notes; yours is Peter-led DC partner growth.\n\nWant an AE enablement reel outline?",
        ],
    ],
    "noah@kvstitle.com": [
        [
            "Attorney Chevy Chase KVS",
            "Hi Noah,\n\nYou attorney at KVS Title Chevy Chase where the firm's 70,000+ settlements and flawless closing promise rest on attorney-led oversight.\n\nAttorneys lose referrals when client-facing video does not match the firm's proactive communication standard.\n\nWe finish supplied explainer footage.\n\nWorth a sample?",
        ],
        [
            "Flawless closing video",
            "Hi Noah,\n\nSeamless and flawless closing is a brand claim; pre-closing video should make it tangible for buyers.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nRelevant?",
        ],
        [
            "Suzanne attorney separate",
            "Hi Noah,\n\nSuzanne Feinstein may get Rockville attorney notes; yours is Noah-led Chevy Chase client education.\n\nOpen to a settlement walkthrough outline?",
        ],
    ],
    "rikki@kvstitle.com": [
        [
            "Settlement coord Baltimore",
            "Hi Rikki,\n\nYou settlement coordinator at KVS Title Baltimore managing agent and lender communication across seven MD/DC/VA offices on kvstitle.com.\n\nCoordinators cut repeat status calls when timeline clips arrive before the question is asked.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Agent lender comms",
            "Hi Rikki,\n\nAgents and lenders trust coordinators who send clear milestone updates, not just email chains.\n\nWe engineer shorts from narration you supply.\n\nPost-production only.\n\nUseful?",
        ],
        [
            "Norbert coord separate",
            "Hi Rikki,\n\nNorbert Kupinski may get parallel coordinator notes; yours is Rikki-led Baltimore comms media.\n\nWant a coordinator workflow reel spec?",
        ],
    ],
    "nkupinski@kvstitle.com": [
        [
            "Settlement coord KVS",
            "Hi Norbert,\n\nYou settlement coordinator at KVS Title where the firm promises proactive updates from start to finish and half the competitor caseload per staff member.\n\nCoordinators who send video milestone updates reduce call volume and build lasting agent trust.\n\nWe finish supplied screen recordings.\n\nWorth a sample?",
        ],
        [
            "Proactive milestone clips",
            "Hi Norbert,\n\nOne master coordination explainer should become distinct lender and agent cuts with captions.\n\nWe engineer pacing on footage you supply.\n\nPost-production only.\n\nCurious?",
        ],
        [
            "Rikki coordinator separate",
            "Hi Norbert,\n\nRikki Woodall may get Baltimore coordinator notes; yours is Norbert-led settlement comms media.\n\nOpen to a workflow video outline?",
        ],
    ],
    "wendy@kvstitle.com": [
        [
            "Director KVS Gaithersburg",
            "Hi Wendy,\n\nYou director at KVS Title Gaithersburg where kvstitle.com promises seamless flawless closings across seven MD/DC/VA offices with attorney-staffed teams.\n\nDirectors set whether every office sends the same partner and client video standard.\n\nWe finish supplied leadership and training footage.\n\nWorth a sample?",
        ],
        [
            "Seven office standard",
            "Hi Wendy,\n\nSeven offices only feel like one firm on video when finishing is centralized, not desk-by-desk.\n\nWe standardize on footage you supply.\n\nPost-production only.\n\nOn your radar?",
        ],
        [
            "Peter AE separate",
            "Hi Wendy,\n\nPeter Parente may get DC AE notes; yours is Wendy-led director brand standard.\n\nWant a firm-wide reel plan?",
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

    if len(COPY) != 20:
        raise SystemExit(f"copy count {len(COPY)}, need 20")
    if len(research_out) != 20:
        raise SystemExit(f"research count {len(research_out)}, need 20")

    emails_r = {r["email"].lower() for r in research_out}
    if emails_r != set(COPY.keys()):
        raise SystemExit(f"email mismatch: {emails_r ^ set(COPY.keys())}")

    (ROOT / "campaigns" / "pilot-20-batch15-research.json").write_text(
        json.dumps(research_out, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "campaigns" / "pilot-20-batch15-copy.json").write_text(
        json.dumps(COPY, indent=2) + "\n", encoding="utf-8"
    )
    print("OK: 20 leads, 60 emails, QA pre-check passed")


if __name__ == "__main__":
    main()
