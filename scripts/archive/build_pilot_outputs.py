#!/usr/bin/env python3
"""Build pilot-20 enriched CSV, markdown review, and JSON from research + copy."""

import csv
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = json.loads((ROOT / "campaigns" / "pilot-20-research.json").read_text())
SOURCE_CSV = ROOT / "leads" / "Real-Estate-USA-500.csv"
OUT_CSV = ROOT / "leads" / "pilot-20-enriched.csv"
OUT_JSON = ROOT / "copy" / "pilot-emails.json"
OUT_MD = ROOT / "copy" / f"pilot-review-{date.today().isoformat()}.md"

BANNED = [
    "hope this email finds you well",
    "impressive linkedin",
    "pick your brain",
    "circle back",
    "touch base",
    "deep dive",
    "—",
]

# Hand-crafted sequences: subject + body per step (Aevora post-production, client-supplied footage)
COPY = {
    "mario@fourdaughtersrealestate.com": [
        ("Virtual listings + Top 1% broker", "Hi Mariusz,\n\nSaw Four Daughters pushes virtual showings for first-time buyers and lists six active units under your name in Palatine and Chicago.\n\nTop 1% listing teams usually win attention with scroll-stopping listing media, not another static gallery.\n\nWe finish your walkthrough and listing footage: retention edits, motion graphics, and short reels from one master (you supply raw).\n\nWorth a 60-second sample on one active listing?"),
        ("Listing reels from one shoot", "Hi Mariusz,\n\nDifferent angle: your SRES and family-estate pages are trust-heavy, but social still rewards fast vertical cuts from the same listing day.\n\nWe batch 8-10 platform-native shorts plus hook variants for paid tests from your supplied clips.\n\nNo new shoot on our side.\n\nWant an example reel structure for a Palatine listing?"),
        ("Front Porch Swing content", "Hi Mariusz,\n\nYour blog reads like long-form trust building, which is rare for a Chicagoland boutique broker.\n\nWe can repackage one owner-story edit into a 3-minute retention piece plus teaser hooks for email and social.\n\nStill post-production only on your footage.\n\nOpen to a quick outline?"),
    ],
    "kathryn@sole-law.com": [
        ("Sole Title + same building", "Hi Kathryn,\n\nNoticed Sole Law and Sole Title are co-located in St. Petersburg, with you on commercial real estate and construction matters.\n\nClosings generate trust, but referral partners still judge the firm on how polished your educational content looks.\n\nWe engineer short authority pieces and motion-led explainers from footage you already capture (deposition prep, client walkthroughs, seminars).\n\nWorth sending a sample structure for a 90-second commercial RE explainer?"),
        ("Construction law visibility", "Hi Kathryn,\n\nConstruction and landlord-tenant disputes are competitive in Tampa Bay search.\n\nA single well-paced case-study style cut (anonymized) often outperforms text-only LinkedIn posts for developer referrals.\n\nWe handle edit, grade, and sound on your supplied media.\n\nCurious if that fits how you market Sole Law today?"),
        ("Title + law brand match", "Hi Kathryn,\n\nBecause title and law share a brand, mismatched video quality between the two entities can quietly hurt perceived sophistication.\n\nWe align finishing standards across both so social and website embeds feel like one premium practice.\n\nHappy to share a before/after frame approach if useful."),
    ],
    "lauren@dpgstl.com": [
        ("Virtual showings in your stack", "Hi Lauren,\n\nYour positioning leans on virtual showings, virtual open houses, and 24/7 availability (dpgstl.com is parked, so I used your public profile keywords).\n\nVirtual tours only convert when the cut feels intentional: pacing, captions, and a hook in the first two seconds.\n\nWe finish supplied walkthrough and open-house footage for luxury St. Louis listings without filming for you.\n\nWant a sample finishing spec for one listing?"),
        ("Luxury listing pacing", "Hi Lauren,\n\nLuxury buyers skim fast on mobile.\n\nWe build a hero cut plus 4-5 hook variants for Meta testing from the same master clip you already have.\n\nPost-production only.\n\nWorth a look?"),
        ("Off-market specialist angle", "Hi Lauren,\n\nOff-market and new construction deals still need shareable proof for referral partners.\n\nWe turn one supplied property story into a tight 45-second reel and a longer agent-brand piece.\n\nOpen to an example storyboard?"),
    ],
    "matt@stapleton-law.com": [
        ("Huntington PI homepage", "Hi Matthew,\n\nYour site leads with personal injury and auto work in Huntington, not residential real estate.\n\nPI firms still compete on trust creative: clear, human-paced explainers beat stock slideshows for intake quality.\n\nWe finish client-safe educational video from footage you supply (intake FAQs, attorney intros).\n\nRelevant for how you market Stapleton Law?"),
        ("Family law intake creative", "Hi Matthew,\n\nFamily and bankruptcy pages sit next to PI on the same brand.\n\nConsistent production-grade finishing across practice areas makes the firm feel larger than a six-person shop.\n\nWe do edit, grade, and sound only.\n\nWorth a short sample on one practice intro?"),
        ("10,000 clients claim", "Hi Matthew,\n\nYou cite 10,000+ clients served on the site.\n\nOne testimonial-style cut with strong retention pacing can anchor that claim on social better than text alone.\n\nWe work from supplied interviews or b-roll.\n\nInterested in a simple format?"),
    ],
    "mark@taupekalaw.com": [
        ("Remote notarization on site", "Hi Mark,\n\nOrange Beach Title advertises remote notarization via videoconference on the homepage, with you as in-house counsel.\n\nRemote closings mean more clients experience your brand on screen before they meet anyone in person.\n\nWe polish supplied explainer and closing-prep video (captions, pacing, brand motion) so it matches an attorney-owned title shop.\n\nWorth a quick sample frame?"),
        ("Gulf Coast title competition", "Hi Mark,\n\nBaldwin County title shops look similar online.\n\nShort, specific reels on wire-fraud prevention and remote closing steps can differentiate without a full rebrand.\n\nPost-production on your footage only.\n\nOpen to an outline?"),
        ("1031 + investor clients", "Hi Mark,\n\nYour services page covers 1031 and commercial work.\n\nInvestor-facing explainers with clean motion graphics tend to earn forwards among broker partners.\n\nWe engineer that from supplied slides or webinar recordings.\n\nUseful to see a format?"),
    ],
    "dfirtel@closingmanagement.com": [
        ("Clear to Close positioning", "Hi Doug,\n\nClosing Management markets a Clear to Close process and attorney-led RE transactions across Connecticut offices.\n\nLenders and agents choose title partners partly on how professional your educational content looks.\n\nWe finish supplied webinar, training, and social clips with consistent motion and grade.\n\nWorth a 60-second sample?"),
        ("Multi-office CT brand", "Hi Doug,\n\nMulti-office brands dilute when each branch posts different quality video.\n\nWe standardize finishing templates so West Hartford and satellite offices sound and look like one firm.\n\nYou keep filming; we engineer delivery.\n\nCurious if that is on your roadmap?"),
        ("Relocation + consumer path", "Hi Doug,\n\nYour homepage splits consumer, lender, and RE professional paths.\n\nThree tight explainers (one per audience) from a single supplied shoot day can save repeat production cost.\n\nWe handle post only.\n\nWant a modular cut plan?"),
    ],
    "dianal@able-title.com": [
        ("No drama NJ title", "Hi Diana,\n\nAble Title leads with No drama. No hassles. and resolving title issues before the scheduled closing date in New Jersey.\n\nThat promise is credible when your social proof video feels as calm and precise as your process.\n\nWe finish supplied client testimonial and realtor-partner clips (grade, sound, captions).\n\nWorth a sample on one Hoboken closing story?"),
        ("Testimonials name you", "Hi Diana,\n\nYour site testimonials reference you by name.\n\nWe can turn one supplied interview into a 30-second partner reel plus a longer trust piece for email nurtures.\n\nPost-production only.\n\nOpen to a structure?"),
        ("Commercial + residential", "Hi Diana,\n\nYou handle both commercial and residential closings.\n\nDifferent reels for each audience, cut from one batch of supplied b-roll, help brokers self-select faster.\n\nInterested in an example split?"),
    ],
    "cynthia@empiretitleservices.com": [
        ("FL remote notarization", "Hi Cynthia,\n\nEmpire Title is positioned in your market data around bilingual service, a client portal, 24/7 availability, and remote notarization in Florida.\n\nRemote closings increase how often buyers see your brand on video before they meet your team.\n\nWe polish supplied closing and FAQ footage so it matches a BBB A accredited shop.\n\nWorth a quick sample?"),
        ("Hollywood FL competition", "Hi Cynthia,\n\nSouth Florida title is crowded.\n\nShort, specific cuts on wire fraud and remote closing steps outperform generic posts.\n\nWe engineer hooks and finishing from your supplied media.\n\nRelevant for Empire's social?"),
        ("Bilingual client experience", "Hi Cynthia,\n\nBilingual service is a real differentiator if video captions and pacing are deliberate in both languages.\n\nWe finish supplied clips with structured captioning and motion templates.\n\nHappy to share a workflow if helpful."),
    ],
    "craig@barnardcommercial.com": [
        ("Shopping center leasing focus", "Hi Craig,\n\nBarnard Commercial positions around shopping center leasing and tenant representation in Oregon and Washington.\n\nCenter marketing packages still lean on dry PDFs while retailers expect short, data-led video tours.\n\nWe finish supplied property and aerial footage with motion graphics and pacing for leasing decks and email.\n\nWorth a sample for one center?"),
        ("Tenant rep outreach", "Hi Craig,\n\nTenant rep wins when brokers can forward a 45-second story about foot traffic and co-tenancy, not a link to a PDF.\n\nWe build that from supplied walkthroughs and charts.\n\nPost-production only.\n\nCurious if that fits your leasing workflow?"),
        ("Investment sales angle", "Hi Craig,\n\nInvestment sales buyers skim on mobile.\n\nOne master interview plus 6 hook variants for testing can be cut from the same supplied shoot.\n\nWe handle edit and motion.\n\nOpen to an example plan?"),
    ],
    "kacy.strell@triumphtitlegroup.com": [
        ("After-hours Orlando title", "Hi Kacy,\n\nTriumph Title advertises courtesy remote and after-hours closings plus same-day quick title searches in Orlando.\n\nOperations teams feel that pressure; agents still judge you on how clear your educational video is.\n\nWe finish supplied attorney-partner and consumer explainers with consistent captions and grade.\n\nWorth a 60-second sample?"),
        ("Attorney-owned title shop", "Hi Kacy,\n\nAttorney-owned positioning is on the site.\n\nShort reels on compliance and closing prep can reinforce trust for Realtors without sounding corporate.\n\nWe work from footage you supply.\n\nRelevant for Triumph's marketing?"),
        ("Office manager visibility", "Hi Kacy,\n\nAs office manager you likely coordinate what agents actually see before a closing.\n\nA single polished week-before-close checklist video reduces repetitive calls.\n\nWe engineer that from a supplied screen recording or walkthrough.\n\nWant a format?"),
    ],
    "ashley@barnardcommercial.com": [
        ("VP tenant rep angle", "Hi Ashley,\n\nBarnard's site centers on shopping center leasing and tenant representation across OR and WA.\n\nAs VP you likely touch deals where the leasing package needs sharper short-form for national tenants.\n\nWe finish supplied tour and trade-area footage into retention-led cuts and motion graphics.\n\nWorth a sample for one active center?"),
        ("Retail leasing reels", "Hi Ashley,\n\nRetail tenants forward video internally when pacing is fast and specific in the first two seconds.\n\nWe batch shorts from one supplied property master.\n\nNo filming on our end.\n\nCurious if that would help your current pipeline?"),
        ("Different from principal outreach", "Hi Ashley,\n\nCraig and I may both reach out from different angles; yours is VP-level leasing packages.\n\nHappy to send a modular deck-to-video plan if you are the right owner for marketing creative."),
    ],
    "ahammack@lawyerstitlemonroe.com": [
        ("Since the 1840s claim", "Hi Ann,\n\nLawyers Title of Monroe leads with serving Michigan since the 1840s and three offices plus mobile closings under your ownership.\n\nHeritage brands win when modern video still feels premium.\n\nWe finish supplied community and agent-partner footage for social and email.\n\nWorth a sample?"),
        ("Three-office Michigan", "Hi Ann,\n\nMulti-office title shops struggle when each branch posts different quality clips.\n\nWe standardize finishing templates across Monroe, Lambertville, and Carleton.\n\nYou supply raw; we engineer delivery.\n\nOn your radar?"),
        ("Mobile closings", "Hi Ann,\n\nMobile closings mean clients meet your brand in the field.\n\nA short supplied-filming checklist video for agents reduces friction and looks polished with pro grade and sound.\n\nInterested in a simple outline?"),
    ],
    "deborah@argeslawfirm.com": [
        ("RE closings + elder law", "Hi Deborah,\n\nArges lists real estate closings alongside estate planning and elder law in Durham.\n\nReferral partners still judge sophistication on how clear your explainer content is.\n\nWe finish supplied seminar and client-safe footage with retention pacing and motion.\n\nWorth a 90-second sample structure?"),
        ("30 years RE law", "Hi Deborah,\n\nYour market positioning cites decades in real estate law.\n\nOne well-paced authority cut can anchor that better than a static bio page.\n\nPost-production only on your media.\n\nRelevant for Arges?"),
        ("Instagram @argesdurhamlaw", "Hi Deborah,\n\nYou maintain Instagram for the firm.\n\nVertical cuts with strong captions from one supplied talking-head session can fill a month of posts.\n\nWe handle edit, grade, and sound.\n\nWant an example calendar?"),
    ],
    "rachel.tutor@ltic.com": [
        ("Amarillo branch + FNF", "Hi Rachel,\n\nLawyers Title's national site cites the 1925 founding and FNF family; your Amarillo branch shows in our data but without local web copy.\n\nBranch managers still need polished closing-prep video agents actually watch.\n\nWe finish supplied clips for wire fraud and timeline explainers.\n\nWorth a sample for your escrow team?"),
        ("Escrow officer workflow", "Hi Rachel,\n\nEscrow officers often field the same pre-close questions weekly.\n\nOne supplied screen-recording plus motion can become a reusable agent resource.\n\nWe engineer post only.\n\nUseful for Lawyers Title Amarillo?"),
        ("Branch differentiation", "Hi Rachel,\n\nNational brand, local trust.\n\nShort Amarillo-specific finishing on supplied community footage helps agents feel you are local, not generic.\n\nOpen to a quick format?"),
    ],
    "tom@arthurthomasproperties.com": [
        ("360 tours on your site", "Hi Thomas,\n\nArthur Thomas Properties promotes 360 virtual tours, pet-friendly rentals, and family-owned management since 2004 in Dover.\n\n360 capture is only half the story; grading, pacing, and hooks decide if renters stop scrolling.\n\nWe finish supplied tour and property footage (no filming).\n\nWorth a sample on one rental?"),
        ("HOA + management", "Hi Thomas,\n\nYou bundle HOA and residential management.\n\nOwner education reels reduce repetitive calls when pacing and captions are intentional.\n\nWe engineer from supplied walkthroughs.\n\nRelevant for your team?"),
        ("NH + Southern Maine", "Hi Thomas,\n\nSeacoast inventory is competitive on short-form.\n\nWe batch reels and hook variants from one supplied property master for Meta tests.\n\nPost-production only.\n\nCurious if that fits?"),
    ],
    "phil@alabamarealtyllc.com": [
        ("Digital tools Montgomery", "Hi Phil,\n\nPartners Realty stresses cutting-edge digital tools and 21st-century resources across Montgomery land, commercial, and residential.\n\nDigital positioning breaks when listing media still looks like 2019 slideshows.\n\nWe finish supplied listing and agent footage into retention cuts and ad hooks.\n\nWorth a sample?"),
        ("Land + commercial mix", "Hi Phil,\n\nLand and commercial deals need different short stories than residential.\n\nWe split one supplied shoot into audience-specific reels.\n\nYou provide raw; we engineer.\n\nOn your marketing roadmap?"),
        ("Brokerage innovation claim", "Hi Phil,\n\nInnovation is on your homepage.\n\nHook-variant packs for paid social from one listing day are a concrete way to show that claim.\n\nWe are post-production only.\n\nWant an example pack structure?"),
    ],
    "will@midwestohiotitle.com": [
        ("Wire fraud prevention", "Hi Will,\n\nMidwest Ohio Title's profile emphasizes wire fraud prevention and an integrated title platform for Troy buyers and lenders.\n\nAgents share short security explainers when they look credible, not like a bulletin.\n\nWe finish supplied training footage with motion and clear captions.\n\nWorth a 60-second sample?"),
        ("Managing partner visibility", "Hi Will,\n\nAs managing partner you set the bar agents expect.\n\nOne polished pre-close video series lowers repeat calls and reinforces trust.\n\nPost-production on supplied media only.\n\nRelevant today?"),
        ("First-time homebuyer", "Hi Will,\n\nYour keywords include first-time homebuyer services.\n\nA simple timeline explainer with retention pacing helps LO partners forward your brand.\n\nWe engineer from supplied slides or webinar.\n\nOpen to an outline?"),
    ],
    "robert@bialkin.com": [
        ("Agent + attorney brand", "Hi Robert,\n\nYour site positions you as realtor and attorney in Santa Rosa with social on Facebook and Twitter.\n\nDual brands need one consistent video standard or referrals get confused.\n\nWe finish supplied listing and authority footage with cinematic grade and motion.\n\nWorth a sample?"),
        ("Solo shop efficiency", "Hi Robert,\n\nOne-person shops rarely have time to edit reels between showings.\n\nWe turn one supplied listing walkthrough into a hero cut plus shorts for social.\n\nNo filming from us.\n\nUseful?"),
        ("RE + legal referrals", "Hi Robert,\n\nReferral partners forward video when the first line references something specific about their client situation.\n\nWe can structure cuts for RE vs legal nurtures from the same raw.\n\nCurious if that helps?"),
    ],
    "rachel@partnersrealty.info": [
        ("Montgomery agent roster", "Hi Rachel,\n\nPartners Realty markets digital-first service with agents across Montgomery and Auburn.\n\nAgents win listings when their video looks as modern as the brokerage promise.\n\nWe finish your supplied listing and open-house footage.\n\nWorth a sample reel?"),
        ("Same firm as Phil", "Hi Rachel,\n\nPartners emphasizes 21st-century tools firm-wide.\n\nIndividual agents still need personal short-form that does not look templated.\n\nWe batch hooks from your raw clips.\n\nPost-production only.\n\nInterested?"),
        ("Featured properties", "Hi Rachel,\n\nFeatured land and residential listings on the site deserve distinct pacing for each asset type.\n\nWe engineer both from one shoot day you supply.\n\nWant a quick plan?"),
    ],
    "terry@wtatitle.com": [
        ("Wally Wrap financing", "Hi Terry,\n\nWally Tingley markets the Wally Wrap creative financing system plus Austin residential and commercial closings.\n\nComplex financing needs explainers people actually finish watching.\n\nWe finish supplied seminar and client-safe footage with pattern interrupts and motion.\n\nWorth a sample?"),
        ("CFO buyer of clarity", "Hi Terry,\n\nAs CFO you care that educational content reduces confusion and support cost.\n\nOne series of short closing-prep videos can standardize agent messaging.\n\nWe handle post on supplied recordings.\n\nRelevant for wtatitle.com?"),
        ("Creative financing niche", "Hi Terry,\n\nCreative financing is your differentiator.\n\nA retention-paced explainer beats a PDF for broker forwards.\n\nWe engineer from footage you provide.\n\nOpen to a format?"),
    ],
}


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def qa(subject: str, body: str) -> dict:
    issues = []
    wc = word_count(body)
    if wc > 100:
        issues.append(f"word count {wc}>100")
    if len(subject) > 60:
        issues.append(f"subject len {len(subject)}>60")
    low = (subject + body).lower()
    for b in BANNED:
        if b in low:
            issues.append(f"banned:{b}")
    if "calendly" in low or "book 15" in low or "free tuesday" in low:
        issues.append("hard CTA")
    return {"word_count": wc, "subject_len": len(subject), "pass": len(issues) == 0, "issues": issues}


def load_source_rows():
    with SOURCE_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return {r["Email"].lower(): r for r in rows}


def main():
    by_email = load_source_rows()
    out_rows = []
    json_out = []

    for item in RESEARCH:
        email = item["email"]
        src = by_email.get(email.lower())
        if not src:
            raise SystemExit(f"Missing source row for {email}")

        seq = COPY.get(email)
        if not seq:
            raise SystemExit(f"Missing copy for {email}")

        row = dict(src)
        row["research_signal"] = item["research_signal"]
        row["research_notes"] = item["research_notes"]
        row["research_website"] = item["website"]
        row["research_linkedin"] = item["linkedin"]
        row["research_twitter"] = item["twitter"]
        row["research_facebook"] = item["facebook"]

        lead_json = {
            "lead": {
                "first_name": item["first_name"],
                "last_name": item["last_name"],
                "email": email,
                "company": item["company"],
                "title": item["title"],
            },
            "channels": {
                "website": item["website"],
                "linkedin": item["linkedin"],
                "twitter": item["twitter"],
                "facebook": item["facebook"],
            },
            "signal": item["research_signal"],
            "notes": item["research_notes"],
            "sequence": [],
        }

        delays = [0, 3, 7]
        for i, (subj, body) in enumerate(seq):
            key_s = f"email_{i+1}_subject"
            key_b = f"email_{i+1}_body"
            row[key_s] = subj
            row[key_b] = body
            q = qa(subj, body)
            lead_json["sequence"].append(
                {
                    "step": i + 1,
                    "delay_days": delays[i],
                    "subject": subj,
                    "body": body,
                    "qa": q,
                }
            )

        out_rows.append(row)
        json_out.append(lead_json)

    # Write CSV
    if out_rows:
        fieldnames = list(out_rows[0].keys())
        with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(out_rows)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(json_out, indent=2), encoding="utf-8")

    # Markdown review
    lines = [
        "# Pilot review (20 leads)",
        f"Date: {date.today().isoformat()}",
        "Sender: Aevora Media (see OFFER.md, BRAND_IDENTITY.md)",
        "",
        "## QA summary",
    ]
    total_pass = 0
    total_emails = 0
    for lead in json_out:
        for step in lead["sequence"]:
            total_emails += 1
            if step["qa"]["pass"]:
                total_pass += 1
    lines.append(f"- Emails passing QA: {total_pass}/{total_emails}")
    lines.append("")

    for lead in json_out:
        l = lead["lead"]
        lines.append(f"## {l['first_name']} {l['last_name']} — {l['company']}")
        lines.append(f"**Email:** {l['email']} | **Title:** {l['title']}")
        lines.append(f"**Signal:** {lead['signal']}")
        lines.append("")
        lines.append("**Channels researched:**")
        ch = lead["channels"]
        for k, v in ch.items():
            lines.append(f"- {k}: {v or '(none in CSV)'}")
        lines.append("")
        lines.append(f"**Notes:** {lead['notes']}")
        lines.append("")
        for step in lead["sequence"]:
            q = step["qa"]
            status = "PASS" if q["pass"] else f"FAIL ({', '.join(q['issues'])})"
            lines.append(f"### Email {step['step']} (day +{step['delay_days']}) — {status}")
            lines.append(f"**Subject ({q['subject_len']} chars):** {step['subject']}")
            lines.append(f"**Words:** {q['word_count']}")
            lines.append("")
            lines.append(step["body"])
            lines.append("")
        lines.append("---")
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print(f"QA: {total_pass}/{total_emails} passed")


if __name__ == "__main__":
    main()
