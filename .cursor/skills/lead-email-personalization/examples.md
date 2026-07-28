# Examples: weak vs strong

Use these patterns when generating or reviewing copy. Replace bracketed placeholders with researched facts.

## Opening line

**Weak**

> Hi Sarah, I noticed you work at Acme Corp and thought our video services might be a fit.

**Strong**

> Hi Sarah, saw Acme shipped entity-based audiences last month, which usually means partner GTM teams need sharper account-level creative, not more generic cuts.

## Body (value tie-in)

**Weak**

> We're a leading post-production studio with great results. Would love to connect.

**Strong**

> From your team's public job posts, AEs look full-cycle on outbound. That often burns closer time on sequencing instead of calls. We run retention-first edits and hook variants on client footage so paid social tests don't wait on an in-house bench.

## CTA

**Weak**

> Let's book 30 minutes this week. Here's my Calendly.

**Strong**

> If it's useful, I can send a 90-second sample cut style matched to your last launch creative. Worth sending?

## Subject lines

| Weak | Strong |
|------|--------|
| Quick question about video | LatticeVerse + AE prospecting |
| Partnership opportunity | Segment audiences / partner GTM |
| Intro from Aevora Media | Hook variants without headcount |

## Follow-up (email 2)

**Weak**

> Just bumping this to the top of your inbox.

**Strong**

> Different angle: your Q1 hiring spike in performance creative usually means backlog on short-form variants. We deliver 10 platform-native cuts from one master for testing, not one hero edit.

## Brand voice

**Weak (forbidden tone)**

> Affordable quick edits for your TikTok. Freelancer rates.

**Strong**

> Production-grade finishing on your supplied footage: retention pacing, motion graphics, and A/B hook variants for paid social.

## Dual-tier greetings (mixed lists)

**Person tier (weak)**

> Hi info, I saw your agency and wanted to reach out about video.

**Person tier (strong)**

> Hi Sarah, saw your agency case study page highlights fintech clients, which usually means deliverable quality is the retention lever.

**Company tier (weak)**

> Hi team at Brightline Media, I noticed your business online and wanted to reach out about video.

**Company tier (strong)**

> Hi,
>
> Your homepage leads with performance creative for DTC brands, which is exactly where hook-variant finishing pays off without adding in-house edit headcount.

Note: on company tier the business name never appears in the copy — a scraped list pasting the company name back reads as mail merge. Always second person: "your homepage", "your Instagram", "your portfolio".

## Research signal field (CSV internal)

Good `research_signal` examples:

- "Shipped X feature on [date] per press/blog"
- "Hiring 3 performance editors; JD mentions full-cycle AE"
- "LatticeVerse 2026 tour: AI + people ops positioning"

Bad:

- "Active on LinkedIn"
- "Large company in SaaS"
- "Could use video" (no observable signal)

## Canonical GMB sequence (company tier, home_design)

**Use for:** Google Maps leads with no contact name. Greeting is `Hi,` only; company name appears in the body when it adds context. Run `scripts/personalization/qa.py` on every email before export.

**Lead context (template):**

| Field | Example |
|-------|---------|
| Business | Lakeview Custom Homes |
| Segment | `home_design` |
| Tier | `company` |
| Signal | Hero walkthrough uncut on site; IG posts full takes, no hook-led Reels |

**research_signal:** `Site hero video is uncut walkthrough; Instagram Feb 2026 kitchen reveal, no paced Reels.`

### Email 1 — Day 0

**Subject:** Kenilworth hero walkthrough

```text
Hi,

Your Kenilworth portfolio leads with $4M+ builds, but the hero walkthrough 
plays like uncut site footage before the kitchen reveal lands.

At that ticket size, the reel often wins the bid before the floor plan does.

We engineer production-grade finishing on supplied site footage: retention 
pacing, cinematic grade, and hook-led Reels from one master. You capture; 
we post-produce.

Worth sending a 90-second sample cut matched to your last reveal?
```

### Email 2 — Day 3

**Subject:** instagram vs kenilworth reels

```text
Hi,

Different angle: your Instagram still posts full walkthroughs while 
Kenilworth builders in your tier ship 15-30s hook-led Reels for the same 
kitchen reveals.

We turn one site capture into paced cuts, kinetic type, and platform-native 
Reels from footage you already have. No shoot on our side.

Want an example structure for your next reveal?
```

### Email 3 — Day 7

**Subject:** Post-wrap video workflow

```text
Hi,

Does video finishing after a Kenilworth wrap sit in backlog, or does your 
team handle it in-house?

If backlog is the bottleneck, we run as a black box on supplied footage: 
retention pacing, grade, and hook variants for social.

Happy to share scope if useful.
```

**QA targets:** ≤100 words per body, subject ≤60 chars, no banned/spam/brand-forbidden terms, soft CTA only.
