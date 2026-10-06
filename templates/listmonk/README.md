# Listmonk Cold Email Templates (Primary Inbox 3-Sequence Setup)

High-deliverability, high-converting email templates for **Listmonk** featuring **Jay's Ghost Ink Framework** ([leadgenjay.com/value/ghost-ink/success](https://leadgenjay.com/value/ghost-ink/success)):
- **Premium Visual Presentation**: Centered 600px white container card on a subtle `#f4f4f5` gray canvas, crisp typography, responsive Aevora Media branding header, and founder signature.
- **Guaranteed Ghost Ink Output**: Hidden ~280-word conversational studio reflections with all 8 client-surviving CSS declarations. Ensures non-empty hidden content in every scenario (test sends, previews, and CSV campaigns).
- **Zero AI Slop & Zero Spam Words**: Plain, friendly English written like talking to a friend or family member. Zero corporate buzzwords, zero sales hype, and zero em dashes (`—`).
- **Direct Variable Insertion**: Automatically pulls `email_1_body`, `email_2_body`, and `email_3_body` from imported CSV attributes, with graceful fallback to Listmonk's `{{ template "content" . }}`.
- **Paragraph Preservation**: Configured with `white-space: pre-line;` so copy paragraphs render with natural spacing.
- **Compliant Opt-Out**: Friendly opt-out footer featuring Listmonk's `{{ UnsubscribeURL }}` and `{{ UnsubscribeURL }}?manage=true`.

---

## 1. The 3 Sequence Templates

| Template File | Purpose in Listmonk | Body Variable | Ghost Ink Delivery |
| :--- | :--- | :--- | :--- |
| **[`sequence_1_template.html`](sequence_1_template.html)** | Sequence 1 (Initial Outreach) | `{{ .Subscriber.Attribs.email_1_body }}` | Dynamic `ghost_ink_1` attribute, with built-in 6-passage auto-rotation |
| **[`sequence_2_template.html`](sequence_2_template.html)** | Sequence 2 (Follow-up) | `{{ .Subscriber.Attribs.email_2_body }}` | Dynamic `ghost_ink_2` attribute, with built-in 6-passage auto-rotation |
| **[`sequence_3_template.html`](sequence_3_template.html)** | Sequence 3 (Breakup Closer) | `{{ .Subscriber.Attribs.email_3_body }}` | Dynamic `ghost_ink_3` attribute, with built-in 6-passage auto-rotation |

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
* **Campaign 1 (Initial Outreach)**:
  - Template: Select `Cold Email - Sequence 1`
  - Subject: `{{ if .Subscriber.Attribs.email_1_subject }}{{ .Subscriber.Attribs.email_1_subject }}{{ else }}video editing for your site{{ end }}`
  - Body: Leave blank or enter campaign notes (the template dynamically renders `{{ .Subscriber.Attribs.email_1_body }}`).
  - **Alt Body (Plain Text Alternative - fixes `multipart/alternative`)**:
    ```text
    {{ if .Subscriber.Attribs.email_1_body }}{{ .Subscriber.Attribs.email_1_body }}{{ end }}

    Best regards,
    Kawsar Mahmud
    CEO and Founder

    Unsubscribe: {{ UnsubscribeURL }}
    ```

* **Campaign 2 (Follow-Up)**:
  - Template: Select `Cold Email - Sequence 2`
  - Subject: `Re: {{ if .Subscriber.Attribs.email_1_subject }}{{ .Subscriber.Attribs.email_1_subject }}{{ else if .Subscriber.Attribs.email_2_subject }}{{ .Subscriber.Attribs.email_2_subject }}{{ else }}video editing for your site{{ end }}`
  - **Alt Body (Plain Text Alternative)**:
    ```text
    {{ if .Subscriber.Attribs.email_2_body }}{{ .Subscriber.Attribs.email_2_body }}{{ end }}

    Best regards,
    Kawsar Mahmud
    CEO and Founder

    Unsubscribe: {{ UnsubscribeURL }}
    ```

* **Campaign 3 (Breakup Closer)**:
  - Template: Select `Cold Email - Sequence 3`
  - Subject: `Re: {{ if .Subscriber.Attribs.email_1_subject }}{{ .Subscriber.Attribs.email_1_subject }}{{ else if .Subscriber.Attribs.email_3_subject }}{{ .Subscriber.Attribs.email_3_subject }}{{ else }}video editing for your site{{ end }}`
  - **Alt Body (Plain Text Alternative)**:
    ```text
    {{ if .Subscriber.Attribs.email_3_body }}{{ .Subscriber.Attribs.email_3_body }}{{ end }}

    Best regards,
    Kawsar Mahmud
    CEO and Founder

    Unsubscribe: {{ UnsubscribeURL }}
    ```

---

## 3. How Ghost Ink Works Inside These Templates

Each template incorporates **Jay's Ghost Ink Framework** placed at the **top of the card** (in the active content zone before the header logo and pitch):

```html
<!-- Ghost Ink Deliverability Block (Jay's Ghost Ink Framework) -->
<!-- Positioned at top of card so spam/NLP filters evaluate 280+ words of human text in active content zone -->
<div data-gi="1" style="color:transparent;font-size:0px;line-height:0px;max-height:0px;mso-hide:all;overflow:hidden;display:none;opacity:0;">
  {{- if .Subscriber.Attribs.ghost_ink_1 -}}{{ .Subscriber.Attribs.ghost_ink_1 }}
  {{- else if .Subscriber.Attribs.ghost_ink -}}{{ .Subscriber.Attribs.ghost_ink }}
  {{- else -}}
    {{- $id := 0 -}}
    {{- if .Subscriber -}}{{- if .Subscriber.ID -}}{{- $id = .Subscriber.ID -}}{{- end -}}{{- end -}}
    {{- $idx := mod (add $id 0) 6 -}}
    {{- if eq $idx 0 -}}...Passage 1...
    {{- else if eq $idx 1 -}}...Passage 2...
    ...
    {{- else -}}...Passage 6...
    {{- end -}}
  {{- end -}}
</div>
```

- **Survives every client**: Uses all 8 stacked CSS declarations (Outlook desktop `mso-hide:all`, `display:none`, zero font/line-height/height, transparent opacity).
- **Rule 2 Compliant (One block per email, never two)**: Strictly 1 hidden block with `data-gi="1"`. Zero hidden secondary divs and zero suspicious zero-width spam evasion characters.
- **Positioned in Active Content Zone (Top of Card)**: Sits before the header and body so Gmail/Outlook NLP classifiers evaluate 280+ words of authentic human storytelling in the primary content zone, shielding the email from commercial/promotions heuristics.
- **6-passage automatic rotation**: Contains all 6 authentic studio reflections (~280 words each). Rotates deterministically across subscribers via Listmonk's Sprig engine (`mod (add $id offset) 6`).
- **Sequence step rotation**: Offsets across sequences (0, 1, 2) ensure the same subscriber never gets the same reflection twice across their 3 sequence emails.
- **Dynamic attribute priority**: If the subscriber has a personalized `ghost_ink_1/2/3` column from CSV enrichment, it seamlessly prioritizes that attribute.
- **Human, authentic tone**: Written in plain, friendly English (like talking to a friend or family member about studio work, editing, sound, and client projects—with zero AI slop, zero spam triggers, and zero em dashes).

---

## 4. CLI Helpers & Verification

Validate any template or enrich CSVs using the CLI script:

```bash
# Check compliance of Sequence 1 template:
.venv/bin/python scripts/personalization/inject_ghost_ink.py --check templates/listmonk/sequence_1_template.html

# Enrich a CSV with deterministic ghost_ink columns:
.venv/bin/python scripts/personalization/inject_ghost_ink.py --csv leads/my-leads.csv --out leads/my-leads-gi.csv
```
