# Segment playbooks (mixed lead lists)

Maps `First_category` from mixed CSVs to Aevora outreach strategy. Used with [`segments.py`](../../../scripts/personalization/segments.py) for normalization and batch copy.

**Sender context:** always load [OFFER.md](../../../OFFER.md) and [BRAND_IDENTITY.md](../../../BRAND_IDENTITY.md) before writing copy.

## Macro segments

| Segment | Pillar | Default fit | Primary angle |
|---------|--------|-------------|---------------|
| `creative_marketing` | Pillar 1/2 | high | White-label fulfillment, hook variants, client campaign finishing |
| `real_estate` | Pillar 3 | high | Listing tours, agent authority, partner reels |
| `professional_services` | Pillar 3 | medium | Trust/authority from seminars and client education |
| `medical_aesthetic` | Pillar 3 | medium | Procedure explainers from client-supplied footage |
| `software_tech` | Pillar 4 | high | UI motion explainers, product demo finishing |
| `home_design` | Pillar 3 | medium | Portfolio/property showcase pacing |
| `luxury_retail` | Pillar 2/4 | medium | Product crave pacing, DTC ad variants |
| `marine_auto_lifestyle` | Mixed | low | Luxury showcase only when positioning is high-ticket |
| `hospitality_events` | Pillar 1 | low | Event recap and brand film finishing |
| `general` | — | general | Catch-all for categories with no specific angle yet; a full copy pool, never a demotion |

## Dual-tier greetings

| Tier | When | Greeting | Company name |
|------|------|----------|--------------|
| `person` | Named contact + non-generic `primary_email` | `Hi {first_name},` | In body when relevant |
| `company` | GMB / generic inbox / business-only name | `Hi,` | In body, mid-message (not in greeting) |

**Rule:** company tier never invents a person's name. Never open with `Hi team at {company},`.

## Per-segment research checklist

### creative_marketing
- **Check:** portfolio/case studies, client logos, Instagram reels, services page
- **Value lens:** save time (scale client volume without in-house edit bench)
- **Avoid:** listing tours, medical procedure demos

### real_estate
- **Check:** listings, agent bios, market footprint, YouTube
- **Value lens:** make money (listings and partner reels that match luxury positioning)
- **Avoid:** SaaS UI explainers, medical content

### professional_services
- **Check:** practice areas, testimonials, team page, LinkedIn
- **Value lens:** save time (turn seminars and partner events into authority clips)
- **Avoid:** listing tours, DTC product ads

### medical_aesthetic
- **Check:** services menu, provider bios, Instagram, education content
- **Value lens:** make money (patient trust and procedure education)
- **Avoid:** agency white-label, listing tours

### software_tech
- **Check:** product page, demo video, feature pages, case studies
- **Value lens:** make money (product explainers that convert trials)
- **Avoid:** listing tours, legal seminar edits

### home_design
- **Check:** portfolio, project gallery, service areas, Instagram
- **Value lens:** make money (showcase pacing that wins high-ticket projects)
- **Avoid:** SaaS UI motion, legal VSLs

### luxury_retail
- **Check:** catalog, brand story, collections, Instagram
- **Value lens:** make money (product crave pacing for DTC and social)
- **Avoid:** legal seminars, B2B white-label unless agency retail client

### marine_auto_lifestyle
- **Check:** inventory highlights, luxury positioning, showroom content
- **Value lens:** make money (only when yacht/luxury auto positioning is clear)
- **Avoid:** fleet rental mass-market pitches

### hospitality_events
- **Check:** event gallery, venue photos, social highlights
- **Value lens:** save time (event recap finishing from supplied footage)
- **Avoid:** hard sell on unrelated pillars

### general
- **Check:** website only
- **Value lens:** save time at most
- **Avoid:** hard sell
- **Not a demotion:** the fallback for unmapped categories, with its own copy
  pool and subject templates like every other segment. These leads are
  personalized and sent like any other. Every industry needs finished video,
  so no category is scored, ranked, or written off.

## Category mapping

All 249 `First_category` values map via `lead_personalization/segments.py` → `CATEGORY_TO_SEGMENT`. Unmapped categories default to `general`.

Top categories by lead count in `all-leads-with-email.csv`:

| Category | Segment |
|----------|---------|
| Marketing agency | creative_marketing |
| Real estate agency | real_estate |
| Medical spa | medical_aesthetic |
| Software company | software_tech |
| Personal injury attorney | professional_services |
| Advertising agency | creative_marketing |
| Law firm | professional_services |
| Real estate agent | real_estate |

## Copy angle by segment (email 1 hook)

Use researched signal + segment angle. Post-production boundary always applies (client supplies footage).

- **creative_marketing:** "Agencies win when client deliverables look production-grade without adding headcount."
- **real_estate:** "Brokers move volume to firms whose listing and partner video matches their market positioning."
- **professional_services:** "Referral partners judge firms on how polished educational content looks, not just case results."
- **medical_aesthetic:** "Patient trust often follows how clearly procedures are explained on video, not stock photos alone."
- **software_tech:** "Product demos convert when UI motion makes the value obvious in the first 10 seconds."
- **home_design:** "High-ticket builders win bids when project reels match the quality of the finished work."

Canonical 3-email example (GMB, company tier): [examples.md](examples.md#canonical-gmb-sequence-company-tier-home_design)
- **luxury_retail:** "Luxury retail converts when product video creates crave, not catalog slideshows."
- **marine_auto_lifestyle:** "High-ticket inventory sells when showcase video matches the price point."
- **hospitality_events:** "Event brands extend reach when recap video is finished for social, not left as raw clips."
- **general:** Use minimal, honest role + company context only; note thin fit in `research_notes`.
