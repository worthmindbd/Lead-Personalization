"""Macro-segment mapping for mixed lead lists. Used by normalize_leads and batch copy."""

from __future__ import annotations

import re

MACRO_SEGMENTS = {
    "creative_marketing": {
        "label": "Creative / Marketing",
        "pillar": "Pillar 1/2",
        "angle": "White-label post-production, hook variants, client campaign fulfillment",
        "value_lens": "save_time",
        "forbidden_angles": ["listing tours", "property walkthroughs", "medical procedure demos"],
        "signal_sources": ["website portfolio", "case studies", "Instagram reels", "client logos"],
    },
    "real_estate": {
        "label": "Real Estate",
        "pillar": "Pillar 3",
        "angle": "Listing tours, agent authority, partner reels from supplied footage",
        "value_lens": "make_money",
        "forbidden_angles": ["SaaS UI explainers", "medical before/after"],
        "signal_sources": ["listings page", "agent bios", "YouTube channel", "market footprint"],
    },
    "professional_services": {
        "label": "Professional Services",
        "pillar": "Pillar 3",
        "angle": "Trust and authority edits from seminars, client education, partner outreach",
        "value_lens": "save_time",
        "forbidden_angles": ["listing tours", "DTC product crave ads", "hook A/B for Meta"],
        "signal_sources": ["practice areas", "testimonials", "team page", "LinkedIn posts"],
    },
    "medical_aesthetic": {
        "label": "Medical / Aesthetic",
        "pillar": "Pillar 3",
        "angle": "Procedure explainers and patient education from client-supplied footage",
        "value_lens": "make_money",
        "forbidden_angles": ["listing tours", "SaaS demos", "agency white-label"],
        "signal_sources": ["services menu", "before/after gallery", "Instagram", "provider bios"],
    },
    "software_tech": {
        "label": "Software / Tech",
        "pillar": "Pillar 4",
        "angle": "UI motion explainers and product demo finishing from screen recordings",
        "value_lens": "make_money",
        "forbidden_angles": ["listing tours", "medical procedure content"],
        "signal_sources": ["product page", "demo video", "feature releases", "case studies"],
    },
    "home_design": {
        "label": "Home / Design / Construction",
        "pillar": "Pillar 3",
        "angle": "Portfolio and property showcase pacing from supplied project footage",
        "value_lens": "make_money",
        "forbidden_angles": ["SaaS UI motion", "legal authority VSLs"],
        "signal_sources": ["portfolio", "project gallery", "Instagram", "service areas"],
    },
    "luxury_retail": {
        "label": "Luxury Retail",
        "pillar": "Pillar 2/4",
        "angle": "Product crave pacing and DTC ad variants from supplied product footage",
        "value_lens": "make_money",
        "forbidden_angles": ["listing tours", "legal seminars"],
        "signal_sources": ["product catalog", "brand story", "Instagram", "collections page"],
    },
    "marine_auto_lifestyle": {
        "label": "Marine / Auto / Lifestyle",
        "pillar": "Mixed",
        "angle": "Luxury showcase edits when high-ticket positioning is clear",
        "value_lens": "make_money",
        "forbidden_angles": ["generic fleet rental pitches", "mass-market used car ads"],
        "signal_sources": ["inventory highlights", "brand positioning", "showroom content"],
    },
    "auto_services": {
        "label": "Auto Services / Detailing / Wraps",
        "pillar": "Pillar 2",
        "angle": "Before/after transformation reels from supplied shop footage",
        "value_lens": "make_money",
        "forbidden_angles": ["inventory listing tours", "medical procedure content"],
        "signal_sources": ["Instagram reels", "before/after gallery", "services page"],
    },
    "hospitality_events": {
        "label": "Hospitality / Events",
        "pillar": "Pillar 1",
        "angle": "Event recap and brand film finishing from supplied event footage",
        "value_lens": "save_time",
        "forbidden_angles": ["SaaS demos", "medical content"],
        "signal_sources": ["event gallery", "venue photos", "social highlights"],
    },
    "low_fit": {
        "label": "Low Fit",
        "pillar": "—",
        "angle": "Minimal authority-only if overridden; otherwise deprioritize",
        "value_lens": "save_time",
        "forbidden_angles": ["hard sell on any pillar"],
        "signal_sources": ["website only"],
    },
}

CATEGORY_TO_SEGMENT: dict[str, str] = {}

def _add(segment: str, *categories: str) -> None:
    for cat in categories:
        CATEGORY_TO_SEGMENT[cat] = segment

_add(
    "creative_marketing",
    "Marketing agency", "Advertising agency", "Public relations firm", "Design agency",
    "Branding agency", "Internet marketing service", "Marketing consultant",
    "Media company", "Video production service", "Website designer", "Graphic designer",
    "Commercial photographer", "Photographer", "Photography studio", "Publisher",
    "Promotional products supplier", "Market researcher", "E commerce agency",
    "Print shop",
)
_add(
    "real_estate",
    "Real estate agency", "Real estate agent", "Commercial real estate agency",
    "Real estate developer", "Real estate consultant", "Real estate attorney",
    "Real estate rental agency", "Real estate school", "Title company", "Escrow service",
    "Property management company", "Property investment company",
    "Apartment rental agency", "Apartment complex", "Condominium complex",
    "Vacation home rental agency", "Holiday apartment rental", "Office space rental agency",
    "Apartment building", "Housing development", "Real estate appraiser",
)
_add(
    "professional_services",
    "Law firm", "Lawyer", "Personal injury attorney", "Trial attorney",
    "Immigration attorney", "Estate planning attorney", "Bankruptcy attorney",
    "Criminal justice attorney", "Employment attorney", "Insurance attorney",
    "Real estate attorney", "Legal services", "Paralegal services provider",
    "Accountant", "Accounting firm", "Certified public accountant",
    "Bookkeeping service", "Tax preparation service",
    "Business management consultant", "Consultant", "Financial planner",
    "Financial consultant", "Financial advisor", "Financial institution",
    "Investment service", "Investment company", "Investment bank",
    "Private equity firm", "Venture capital company", "Business broker",
    "Executive search firm", "Recruiter", "Human resource consulting",
    "Career guidance service", "Coaching center", "Life coach", "Training center",
    "Business school", "Economic consultant", "Engineering consultant",
    "Business development service", "Business to business service",
    "Professional services", "Insurance agency", "Insurance broker",
    "Health insurance agency", "Auto insurance agency", "Mortgage broker",
    "Mortgage lender", "Loan agency", "Credit counseling service",
    "Notary public", "Customs broker",
)
_add(
    "medical_aesthetic",
    "Medical spa", "Plastic surgeon", "Plastic surgery clinic", "Cosmetic surgeon",
    "Cosmetic dentist", "Dentist", "Dental clinic", "Dental implants periodontist",
    "Dental implants provider", "Dermatologist", "Doctor", "Medical clinic",
    "Facial spa", "Day spa", "Spa", "Spa and health club", "Skin care clinic",
    "IV therapy service", "Laser hair removal service", "Hair transplantation clinic",
    "Hair replacement service", "Teeth whitening service", "Weight loss service",
    "Wellness center", "Surgical center", "Fertility clinic", "Pain management physician",
    "Naturopathic practitioner", "Mental health clinic", "Chiropractor",
    "Massage spa", "Massage therapist", "Personal trainer", "Pilates studio",
    "Fitness center", "Gym",
)
_add(
    "software_tech",
    "Software company", "Computer consultant", "Computer service",
    "Computer support and services", "Biotechnology company",
    "Research and product development", "Research institute",
)
_add(
    "home_design",
    "Custom home builder", "Home builder", "General contractor", "Contractor",
    "Construction company", "Interior designer", "Interior construction contractor",
    "Kitchen remodeler", "Flooring contractor", "Cabinet maker", "Cabinet store",
    "Millwork shop", "Dock builder", "Building consultant", "Architect",
    "Architecture firm", "Home theater store", "Upholstery shop", "Wallpaper store",
    "Furniture maker", "Furniture manufacturer",
    "Building firm", "Modular home builder", "Interior fitting contractor",
)
_add(
    "luxury_retail",
    "Jewelry store", "Jeweler", "Jewelry designer", "Jewelry buyer",
    "Jewelry appraiser", "Jewelry repair service", "Jewelry equipment supplier",
    "Wholesale jeweler", "Diamond dealer", "Gold dealer", "Watch store",
    "Watch repair service", "Watch manufacturer", "Furniture store",
    "Antique furniture store", "Antique store", "Home goods store",
    "Kitchen furniture store", "Boutique", "Men's clothing store", "Clothing store",
    "Vintage clothing store", "Perfume store", "Art gallery", "Appliance store",
    "Architectural salvage store", "Antique furniture restoration service",
    "Consignment shop", "Wholesaler",
)
_add(
    "marine_auto_lifestyle",
    "Yacht broker", "Yacht club", "Boat dealer", "Boat rental service",
    "Boat repair shop", "Boat tour agency", "Car dealer", "Used car dealer",
    "Bugatti dealer", "Auto broker", "Car racing venue",
    "Motor vehicle dealer", "Rolls-Royce dealer", "Motorcycle shop",
    "Marina", "Shipyard", "Boat club", "Boat builders", "Boat trailer dealer",
    "Boat storage facility", "Outboard motor store", "Marine engineer",
    "Boat accessories supplier",
)
_add(
    "auto_services",
    "Car detailing service", "Vehicle wrapping service", "Window tinting service",
    "Auto window tinting service", "Car wash", "Car accessories store",
    "Auto restoration service", "Auto tune up service",
    "Car repair and maintenance service", "Auto accessories wholesaler",
    "Auto upholsterer", "Boat detailing service", "Powder coating service",
)
_add(
    "medical_aesthetic",
    "Beauty salon", "Beauty school", "Health spa", "Sauna",
    "Thai massage therapist", "Sports massage therapist", "Yoga studio",
    "Hot tub store", "Medical Center", "Medical office", "Specialized clinic",
    "Surgeon", "Orthopedic clinic", "Physical therapist",
    "Physical therapy clinic", "Sports medicine clinic", "Mental health service",
    "Cosmetics industry", "Wellness hotel", "Physical fitness program",
    "Martial arts school", "Boxing gym", "Gymnastics center", "Weightlifting area",
)
_add(
    "hospitality_events",
    "Wedding venue", "Resort hotel", "Restaurant", "Recreation center",
    "Sports complex", "Performing arts group", "Golf course",
    "Golf driving range", "Golf instructor", "Indoor golf course", "Golf shop",
    "Tennis club", "Tennis instructor", "Sports club", "Sports school",
    "Volleyball club", "Baseball club", "Basketball club", "Batting cage center",
)
_add(
    "home_design",
    "Home automation company", "Interior Decorator",
)
_add(
    "hospitality_events",
    "Hotel", "Event management company", "Event planner", "Event venue",
    "Tour operator", "Helicopter tour agency", "Flight school",
    "Social club", "Community center", "Coworking space", "Business center",
    "Corporate campus", "Corporate office", "Holding company",
)
_add(
    "low_fit",
    "Car rental agency", "Van rental agency", "Aircraft rental service",
    "Limousine service", "Airport shuttle service", "Towing service",
    "Department of motor vehicles", "Pawn shop", "Cleaners", "Mailing service",
    "Warehouse", "Shipping company", "Shipping service", "Freight forwarding service",
    "Logistics service", "Transportation service", "Trucking company",
    "Vehicle shipping agent", "Auto repair shop", "Auto body shop", "Auto parts store",
    "Cremation service", "Coffee shop", "Nail salon", "Hair salon", "Tailor",
    "Custom tailor", "Men's tailor", "Non-profit organization", "Youth organization",
    "Association / Organization", "Private investigator", "Manufacturer",
    "Medical equipment supplier", "Bank", "Banking and finance", "Aircraft dealer",
    "Airline",
)

# The one generic-inbox definition for the whole repo: both the primary-email
# pick (clean stage) and the tier resolution (normalize) consult it, so a
# divergence here made the two stages disagree about the same address.
GENERIC_EMAIL_PREFIXES = (
    "info", "hello", "contact", "support", "sales", "admin", "office",
    "team", "inquiries", "enquiries", "inquiry", "help", "mail", "service",
    "booking", "reservations", "customerservice", "reception", "general",
    "noreply",
)

BUSINESS_NAME_MARKERS = re.compile(
    r"\b(LLC|L\.L\.C\.|Inc|Incorporated|Corp|Corporation|Group|Agency|Company|"
    r"Services|Solutions|Consulting|Firm|Store|Clinic|Center|Centre|Office|"
    r"Properties|Realty|Title|Law|Legal|Dental|Spa|Media|Studio|Partners|"
    r"Associates|Enterprises|Holdings|Industries|Systems|Technologies|Tech)\b",
    re.I,
)


def segment_for_category(category: str) -> str:
    return CATEGORY_TO_SEGMENT.get((category or "").strip(), "low_fit")


def looks_like_business(name: str) -> bool:
    if BUSINESS_NAME_MARKERS.search(name):
        return True
    if name.isupper() and len(name) > 3:
        return True
    words = name.split()
    if len(words) == 1 and len(name) > 8:
        return True
    return False


# Tokens from misparsed GMB business names — never use as Hi {name},
NOT_PERSON_NAME_TOKENS = frozenset({
    "a", "an", "the", "best", "custom", "premium", "quality", "professional",
    "local", "north", "south", "east", "west", "new", "old", "top", "first",
    "one", "elite", "luxury", "royal", "modern", "classic", "national", "global",
    "closet", "kitchen", "cabinet", "design", "building", "construction",
    "escapology", "villa", "cigar", "golf", "marine", "yacht", "auto", "car",
    "pet", "time", "island", "mountain", "valley", "lake", "bay", "coast",
    "city", "county", "shipping", "flying", "access", "bin", "black", "white",
    "green", "blue", "red", "golden", "silver", "facebook", "instagram", "x",
    "tg", "homa", "villa", "forte", "coeur", "cigars", "shop", "store", "room",
    "tailored", "absolute", "hollow", "mesa", "cascade", "high", "country",
    "idaho", "stand", "cda", "trail", "creek", "taylor", "made", "orange",
    "edward", "island", "chris", "absolute", "moderneuropean", "articulate",
    "wegner", "carriage", "house", "motor", "cars", "shooting", "facilities",
    "storage", "range", "indoor", "outdoor", "wood", "working", "furniture",
})

BUSINESS_FRAGMENT_WORDS = frozenset({
    "closet", "closets", "kitchen", "kitchens", "cabinet", "cabinets", "custom",
    "design", "designs", "building", "construction", "company", "companies",
    "group", "services", "service", "solutions", "media", "studio", "studios",
    "escape", "escapology", "rooms", "room", "shop", "store", "club", "auto",
    "marine", "yacht", "golf", "cigar", "cigars", "furniture", "woodworking",
    "closets", "garages", "storage", "range", "shooting", "facilities", "county",
    "shipping", "trail", "creek", "ranch", "made", "house", "motor", "cars",
    "image", "country", "sky", "mountain", "valley", "floor", "flooring",
})


def is_generic_email(email: str) -> bool:
    local = email.split("@", 1)[0].lower()
    local = re.sub(r"[^a-z0-9]", "", local)
    return any(local == p or local.startswith(p) for p in GENERIC_EMAIL_PREFIXES)


def is_plausible_first_name(name: str) -> bool:
    token = (name or "").strip().strip("'\"")
    if not token or " " in token or len(token) < 2 or len(token) > 18:
        return False
    low = token.lower()
    if low in NOT_PERSON_NAME_TOKENS or low in BUSINESS_FRAGMENT_WORDS:
        return False
    if token.isupper() and len(token) > 2:
        return False
    if not token[0].isupper():
        return False
    if looks_like_business(token):
        return False
    return True


def is_plausible_last_name(name: str) -> bool:
    token = (name or "").strip().strip("'\"")
    if not token or " " in token or len(token) < 2 or len(token) > 22:
        return False
    low = token.lower()
    if low in NOT_PERSON_NAME_TOKENS or low in BUSINESS_FRAGMENT_WORDS:
        return False
    if looks_like_business(token):
        return False
    return True


def resolve_outreach_tier(
    first_name: str,
    last_name: str,
    primary_email: str,
    raw_name: str = "",
) -> str:
    """Person tier only when name + email clearly indicate a real contact."""
    if not primary_email or is_generic_email(primary_email):
        return "company"
    if not is_plausible_first_name(first_name) or not is_plausible_last_name(last_name):
        return "company"
    if raw_name and looks_like_business(raw_name):
        return "company"
    return "person"


def greeting_template(tier: str, first_name: str, company_name: str) -> str:
    if tier == "person" and is_plausible_first_name(first_name):
        return f"Hi {first_name.strip()},"
    return "Hi,"
