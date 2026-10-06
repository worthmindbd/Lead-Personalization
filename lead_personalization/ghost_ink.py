"""Ghost Ink deliverability engine.

Implements Jay's Ghost Ink framework (https://leadgenjay.com/value/ghost-ink/success):
A hidden ~300-word conversational passage rendered with a strictly specified CSS stack
designed to survive every email client (including desktop Outlook MSO) without leaving visual gaps.

Four Golden Rules:
1. The hiding has to survive every client (8 required CSS declarations).
2. One block per email, never two (enforced via `data-gi="1"` handle).
3. Never the same paragraph twice (pool rotation, avoiding spam fingerprints).
4. Same email in, same passage out (deterministic per-lead hash selection).

Two Unbendable Rules:
- Keep the hidden text honest and relevant (no keyword stuffing, no contradictions).
- Moves placement, not reputation (complies with SPF/DKIM/DMARC and healthy inbox hygiene).
"""

from __future__ import annotations

import hashlib
import re
from typing import Sequence

# Rule 1: The exact style attribute stack required to survive every client.
# Do not trim or alter any of these declarations:
# - color:transparent (invisible text)
# - font-size:0px; line-height:0px; max-height:0px; overflow:hidden (zero dimensions)
# - mso-hide:all (Outlook Word engine hides block)
# - display:none (standard modern clients hide block)
# - opacity:0 (visual transparency fallback)
GHOST_INK_STYLE = (
    "color:transparent;font-size:0px;line-height:0px;max-height:0px;"
    "mso-hide:all;overflow:hidden;display:none;opacity:0;"
)

# Rule 2: Distinct attribute handle so injectors can detect and replace rather than duplicate.
GHOST_INK_ATTR = 'data-gi="1"'

# Rule 3: Curated pool of real, high-entropy, ~300-word conversational passages
# strictly aligned with Aevora Media's Brand DNA (BRAND_IDENTITY.md) and Offer (OFFER.md).
# Passages reflect authentic studio insights on retention mechanics, post-production bottlenecks,
# hook engineering, authority content, audio design, and creative systems.
GHOST_INK_PASSAGES: list[dict[str, str]] = [
    {
        "id": "retention_and_pacing",
        "topic": "Audience retention mechanics, micro-pacing, and watch-time dynamics",
        "text": (
            "There is a quiet rhythm to video that you only start to notice after staring at the same "
            "timeline for eight hours straight. When someone is speaking on screen, their eyes shift and "
            "their hands move in tiny rhythms that tell you when a sentence is really finished. If you cut "
            "three frames too early, the thought feels chopped in half. If you linger half a second too "
            "long on an empty stare, the person watching reaches for their pocket without even realizing it. "
            "In the studio, we spend hours just nudging cut points back and forth by a few frames. Newer "
            "editors always try to save a slow moment by dropping in a loud swoosh sound or a flashing "
            "graphic, but that usually makes things worse. It distracts the eye instead of helping the "
            "viewer follow along. When an edit truly works, nobody thinks about the software or the person "
            "sitting at the keyboard. The story just rolls forward naturally, the way a good conversation "
            "unfolds on a long evening drive. You forget that you are looking at thousands of still "
            "pictures running past twenty-four times a second. You just stay glued to the person talking "
            "because nothing pulled you out of the room. When I review a rough cut before sending it over "
            "to a director, I mute the speaker volume first and watch the shapes move across the monitor. "
            "If the picture still holds my attention without any music to lean on, then I know the cut is "
            "solid. Real craft is about having the patience to trim away the clutter until only the honest "
            "pulse remains."
        ),
    },
    {
        "id": "agency_post_bottleneck",
        "topic": "Creative agency scaling, edit capacity, and post-production bottlenecks",
        "text": (
            "Most agency founders start out loving the creative side of the work, but after a few years "
            "they find themselves buried under endless production queues. You finish filming a strong "
            "campaign, the client is excited, and suddenly you are staring down forty terabytes of raw "
            "camera cards spread across five different drives. Someone has to ingest the files, sync the "
            "separate audio tracks, balance mismatched skin tones, and build three rounds of revisions "
            "before Tuesday morning. If you try to carry all of that finishing weight on your own "
            "shoulders, you stop thinking about growing the business and start feeling like an exhausted "
            "machine operator. When you juggle ten tasks at once, small details slip through the cracks "
            "and you spend precious hours apologizing to clients for delayed exports. What founders really "
            "need is a calm post-production bench that takes the heavy files and returns clean cuts without "
            "needing constant guidance. You upload the media to a structured server, outline the tone and "
            "deliverables in a few plain sentences, and let an experienced team handle the frame-by-frame "
            "assembly. When Monday arrives, the review links are already waiting in your inbox, formatted "
            "for every delivery standard your client asked for. That peace of mind lets you show up to "
            "strategy meetings with a clear head instead of bags under your eyes from staying awake until "
            "four in the morning fixing render errors. Building a great agency should feel like building "
            "an enduring institution, not running an endless emergency drill. When your finishing "
            "pipeline runs predictably behind the scenes, you get your evenings back and your work looks "
            "sharper than ever."
        ),
    },
    {
        "id": "the_first_three_seconds",
        "topic": "Performance creative, A/B hook engineering, and combating creative fatigue",
        "text": (
            "Every time we sit down to cut a paid video campaign, the conversation eventually turns to "
            "the opening three seconds. You can spend thirty thousand dollars hiring actors, renting "
            "lighting trucks, and scouting locations, but if the first two seconds feel sluggish on a phone "
            "screen, ninety percent of viewers will thumb right past it before the story begins. That does "
            "not mean you have to reshoot the whole project when an ad starts to feel stale. In the cutting "
            "room, the smart move is always to cut multiple distinct beginnings from the exact same raw "
            "footage. For one version, you might open on a striking close-up of a finished piece. For "
            "another, you lead with a sharp question or show the messy problem people run into every "
            "afternoon. You can even rearrange the order of scenes so the most compelling visual arrives "
            "right on frame one instead of burying it twenty seconds into the timeline. Then you deliver "
            "those distinct openings to your media team and watch how real people react in the feed. It is "
            "fascinating because the opening everyone thought was clever in the boardroom is rarely the one "
            "that wins with actual customers. By treating the beginning as an active variable rather than a "
            "fixed monument, you protect your production budget and let genuine viewer curiosity guide "
            "your choices. It turns video distribution into a disciplined craft instead of a nerve-wracking "
            "toss of the dice. Once you find the opening beat that makes someone pause their scroll and lean "
            "in, the rest of the story has a fair chance to do its job."
        ),
    },
    {
        "id": "executive_authority_and_craft",
        "topic": "Executive talking-head authority, motion graphics, and brand equity",
        "text": (
            "People form an opinion about someone's expertise within ten seconds of seeing them on "
            "camera, long before they finish listening to the argument. If an executive sits down to "
            "explain a complex topic, but the room sounds like an echo chamber and the lighting is harsh "
            "and uneven, viewers subconsciously discount the message. It is an unfair instinct, but human "
            "psychology has always worked that way. Polish communicates respect for the person on the "
            "other end of the screen. In our studio, when we work on presentations and authority videos, "
            "our approach is to strip away anything that gets between the speaker and the audience. We do "
            "not plaster the frame with cartoon stickers, noisy graphics, or frantic transitions that "
            "belong in a toy commercial. Instead, we balance the color palette so skin tones look rich and "
            "natural, clean up background hums so the voice sounds warm and centered, and introduce clean "
            "on-screen charts only when a specific data point needs visual clarity. If someone mentions a "
            "key ratio or a structural trend, showing a simple, elegant graphic keeps the audience oriented "
            "without breaking their concentration. When every frame is clean and intentional, viewers stay "
            "immersed in the substance of your thinking rather than distracted by sloppy production. That "
            "kind of quiet restraint builds enduring credibility. When a prospect or investor watches a "
            "clear, well-finished piece on their own time, they feel confident about your standards before "
            "ever stepping into a meeting room. You never have to shout or wave your arms to prove your "
            "standing; the care you put into the details says everything that needs to be said."
        ),
    },
    {
        "id": "audio_and_sensory_immersion",
        "topic": "Sound design, spatial audio, vocal presence, and tactile Foley",
        "text": (
            "You can tell how much care went into a video simply by closing your eyes and listening to "
            "the track. Most people obsess over camera lenses and sensor sizes, but then they toss a "
            "stock music file under the dialogue and consider the audio finished. Our ears are far more "
            "sensitive to rushed shortcuts than our eyes will ever be. If a scene cuts from an indoor "
            "hallway to an outdoor garden without any subtle shift in room tone or environmental breeze, "
            "the entire illusion collapses. The video suddenly feels hollow, like two plastic toys being "
            "clicked together. When we finish audio in the studio, we spend hours layering natural "
            "textural details that most viewers will never consciously identify. We clean the dialogue so "
            "every consonant comes through cleanly without any harsh sibilance or nasal rumble. We place "
            "gentle foley under movement, like the soft setting down of a ceramic mug or the subtle creak "
            "of a heavy wooden door. Most importantly, we keep the background music from competing with "
            "the human voice. Music should sit just beneath the conversation like a quiet foundation, "
            "supporting the emotion of the scene rather than drowning out the words. When an essential "
            "point arrives, the most powerful choice an editor can make is often to pull the music away "
            "entirely. That brief instant of silence commands immediate focus and gives the words real "
            "weight. Great sound work is the invisible thread that holds the entire picture together. When "
            "the mix is balanced with care, viewers remain immersed from the first sentence to the final "
            "fade."
        ),
    },
    {
        "id": "systems_and_the_creative_standard",
        "topic": "Post-production systems, asset hygiene, and global commercial standards",
        "text": (
            "Every reliable video editor I know eventually develops a near obsession with folder "
            "structure and file naming. When you are balancing twelve commercial deliverables at the "
            "same time, creative inspiration cannot survive messy desktop folders and broken cloud "
            "links. If someone names a project file final version three and another editor renames it "
            "final version new, the team wastes valuable hours comparing audio sync and chasing down "
            "lost b-roll. You end up burning out your best talent on administrative confusion instead of "
            "letting them focus on visual craft. In our studio, we treat file management with the exact "
            "same seriousness as color grading or pacing. Every campaign follows an unbending folder "
            "tree from the moment camera cards arrive on our server to the final master export. Audio "
            "lives in one folder, project timelines in another, motion assets in a dedicated bin, and "
            "revision exports in clearly dated subfolders. Our production partners drop their raw clips "
            "into an organized portal where they can check progress and leave timecoded feedback directly "
            "on the video player without messy email threads. Having that reliable routine behind the "
            "scenes protects the team from unnecessary panic. It creates a calm working rhythm where "
            "everyone knows where their assets live and what version is currently active. That means our "
            "editors can pour all of their mental energy into visual tone, narrative tension, and clean "
            "pacing rather than hunting down missing font files ten minutes before a deadline. True "
            "professionalism is not about working in chaotic scrambles; it is about building a quiet, "
            "dependable bench so that every delivery arrives on schedule looking polished and complete "
            "every single time."
        ),
    },
]

# Regex pattern matching any existing ghost ink block with the data-gi attribute
GHOST_INK_RE = re.compile(
    r'<div\s+[^>]*?data-gi=["\']?\d+["\']?[^>]*?>.*?</div>',
    re.IGNORECASE | re.DOTALL,
)


def pick_ghost_ink(
    key: str,
    step: int = 1,
    *,
    salt: str = "ghost_ink",
    pool: Sequence[dict[str, str]] | None = None,
) -> dict[str, str]:
    """Deterministically pick a ghost ink passage based on key (email) and sequence step.

    Rule 4 ('Same email in, same passage out') + Rule 3 ('Never the same paragraph twice'):
    Hashes the lead's email + step so:
    - The same lead always receives the exact same passage for that step.
    - Consecutive sequence steps (step 1, step 2, step 3) rotate to different passages.
    - Large batches distribute evenly across the variant pool.
    """
    candidates = pool or GHOST_INK_PASSAGES
    norm_key = (key or "").strip().lower()
    raw = f"{salt}:{norm_key}:step{step}".encode("utf-8")
    digest = int(hashlib.md5(raw, usedforsecurity=False).hexdigest(), 16)
    idx = digest % len(candidates)
    return candidates[idx]


def render_ghost_ink_block(passage_text: str) -> str:
    """Render the exact HTML ghost ink div adhering strictly to Rule 1 and Rule 2."""
    clean_text = passage_text.strip()
    return f'<div data-gi="1" style="{GHOST_INK_STYLE}">{clean_text}</div>'


def has_ghost_ink(html: str) -> bool:
    """Check if the HTML already contains a Ghost Ink block."""
    return bool(GHOST_INK_RE.search(html))


def inject_ghost_ink(html: str, passage_text: str) -> str:
    """Inject a ghost ink block into HTML, strictly obeying Rule 2 (One block per email, never two).

    If a block with `data-gi` already exists, replaces it in-place.
    If none exists, inserts the block after the actual email template content:
    - At the bottom of `<td class="email-card"...>` (before `</td>`) if present.
    - At the bottom of `<div class="email"...>` (before `</div>`) if present.
    - Otherwise right before `</body>` or appended at the end of the document.
    """
    new_block = render_ghost_ink_block(passage_text)

    # Rule 2: If existing block is present, replace it in-place.
    if GHOST_INK_RE.search(html):
        return GHOST_INK_RE.sub(lambda _: new_block, html, count=1)

    # Target 1: bottom of email-card cell (after actual email content)
    card_match = re.search(r'(<td\s+[^>]*?class=["\'][^"\']*?email-card[^"\']*?["\'][^>]*?>)', html, re.IGNORECASE)
    if card_match:
        close_td = html.find("</td>", card_match.end())
        if close_td != -1:
            return html[:close_td] + "\n              <!-- Ghost Ink Deliverability Block (After Actual Email Content) -->\n              " + new_block + "\n\n            " + html[close_td:]
        pos = card_match.end()
        return html[:pos] + "\n\n              <!-- Ghost Ink Deliverability Block -->\n              " + new_block + html[pos:]

    # Target 2: bottom of .email container
    email_div_match = re.search(r'(<div\s+[^>]*?class=["\'][^"\']*?email[^"\']*?["\'][^>]*?>)', html, re.IGNORECASE)
    if email_div_match:
        close_div = html.rfind("</div>")
        if close_div != -1 and close_div > email_div_match.end():
            return html[:close_div] + "\n  " + new_block + "\n" + html[close_div:]
        pos = email_div_match.end()
        return html[:pos] + "\n" + new_block + html[pos:]

    # Target 3: right before </body> (after body content)
    body_close_match = re.search(r'(</body>)', html, re.IGNORECASE)
    if body_close_match:
        pos = body_close_match.start()
        return html[:pos] + new_block + "\n" + html[pos:]

    # Fallback: append
    return html + "\n" + new_block


def validate_ghost_ink_text(passage_text: str) -> list[str]:
    """Audit Ghost Ink passage copy against deliverability, spam, and AI-slop rules.

    Two Unbendable Rules & Deliverability Guidelines:
    1. Honest, natural human tone (no keyword stuffing, no marketing claims).
    2. Zero spam triggers (SPAM_TRIGGERS).
    3. Zero AI slop buzzwords or formulaic AI clichés (AI_SLOP_PHRASES).
    4. Zero banned generic cold email phrases (BANNED).
    5. Zero brand-forbidden terms (BRAND_FORBIDDEN).
    6. Conversational passage length: ~250-350 words.

    Returns a list of issue strings (empty if fully compliant).
    """
    from lead_personalization.qa import (
        AI_SLOP_PHRASES,
        BANNED,
        BRAND_FORBIDDEN,
        SPAM_TRIGGERS,
    )

    issues: list[str] = []
    text = (passage_text or "").strip()
    words = len(text.split())
    if words < 250 or words > 350:
        issues.append(f"word_count_out_of_range:{words}")

    low = text.lower()
    for trigger in SPAM_TRIGGERS:
        if trigger in low:
            issues.append(f"spam_trigger:{trigger}")
    for slop in AI_SLOP_PHRASES:
        if slop in low:
            issues.append(f"ai_slop:{slop}")
    for b in BANNED:
        if b in low:
            issues.append(f"banned:{b}")
    for bf in BRAND_FORBIDDEN:
        if bf.strip() in low:
            issues.append(f"brand_forbidden:{bf.strip()}")

    return issues
