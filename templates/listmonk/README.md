# Listmonk Cold Email Templates (3-Sequence Setup with Ghost Ink)

High-deliverability, responsive HTML templates for **Listmonk** featuring **Jay's Ghost Ink Framework** ([leadgenjay.com/value/ghost-ink/success](https://leadgenjay.com/value/ghost-ink/success)):
- **3 Dedicated Sequence Templates**: Ready to copy and paste directly into Listmonk (`Campaigns -> Templates`).
- **Built-in Ghost Ink**: Hidden ~300-word conversational passages that tilt spam filter algorithms away from promotional classification without appearing to the recipient.
- **Responsive design**: Clean card design across desktop, tablet, and mobile (Gmail, Outlook MSO, Apple Mail, Superhuman).
- **Direct variables**: Pulls `email_1_body`, `email_2_body`, and `email_3_body` directly from your imported lead subscriber attributes.
- **Line break preservation**: Configured with `white-space: pre-line;` so that paragraphs render naturally without clumping.
- **Direct unsubscribe**: Features official Listmonk `{{ UnsubscribeURL }}` in the footer.

---

## 1. The 3 Sequence Templates

| Template File | Purpose in Listmonk | Body Variable | Ghost Ink Delivery |
| :--- | :--- | :--- | :--- |
| **[`sequence_1_template.html`](sequence_1_template.html)** | Sequence 1 (Initial Outreach) | `{{ .Subscriber.Attribs.email_1_body }}` | Step 1 rotation pool (offset 0) |
| **[`sequence_2_template.html`](sequence_2_template.html)** | Sequence 2 (Follow-up) | `{{ .Subscriber.Attribs.email_2_body }}` | Step 2 rotation pool (offset 1) |
| **[`sequence_3_template.html`](sequence_3_template.html)** | Sequence 3 (Breakup Closer) | `{{ .Subscriber.Attribs.email_3_body }}` | Step 3 rotation pool (offset 2) |

---

## 2. How to Set Up in Listmonk

### Step 1: Create the 3 Templates in Listmonk
1. Open Listmonk Admin → **Campaigns** → **Templates**.
2. Click **Create Template**:
   - Name: `Cold Email - Sequence 1`
   - Paste the code from [`sequence_1_template.html`](sequence_1_template.html)
3. Click **Create Template**:
   - Name: `Cold Email - Sequence 2`
   - Paste the code from [`sequence_2_template.html`](sequence_2_template.html)
4. Click **Create Template**:
   - Name: `Cold Email - Sequence 3`
   - Paste the code from [`sequence_3_template.html`](sequence_3_template.html)

### Step 2: Create Your Campaigns in Listmonk
* **Campaign 1**:
  - Template: Select `Cold Email - Sequence 1`
  - Subject: `{{ if .Subscriber.Attribs.email_1_subject }}{{ .Subscriber.Attribs.email_1_subject }}{{ else }}quick question{{ end }}`
  - Body: Leave blank or add any campaign notes (the template automatically pulls each lead's `{{ .Subscriber.Attribs.email_1_body }}`).
* **Campaign 2 (Follow-Up)**:
  - Template: Select `Cold Email - Sequence 2`
  - Subject: `Re: {{ if .Subscriber.Attribs.email_1_subject }}{{ .Subscriber.Attribs.email_1_subject }}{{ else if .Subscriber.Attribs.email_2_subject }}{{ .Subscriber.Attribs.email_2_subject }}{{ else }}quick question{{ end }}`
* **Campaign 3 (Breakup Closer)**:
  - Template: Select `Cold Email - Sequence 3`
  - Subject: `Re: {{ if .Subscriber.Attribs.email_1_subject }}{{ .Subscriber.Attribs.email_1_subject }}{{ else if .Subscriber.Attribs.email_3_subject }}{{ .Subscriber.Attribs.email_3_subject }}{{ else }}quick question{{ end }}`

---

## 3. How Ghost Ink Works Inside These Templates

Each template contains the exact Ghost Ink block specified by Jay:

```html
<div data-gi="1" style="color:transparent;font-size:0px;line-height:0px;max-height:0px;mso-hide:all;overflow:hidden;display:none;opacity:0;">
  ...
</div>
```

### The 4 Golden Rules Built In:
1. **Survives every client**: Uses all 8 stacked CSS declarations (Outlook desktop `mso-hide:all`, `display:none`, zero font/line-height/height, transparent opacity).
2. **One block per email**: Exactly one `data-gi="1"` block per template.
3. **Never the same paragraph twice**: Automatically rotates through a pool of 6 authentic, ~280-word casual reflections written in plain, friendly English (like talking to a friend or family member about studio work, editing, sound, and client projects—with zero AI slop, zero spam triggers, and zero em dashes).
4. **Deterministic per recipient**: Same subscriber always gets the same passage for a given sequence step (`mod (add .Subscriber.ID offset) 6`), while consecutive steps (1, 2, 3) rotate to different passages so no recipient ever sees the same passage repeated.

### Custom CSV Override:
If your imported CSV contains `ghost_ink_1`, `ghost_ink_2`, `ghost_ink_3`, or `ghost_ink`, the template automatically uses your CSV attribute instead of the built-in pool.

---

## 4. CLI Helpers & Verification

Validate any template or enrich CSVs using the CLI script:

```bash
# Check compliance of Sequence 1 template:
.venv/bin/python scripts/personalization/inject_ghost_ink.py --check templates/listmonk/sequence_1_template.html

# Enrich a CSV with deterministic ghost_ink columns:
.venv/bin/python scripts/personalization/inject_ghost_ink.py --csv leads/my-leads.csv --out leads/my-leads-gi.csv
```
