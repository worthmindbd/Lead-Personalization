# B2B Icebreakers, Greeting Rotation & Deliverability Rules

## 1. Greeting Rules & Rotation
- **Rotation Mandate**: Rotate greetings across runs to prevent ESP content hash fingerprinting (e.g. Google Workspace / Microsoft 365 spam defense).
- **Named Contacts (`person` tier)**:
  - Rotate: `Hi {first_name},`, `Hey {first_name},`, `Hello {first_name},`, `{first_name},`.
  - Only use first name when corroborated by a named contact with a valid personal inbox.
- **Company-Only & Google Maps Leads (`company` tier)**:
  - Leads from Google Maps, GMB, or generic inboxes (`info@`, `contact@`, `sales@`, `office@`):
  - **STRICT PROHIBITION**: NEVER write `Hello [Company Name]`, `Hello Team`, `Hi Team`, or `[Company Name] Team`.
  - Rotate greeting alone: `Hi,`, `Hey,`, `Hello,`.
  - Jump directly to the icebreaker on line 2.

## 2. Client-Centric First Line

The **first line** after the greeting (opener, second angle, closer) is about the client: their business, category, market, or observable assets. It never starts with *I / We / My / Our*, and no line uses stock sender-centric phrases: *"caught my eye"*, *"I noticed"*, *"I came across"*, *"I was looking at"*, *"I am reaching out"*, *"My name is"*, *"We help companies like yours"*. Enforced by `qa.opener_is_client_centric` (QA issue `sender_centric_opener`) and at offer-pack load.

The solution line may say what "we" do ("We finish the footage you already shoot..."): that is plain, honest copy, not sender-centric filler.

The first line must be a specific, **verifiable** observation, asset gap, local market reality, or operational point. Never claim more than research checked (a linked Instagram is "set up on Instagram", not "consistent weekly work"), and never quote prospect text that fails `qa.snippet_reject_reasons` (error pages, addresses, nav/CTA labels, questions, person names, filler, markup, non-English, mid-sentence cuts).

## 3. Deliverability, Anti-Slop & Anti-Spam
- **Zero AI Slop**: Strict ban on buzzwords: *delve, elevate, streamline, supercharge, revolutionize, tapestry, game-changer, seamless, cutting-edge, state-of-the-art, bespoke, in today's fast-paced world, picture this, look no further, take your business to the next level*.
- **Zero Spam Triggers**: No artificial urgency, hype, or guarantees: *guaranteed, 100% free, act now, double your income, risk-free, buy now, click here, urgent*.
- **Formatting**:
  - Word count ≤ 100 words.
  - 5th–8th grade reading level (conversational, peer-to-peer).
  - Mobile preview hook under 70 characters.

## 4. Curated Best-Performing Icebreakers

### Named Contacts (`person` tier)
- **LinkedIn Observation**: *"Your recent LinkedIn post, \"{snippet}\", is the kind of point that usually reaches more people as a short captioned clip than as text alone."* (`{snippet}` is a complete sentence or clause, never cut mid-sentence)
- **On-Site Asset / Video Gap**: *"Your current project gallery shows substantial portfolio depth, but the walkthrough clips on the landing page still rely on static title cards..."*
- **Positioning Contrast**: *"Your site leads with \"{snippet}\", which is clear positioning that most {peer} in {loc} never back up with finished video."*

### Company-Only & Google Maps Leads (`company` tier)
- **Google Maps Review / Reputation**: *"Over {review_count} verified reviews in {loc} with a {rating} average is a rare track record for {category}."* (only with real review data on the row; never describe review content research did not read)
- **Website Media Gap**: *"The portfolio on your site highlights extensive project work, yet the landing pages rely almost entirely on still photography. For commercial inquiries, short site-walk reels tend to answer client questions before the initial consultation."*
- **Social vs. Site Disconnect**: *"Your {channel} is linked from your listing, but the website itself carries no video. Visitors who arrive from Google never see the work your followers do."*
- **Category Peer Baseline (Fallback)**: *"Most {peer} in {loc} sit on usable walkthrough footage and phone clips from active projects that never become finished client-facing video."*
