# Cold email frameworks

Derived from research-led outbound practice: personalization plus relevance and value—not mail merge.

## Strategic goal

- **Not** cold → close in one email
- **Yes** cold → warm intent: curiosity, "how did they know that?", optional silent research on sender
- Prospect outcomes: no reply (majority), yes/no reply, or no reply but self-educates on sender

## What counts as personalization

| Weak (mail merge) | Strong (research-led) |
|-------------------|------------------------|
| Hey {first_name}, I see you work at {company} | Reference a recent launch, hire, post, job spec detail, event, or public initiative |
| "Impressive LinkedIn" | Observable fact tied to their role or company motion |
| Generic industry pain | Their situation + how sender improves time, money, or revenue |

## Email structure

1. **Greeting** — simple human hello (first name when available; bare `Hi,` on company tier)
2. **First line (issue)** — most important; earns 1–3 seconds; an observable issue or gap specific to this lead; no filler
3. **Body (solution)** — how the sender solves that issue; connect the offer without hype
4. **Close (CTA)** — soft, one clear low-friction next step: sample offer, example, or short call

**Length:** ≤100 words total per email. Short lines for mobile.

**Elevator test:** Like offering a stain remover when you notice a stain—direct, relevant, useful—not "hope you're well."

## B2B value lens

Every offer must map to at least one:

1. Save time  
2. Save money  
3. Make more money  

If none apply honestly, do not force outreach—flag the lead as low fit.

## Banned phrases and patterns

Never use:

- "Hope this email finds you well"
- "I came across your profile" / vague LinkedIn praise
- "I'd love to pick your brain"
- Hard CTAs: "Book 15 min", "Are you free Tuesday?", calendar links in email 1
- Corporate filler: "circle back", "touch base", "deep dive", "synergy", "leverage" (as buzzword)
- Em dashes (—) in body or subject
- **AI Slop & Buzzwords (User-Voted AI Tells):**
  - Verbs: `delve`, `delving`, `unleash`, `supercharge`, `revolutionize`, `spearhead`, `skyrocket`, `harness`, `bolster`
  - Clichés: `tapestry`, `testament to`, `game-changer`, `transformative`, `seamless`, `cutting-edge`, `bespoke`, `plethora`, `multifaceted`, `paradigm shift`, `beacon of`
  - Formulaic Openers: `in today's fast-paced`, `in today's digital landscape`, `in today's competitive landscape`, `at its core`, `look no further`, `take your business to the next level`, `unlock your potential`, `stand out from the crowd`, `without further ado`, `needless to say`

Avoid:

- Fake familiarity, excessive exclamation marks
- Symmetrical AI cadences (e.g. "X is set up, yet Y carries no video. For Z, that is often the gap between a visit and an inquiry.")
- Statistics not verified in sender docs
- "We help companies like yours" without specificity
- Spam-trigger phrasing: `free`, `guarantee`, `act now`, `limited time`, `click here`, `amazing offer`, `risk-free`
- Brand-forbidden words per `BRAND_IDENTITY.md`: cheap, affordable, freelancer, quick edit, basic video, gig, broadcast
- Subject line `Quick question` unless email 3 body asks one specific question (prefer a concrete subject instead)

## Subject lines

- Target ≤60 characters; prefer ≤33 when possible (mobile truncation)
- **Lowercase** — no title case, no ALL CAPS, no exclamation marks
- **Specific > clever** — anchor on city, category, meta description, or research signal (not company name + generic noun)
- **No spam triggers** — avoid: free, guarantee, urgent, act now, limited time, click here, winner, discount, last chance, `!!!`, fake `Re:`/`Fwd:`
- **No generic openers** — avoid `Quick question` unless email 3 body asks one specific question
- **Unique per step** — email 1 = signal hook; email 2 = alternate angle; email 3 = workflow/backlog question
- Generated via `scripts/personalization/subjects.py` segment templates + signal/meta hooks

Good patterns (from pilot examples):

- `Kenilworth hero walkthrough`
- `reels vs long walkthroughs`
- `post-wrap video workflow`

Bad patterns:

- `{Company} project reels` (mail-merge feel)
- `Quick sample / {Company}` (generic + company slug)
- `FREE video edit` (spam trigger)

## Calls to action

- Soft, no-brainer asks: curiosity question, permission to send example, "worth a look?"
- Good variants: "Interested in a sample edit from one clip you already have?", "Want an example of how we'd structure that?", "Open to a ten-minute call to see if this maps to how you work?"
- One CTA per email; rotate variants across the list (never the same CTA text for every lead)
- Follow-ups: new angle or one useful detail—not "just following up"

## Three-email sequence

| Step | Delay (user sets in ESP) | Purpose |
|------|--------------------------|---------|
| 1 | Day 0 | Signal hook + value + soft CTA |
| 2 | Day 3 | Alternate angle or proof point from research |
| 3 | Day 7 | Light bump with new detail or question; still ≤100 words |

Each step: unique subject and body. No duplicate paragraphs across steps.

## Sender brand alignment

When `BRAND_IDENTITY.md` applies:

- Tone: authoritative, clinical, premium—not desperate
- Use: engineer, retention, hooks, motion graphics, VFX, cinematic, production-grade, conversion
- Never: cheap, affordable, freelancer, quick edit, basic video, gig, broadcast
- Boundary: post-production only; client provides footage; faceless/AI only when offer allows

Map pillars to prospect segment using [segments.md](segments.md) and `OFFER.md` tiers only when relevant—do not dump pricing unprompted in email 1.

## Dual-tier outreach (mixed lists)

| Tier | When | Greeting | Company name |
|------|------|----------|--------------|
| **Person** | `outreach_tier: person` | `Hi {first_name},` | In body when relevant |
| **Company** | GMB / generic inbox / business name only | `Hi,` | **Never** — not in greeting, subject, or body |

**Company tier (Google Maps lists):** Do not use `Hi team at {company},` and do not paste the business name into the body — pulled from a scraped list, it reads as mail merge, not familiarity. Open with `Hi,` then lead with a specific observation in second person: "your site", "your homepage", "your Instagram", "your portfolio". QA flags any company-name occurrence in the body (`company_name_in_body`).

Company tier must never invent a person's name. Normalize leads before writing copy.

## Mixed-list normalization

Run `scripts/personalization/normalize_leads.py` when the CSV lacks `company`/`title` columns or uses Google Business `Name` field. Use `primary_email` for matching and sending.

## QA checklist (per email)

- [ ] ≤100 words  
- [ ] First line is specific to this lead  
- [ ] No banned phrases, brand-forbidden words, or spam triggers (see `scripts/personalization/qa.py`)
- [ ] Soft CTA  
- [ ] Subject ≤60 chars  
- [ ] No em dashes  
- [ ] No company name in body (company tier)  
- [ ] No `...` truncation artifacts  
- [ ] No duplicate paragraphs or subjects across the sequence  
- [ ] Offer claims traceable to sender docs  
- [ ] Readable on mobile in ~5 seconds  
