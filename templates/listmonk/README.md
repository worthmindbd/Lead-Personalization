# Listmonk Cold Email Templates (3-step sequence)

Plain templates for **Listmonk** that render the per-lead copy from the enriched CSV:

- **Looks like a personal email**: no logo, no card or gray canvas, no images, no tracking pixel. Marketing-style HTML pushes cold email toward Promotions and spam.
- **No hidden text**: an earlier version carried a hidden "Ghost Ink" block. Hidden text (`display:none`, zero font size, transparent color) is a known spam and phishing signal for Gmail and Outlook, so it was removed. `tests/test_email_templates.py` fails if it comes back.
- **Direct variable insertion**: renders `email_1_body` / `email_2_body` / `email_3_body` from imported CSV attributes, falling back to Listmonk's `{{ template "content" . }}`.
- **Paragraph preservation**: `white-space: pre-line` keeps the copy's paragraph breaks.
- **Opt-out**: `{{ UnsubscribeURL }}` and `{{ UnsubscribeURL }}?manage=true` in the footer.

---

## 1. The 3 Sequence Templates

| Template File | Purpose | Body Variable |
| :--- | :--- | :--- |
| [`sequence_1_template.html`](sequence_1_template.html) | Step 1 (initial outreach) | `{{ .Subscriber.Attribs.email_1_body }}` |
| [`sequence_2_template.html`](sequence_2_template.html) | Step 2 (follow-up) | `{{ .Subscriber.Attribs.email_2_body }}` |
| [`sequence_3_template.html`](sequence_3_template.html) | Step 3 (breakup) | `{{ .Subscriber.Attribs.email_3_body }}` |

---

## 2. How to Set Up in Listmonk

### Step 1: Create the 3 templates
Listmonk Admin → **Campaigns** → **Templates** → **Create Template**, once per file (`Cold Email - Sequence 1/2/3`), pasting each file's code.

### Step 2: Create the 3 campaigns

Each step uses **its own** generated subject. The engine writes three distinct subjects per lead (`email_1_subject` … `email_3_subject`) and checks them for spam words, fragments, and duplicates. Do not prefix follow-ups with `Re:`: Listmonk sends each step as a separate message, not a reply, so `Re:` misrepresents it (and is on the subject spam list).

* **Campaign 1 (initial outreach)**
  - Template: `Cold Email - Sequence 1`
  - Subject: `{{ if .Subscriber.Attribs.email_1_subject }}{{ .Subscriber.Attribs.email_1_subject }}{{ else }}video finishing{{ end }}`
  - Alt body (plain text, keeps `multipart/alternative`):
    ```text
    {{ if .Subscriber.Attribs.email_1_body }}{{ .Subscriber.Attribs.email_1_body }}{{ end }}

    Best regards,
    Kawsar Mahmud
    CEO and Founder, Aevora Media

    Unsubscribe: {{ UnsubscribeURL }}
    ```

* **Campaign 2 (follow-up)**
  - Template: `Cold Email - Sequence 2`
  - Subject: `{{ if .Subscriber.Attribs.email_2_subject }}{{ .Subscriber.Attribs.email_2_subject }}{{ else }}video finishing{{ end }}`
  - Alt body: same as above with `email_2_body`.

* **Campaign 3 (breakup)**
  - Template: `Cold Email - Sequence 3`
  - Subject: `{{ if .Subscriber.Attribs.email_3_subject }}{{ .Subscriber.Attribs.email_3_subject }}{{ else }}video finishing{{ end }}`
  - Alt body: same as above with `email_3_body`.
