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
            "I was talking with a good friend the other day about why we stop watching videos on our "
            "phones, and we ended up laughing because we both do the exact same thing. You never "
            "really stop and think to yourself, 'Okay, I am bored now, goodbye.' You just swipe "
            "away because the person took a breath that was a second too long, or the camera stayed "
            "on one dull angle where nothing was happening. In our video editing work, I see this "
            "pattern all the time. When people start editing videos, they often think the answer is "
            "to throw ten flashy graphics and loud sound effects on the screen every two seconds. But "
            "watching something like that just gives you a headache. Over the years, I learned that "
            "keeping someone interested is actually about doing less, not more. It is about trimming "
            "the awkward little pauses, removing the empty moments, and letting the story move along "
            "smoothly like a good chat around the kitchen table. When a cut happens at just the "
            "right beat, you do not even realize you have been watching for five straight minutes. "
            "We call it pacing, but really it is just being thoughtful with someone's time. If a "
            "video feels easy to listen to and looks clean, people stick around because it feels "
            "comfortable. When I sit at my desk and look at a rough edit, my main question is "
            "simple: would my brother or my closest friend sit through this, or would they reach for "
            "their phone? If the rhythm drags, I trim it until it moves on its own. Good video work "
            "is not about showing off fancy software buttons. It is just about telling a clear story "
            "without wasting anyone's day."
        ),
    },
    {
        "id": "agency_post_bottleneck",
        "topic": "Creative agency scaling, edit capacity, and post-production bottlenecks",
        "text": (
            "A close friend of mine who runs a marketing team called me last Friday evening, and you "
            "could hear in his voice that he was completely worn out. He told me his team had just "
            "brought on two wonderful new clients, which should have been great news, but instead he "
            "was sitting at his laptop at nine at night staring at huge folders of raw camera footage. "
            "That seems to happen to almost every agency owner I know. Finding new clients is one "
            "part of the job, but once the work rolls in, the video editing side turns into a heavy "
            "load. You have to sort through messy files, fix uneven lighting, clean up the audio, "
            "add graphics, and turn hours of scattered clips into clean videos that people enjoy. If "
            "you try to do all of that yourself or scramble for help at the last minute, you end up "
            "working through weekends and fixing silly mistakes. I told him the real answer is "
            "having a dependable team you can trust like family. You send over the raw files through "
            "an organized portal, you talk through the general direction, and you go have dinner "
            "with your family while the heavy lifting gets finished behind the scenes. That way, "
            "your clients get clean finished videos on time, your team stays happy, and you do not "
            "burn out trying to be a full-time video editor on top of running a company. Finding "
            "reliable help that takes pride in the craft is what lets a business grow without all "
            "the daily chaos. He smiled and said he had forgotten what a quiet weekend felt like. "
            "Running a business should give you some peace, not keep you trapped at a desk until "
            "midnight."
        ),
    },
    {
        "id": "the_first_three_seconds",
        "topic": "Performance creative, A/B hook engineering, and combating creative fatigue",
        "text": (
            "My sister was showing me an online shop she found through a social media video, and it "
            "made me laugh thinking about how short our attention spans have become. If a video ad "
            "does not catch your eye in the first two or three seconds while you are relaxing on the "
            "couch, your thumb just moves right past it. It does not matter if the product is "
            "wonderful or if the rest of the story is great. Nobody will ever know because they "
            "never made it past the opening. Whenever we help teams put together video ads, I "
            "always tell them not to put all their hopes into just one opening scene. You film the "
            "main story or product demonstration once, but then in the editing room, you try out ten "
            "or fifteen different opening hooks. For one version, you might start with a surprising "
            "question. For another, you show a clear close-up, or call out a common problem people "
            "deal with every day. Then you share them and let real people show you what they "
            "actually like. It is always fun to see because the opening we think is the best is not "
            "always the one that wins. Sometimes a simple, honest opening does much better than "
            "something overly fancy. By testing different beginnings with the same core video, you "
            "save a lot of money on filming and you never have to guess what people want. It turns "
            "video marketing into a practical, step-by-step project instead of a stressful gamble. "
            "Instead of crossing your fingers and hoping for luck, you let real viewers guide the "
            "way. When you get those first three seconds right, the rest of the video gets a whole "
            "lot easier."
        ),
    },
    {
        "id": "executive_authority_and_craft",
        "topic": "Executive talking-head authority, motion graphics, and brand equity",
        "text": (
            "I was talking with my cousin recently about how people present themselves online, and we "
            "got onto the topic of trust. Think about what happens when you watch someone share "
            "advice on video. If their camera is grainy, the room sounds hollow like an empty garage, "
            "and the text looks sloppy, it is hard to take their ideas seriously. Even if they are "
            "brilliant at what they do, the messy video makes them look like a beginner. It is not "
            "fair, but that is simply human nature. People judge what they see and hear before they "
            "judge the idea itself. When we work on talking-head videos and presentations, our goal "
            "is simply to make sure the person looks and sounds as smart as they truly are. That "
            "does not mean adding silly cartoon stickers or loud pop-ups all over the screen. It "
            "just means setting up clean colors, clearing out background noise so the voice sounds "
            "warm and clear, and adding simple graphics when they explain a tricky concept. If "
            "someone talks about numbers, showing a clean little chart helps the viewer follow "
            "along without getting tired. Videos like that end up working for you for years. A "
            "potential client or partner can watch one thoughtful video on their own time and feel "
            "confident about working with you before you ever pick up the phone. When you take the "
            "time to polish the details, it shows that you care about your work and respect the "
            "people watching. That quiet confidence goes a very long way. You do not need to shout to "
            "be heard; you just need to make sure nothing gets in the way of your message."
        ),
    },
    {
        "id": "audio_and_sensory_immersion",
        "topic": "Sound design, spatial audio, vocal presence, and tactile Foley",
        "text": (
            "An old mentor once told me that sound is half of what you see, and the longer I work "
            "with video, the more I realize how true that is. Most people spend days picking out "
            "cameras and adjusting colors, but then they grab a generic music track, slap it under "
            "the voices, and call it a day. The funny thing is that our ears are much pickier than "
            "our eyes. If a video cut happens without any natural sound behind it, the whole thing "
            "feels fake and cold. If someone is speaking and you hear an annoying hum or their voice "
            "sounds tinny, you start feeling restless without even knowing why. In our studio, we "
            "spend a lot of time getting the sound just right. We clean up the room echoes, bring "
            "out the natural warmth in the voice, and add subtle little background sounds like the "
            "soft click of a button or the gentle rustle of paper. We also make sure the background "
            "music stays out of the way. It should sit quietly underneath so you never have to "
            "strain to hear what the person is saying. And when a really important point comes up, "
            "sometimes the best move is to cut the music completely. That sudden silence makes you "
            "sit up and pay attention. Most people will never tell you, 'Hey, the audio mix on that "
            "video was great.' They will just tell you that the video felt nice to watch and kept "
            "their attention all the way through. Good sound is the quiet glue that makes everything "
            "feel real. Taking the extra time to balance the audio makes the whole piece feel "
            "grounded and complete."
        ),
    },
    {
        "id": "systems_and_the_creative_standard",
        "topic": "Post-production systems, asset hygiene, and global commercial standards",
        "text": (
            "My uncle used to run a small cabinet shop, and whenever I visited, every tool had its "
            "own hook on the wall and every piece of wood was clearly labeled. He used to tell me "
            "that being organized is not about being stiff; it is about keeping your mind clear so "
            "you can do good work without getting frustrated. That advice stuck with me, and it is "
            "how we run our video studio today. When you handle dozens of video projects every month, "
            "things can turn messy very fast if you are not careful. If editors use different folder "
            "names or lose track of files, you end up wasting hours searching through emails, dealing "
            "with broken download links, and fixing things that should have been simple. We set up "
            "our studio so every project follows the exact same clear path from the moment raw "
            "footage arrives to the final delivery. We use a simple client portal so our partners "
            "always know where their files live, what we are working on, and how revisions are moving "
            "along. No messy email attachments, no confusion about which version is final, and no "
            "missed deadlines. Having those basic habits in place means our team can focus all their "
            "energy on storytelling, color, and pacing instead of hunting down missing assets. People "
            "do not want to babysit their video projects; they just want to send over their raw clips "
            "and receive finished work they can feel proud of. When the system behind the scenes is "
            "calm and organized, the creative work comes out looking its absolute best every single "
            "time. It takes the stress out of production and lets everyone enjoy the creative "
            "process."
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
    If none exists, inserts the block inside the first sensible container:
    - Immediately after `<td class="email-card"...>` or `<div class="email"...>` if present.
    - Otherwise right after `<body...>` or at the very beginning of the document.
    """
    new_block = render_ghost_ink_block(passage_text)

    # Rule 2: If existing block is present, replace it in-place.
    if GHOST_INK_RE.search(html):
        return GHOST_INK_RE.sub(lambda _: new_block, html, count=1)

    # Target 1: inside email-card cell (common in our Listmonk templates)
    card_match = re.search(r'(<td\s+[^>]*?class=["\'][^"\']*?email-card[^"\']*?["\'][^>]*?>)', html, re.IGNORECASE)
    if card_match:
        pos = card_match.end()
        return html[:pos] + "\n\n              <!-- Ghost Ink Deliverability Block -->\n              " + new_block + html[pos:]

    # Target 2: inside .email container (common in marketing HTMLs)
    email_div_match = re.search(r'(<div\s+[^>]*?class=["\'][^"\']*?email[^"\']*?["\'][^>]*?>)', html, re.IGNORECASE)
    if email_div_match:
        pos = email_div_match.end()
        return html[:pos] + "\n" + new_block + html[pos:]

    # Target 3: after <body>
    body_match = re.search(r'(<body[^>]*?>)', html, re.IGNORECASE)
    if body_match:
        pos = body_match.end()
        return html[:pos] + "\n" + new_block + html[pos:]

    # Fallback: prepend
    return new_block + "\n" + html
