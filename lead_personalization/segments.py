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
    # Video producers, photographers, and studios already make video, so the
    # "your site has no video" angle insults them. They buy edit capacity:
    # white-label overflow so they can book more shoots.
    "production_studios": {
        "label": "Video / Photo / Audio Production Studios",
        "pillar": "Pillar 1",
        "angle": "White-label overflow editing, color, and sound for studios that already shoot",
        "value_lens": "make_money",
        "forbidden_angles": ["your site has no video", "you should start making video"],
        "signal_sources": ["portfolio", "showreel", "YouTube/Vimeo", "Instagram"],
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
    # Every industry needs finished video, so there is no "bad" segment. This
    # is the catch-all for categories with no specific angle yet: it gets the
    # same full solution pool every other segment gets, at a generic level.
    "general": {
        "label": "General Business",
        "pillar": "—",
        "angle": "Generic finished-video angle for categories without a specific angle yet",
        "value_lens": "save_time",
        "forbidden_angles": ["hard sell on any pillar"],
        "signal_sources": ["website only"],
    },
}

# Segments renamed after their first personalization run. Rows already written
# to disk carry the old key, so resolution has to keep accepting it or a re-run
# would strand a shipped list in the fallback. The rename is a clarity fix
# ("fit" implied a score; nothing is scored) and must not change any copy.
SEGMENT_ALIASES = {"low_fit": "general"}

GENERAL_SEGMENT = "general"


def canonical_segment(segment: str) -> str:
    """Resolve a possibly-legacy segment key to its current name."""
    seg = (segment or "").strip() or GENERAL_SEGMENT
    return SEGMENT_ALIASES.get(seg, seg)

CATEGORY_TO_SEGMENT: dict[str, str] = {}

def _add(segment: str, *categories: str) -> None:
    for cat in categories:
        CATEGORY_TO_SEGMENT[cat] = segment

_add(
    "creative_marketing",
    "Marketing agency", "Advertising agency", "Public relations firm", "Design agency",
    "Branding agency", "Internet marketing service", "Marketing consultant",
    "Media company", "Website designer", "Graphic designer", "Publisher",
    "Promotional products supplier", "Market researcher", "E commerce agency",
    "Print shop",
)
_add(
    "production_studios",
    "Video production service", "Videographer", "Wedding videographer",
    "Video editing service", "Film production company", "Movie studio",
    "Animation studio", "Video duplication service", "Photographer",
    "Wedding photographer", "Commercial photographer", "Photography studio",
    "Photography service", "Aerial photographer", "Portrait studio",
    "Drone service", "Aerial photography service", "Recording studio",
    "Audio visual consultant", "Audio visual equipment rental service",
    "Sound studio", "Music producer", "Podcast studio", "Live music production",
    "Event photographer", "Fashion photographer", "Food photographer",
    "Real estate photographer", "Photo booth", "Photo lab", "Film studio",
)
_add(
    "real_estate",
    "Real estate agency", "Real estate agent", "Commercial real estate agency",
    "Real estate developer", "Real estate consultant",
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
    "general",
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

# ---------------------------------------------------------------------------
# 2026-09-15 survey pass. Every category below was unmapped in the Aug 13
# list and has NEVER been personalized on any Drive list, so mapping it
# cannot split an audience across two angles. Categories that already
# shipped under the generic fallback are deliberately absent: their copy is
# live in ESPs and re-angling them would make per-segment reply rates
# incomparable.
# tests/test_shipped_segments_frozen.py enforces this invariant.
# ---------------------------------------------------------------------------
_add(
    "auto_services",
   "Auto glass shop", "Battery store", "Dry cleaner", "EV charging station",
   "Electric vehicle charger", "Fleet washing service", "Glass repair service",
   "Jump start service", "Key duplication service", "Locksmith", "Roadside assistance",
   "Safe opening service", "Scooter dealer", "Truck wash", "Window cleaning service",
   "Windshield repair shop",
)

_add(
    "creative_marketing",
   "Exhibition planner", "Invitation printing service", "Magician",
   "Multimedia and electronic book publisher", "Photography class",
)

_add(
    "home_design",
   "Architects association", "Building designer", "Carpet store", "Cement supplier",
   "Civil engineering company", "Countertop store", "Curtain supplier and maker",
   "Deck builder", "Drafting service", "Gutter service", "Home inspector",
   "Interior plant service", "Landscape architect", "Landscape lighting designer",
   "Lumber store", "Siding contractor", "Steel construction company", "Tile store",
   "Turf supplier", "Wallpaper installer", "Wholesale plant nursery",
   "Window installation service", "Woodworking supply store",
)

_add(
    "hospitality_events",
   "Amphitheater", "Auditorium", "Banquet hall", "Baseball", "Basketball court",
   "Beach volleyball club", "Campground", "Civic center", "Concert hall", "Conference center",
   "Dinner theater", "Exhibition and trade center", "Extended stay hotel", "Fairground",
   "Festival", "Go-karting venue", "Health resort", "Holiday home", "Homestay", "Inn",
   "Irish pub", "Live music bar", "Lounge bar", "Mobile caterer", "Night club", "Orchestra",
   "Piano bar", "Ranch", "Retreat center", "Roller skating rink", "Self defense school",
   "Swimming school", "Velodrome", "Vineyard", "Wedding chapel", "Wrestling school",
   "Yoga retreat center",
)

_add(
    "luxury_retail",
   "Animal feed store", "Asian grocery store", "Bagel shop", "Beauty supply store",
   "Bicycle store", "Cake shop", "Cannabis club", "Cannabis store", "Car stereo store",
   "Cheese shop", "Chocolate artisan", "Chocolate shop", "Clothing wholesaler",
   "Coffee roastery", "Coin dealer", "Comic book store", "Costume jewelry shop", "Deli",
   "Dessert shop", "Diner", "Dressmaker", "Exercise equipment store", "Farmers' market",
   "Fashion accessories store", "Footwear wholesaler", "Formal wear store",
   "Fresh food market", "General store", "Goldsmith", "Gourmet grocery store",
   "Grocery delivery service", "Gun shop", "Handbags shop", "Hat shop", "Health food store",
   "Herbal medicine store", "Home audio store", "Ice cream shop", "Indian grocery store",
   "Italian grocery store", "Japanese grocery store", "Jewelry manufacturer", "Juice shop",
   "Luggage store", "Market", "Meat products store", "Metaphysical supply store",
   "Natural goods store", "Organic food store", "Orthopedic shoe store", "Pastry shop",
   "Pet supply store", "Produce market", "Shoe store", "Silversmith", "Tea and coffee shop",
   "Tea house", "Tea store", "Thrift store", "Tuxedo shop", "Uniform store",
   "Vitamin & supplements store", "Western apparel store",
)

_add(
    "marine_auto_lifestyle",
   "Aircraft manufacturer", "Auto dent removal service", "Bus charter", "Bus company",
   "Canoe & kayak tour agency", "Chauffeur service", "Diving center", "Fishing charter",
   "Helicopter charter", "Horse breeder", "Hot tub repair service", "International airport",
   "Motoring club", "Parking garage", "Riding school", "Sailing school", "Taxi service",
   "Valet parking service", "Water sports equipment rental service", "Yacht charter",
)

_add(
    "medical_aesthetic",
   "Alternative medicine practitioner", "Cardiovascular and thoracic surgeon",
   "Dental laboratory", "Dental supply store", "Emergency dental service", "Endodontist",
   "Esthetics service", "Family practice physician", "Foot care", "General hospital",
   "General practitioner", "Hand surgeon", "Hospital department", "Internist",
   "Medical diagnostic imaging center", "Nurse practitioner", "Occupational health service",
   "Optometrist", "Oral and maxillofacial surgeon", "Oral surgeon", "Orthodontist",
   "Pediatric dentist", "Periodontist", "Podiatrist", "Prosthodontist", "Travel clinic",
   "Urgent care center", "Wig shop", "Women's health clinic",
)

_add(
    "professional_services",
   "Accounting school", "After school program", "Auditor", "Aviation training institute",
   "Business administration service", "Car finance and loan company", "Catholic church",
   "Certification agency", "Charter school", "Chinese language school", "Community college",
   "Consumer advice center", "Cooperative bank", "Council", "Court executive officer",
   "Credit union", "Customs consultant", "Dating service", "Design institute",
   "Employment consultant", "Engineering school", "Episcopal church", "Evangelical church",
   "Fraternal organization", "Gay & lesbian organization", "High school", "Human resources",
   "Hypnotherapy service", "Insolvency service", "Institute of technology",
   "Insurance company", "International trade consultant", "Mapping service",
   "Marriage or relationship counselor", "Massage school", "Meditation center",
   "Nursing school", "Photography school", "Place of worship", "Pregnancy care center",
   "Presbyterian church", "Private college", "Private educational institution",
   "Private university", "Public health department", "Public university",
   "Religious destination", "Religious organization", "School administration office",
   "School district office", "Seminary", "Stock broker", "Student career counseling office",
   "Training provider", "University library", "Visa and passport office", "Vocational school",
)

_add(
    "real_estate",
   "Apartment", "Appraiser", "Auction house", "Gated community", "House", "Leasing service",
   "Property maintenance", "Retail space rental agency", "Retirement community", "Surveyor",
)

_add(
    "software_tech",
   "Computer hardware manufacturer", "Data recovery service", "Electronics company",
   "Internet cafe", "Laboratory equipment supplier", "Medical technology manufacturer",
   "Phone repair service",
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
    return CATEGORY_TO_SEGMENT.get((category or "").strip(), GENERAL_SEGMENT)


def looks_like_business(name: str) -> bool:
    if BUSINESS_NAME_MARKERS.search(name or ""):
        return True
    name = name or ""
    if name.isupper() and len(name) > 3:
        return True
    words = name.split()
    # A bare long token is only a business signal when it also carries a
    # business fragment ("LakeviewHomes"); a bare long first name
    # ("Christopher", "Alexandra") must not mis-tier to company.
    if len(words) == 1 and len(name) > 8:
        low = name.lower()
        return any(frag in low for frag in BUSINESS_FRAGMENT_WORDS)
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
    # Place and locality words. A GMB business name parsed into a single token
    # is usually the town it is named after, not a person.
    "paradise", "oakland", "austin", "dallas", "houston", "phoenix", "tempe",
    "mesa", "scottsdale", "chandler", "gilbert", "irvine", "pasadena",
    "boulder", "denver", "seattle", "portland", "sandiego", "chicago",
    "boston", "atlanta", "miami", "orlando", "tampa", "jacksonville",
    "columbia", "charleston", "savannah", "nashville", "memphis", "milwaukee",
    "minneapolis", "stlouis", "kansas", "omaha", "tucson", "albuquerque",
    "fresno", "sacramento", "oakland", "berkeley", "pasadena", "redding",
    # Single letters and abbreviation soup from mis-split "Name" fields.
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n",
    "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "jr", "sr", "ii", "iii", "iv", "md", "phd", "dds", "dmd", "esq",
    "inc", "llc", "ltd", "co", "plc", "pc", "pa", "np",
})

# Raw GMB "Name" fields that parse into a first-name token which is really a
# parse artifact or a business word, not a person. Kept separate from
# NOT_PERSON_NAME_TOKENS because these are the shapes that actually appear in
# the Name column: a leading verb/adjective fragment ("Become.", "Big",
# "Better"), a category noun ("Dentistry", "Film", "Photo"), or a bare
# placeholder the CSV exported instead of a real name ("None", "My").
PARSE_ARTIFACT_TOKENS = frozenset({
    "none", "my", "our", "us", "we", "me", "him", "her", "their", "its",
    "nan", "null", "none", "n/a", "na", "unknown", "undefined", "test",
    "name", "first", "last", "firstname", "lastname", "fullname", "contact",
    "admin", "office", "info", "hello", "team", "owner", "founder", "ceo",
    "boss", "principal", "partner", "manager", "reception", "front", "desk",
    "someone", "anyone", "nobody", "mr", "mrs", "ms", "dr", "prof",
    "become", "becomes", "big", "better", "best", "good", "great", "grow",
    "growthe", "building", "built", "build", "make", "made", "do", "done",
    "get", "got", "go", "hold", "hot", "new", "now", "one", "real", "say",
    "see", "use", "want", "well", "all", "every", "any", "double", "triple",
    "single", "full", "half", "more", "most", "less", "many", "much", "such",
    "very", "quite", "just", "only", "even", "still", "already", "always",
    "never", "often", "sometimes", "maybe", "perhaps", "definitely",
    "actually", "basically", "literally", "simply", "clearly", "obviously",
})

# Nouns naming a business type or trade. A first name is never one of these.
BUSINESS_NOUN_TOKENS = frozenset({
    "dentistry", "dental", "medicine", "medical", "surgery", "surgical",
    "clinic", "hospital", "pharmacy", "therapy", "therapist", "fitness",
    "yoga", "pilates", "massage", "salon", "spa", "barber", "hair", "nails",
    "florist", "floral", "bakery", "cafe", "coffee", "restaurant", "bistro",
    "pizza", "grill", "kitchen", "brewery", "bar", "pub", "winery", "vineyard",
    "hotel", "motel", "resort", "lodge", "inn", "travel", "tours", "tour",
    "law", "legal", "attorney", "accounting", "tax", "insurance", "banking",
    "realty", "realestate", "property", "properties", "landscaping",
    "landscape", "roofing", "plumbing", "hvac", "electrical", "painting",
    "cleaning", "cleaners", "laundry", "drycleaning", "catering", "caterer",
    "printing", "print", "signage", "marketing", "advertising", "branding",
    "photography", "photographer", "photo", "video", "film", "films", "media",
    "studio", "studios", "recordings", "recording", "productions",
    "entertainment", "events", "wedding", "weddings", "venue", "catering",
    "camping", "marina", "marine", "diving", "fishing", "hunting",
    "church", "temple", "mosque", "synagogue", "school", "academy", "college",
    "university", "college", "preschool", "daycare", "childcare",
    "carrental", "rental", "rentals", "leasing", "storage", "moving",
    "towing", "locksmith", "repair", "repairs", "shop", "store", "market",
    "supply", "supplies", "wholesale", "retail", "boutique", "salon",
    "contractor", "contracting", "builder", "builders", "construction",
    "consulting", "consultants", "management", "partners", "holdings",
    "ventures", "capital", "partners", "group", "team", "labs", "laboratory",
    "clinic", "dental", "optical", "vision", "hearing", "audiology",
    "pets", "pet", "veterinary", "vet", "animal", "farm", "ranch", "garden",
    "hardware", "plumbing", "tools", "machine", "machinery", "industrial",
    "fabrication", "foundry", "mining", "energy", "solar", "electric",
    "plastics", "chemical", "packaging", "food", "beverage", "caterers",
    "agriculture", "farmers", "winery", "cider", "butcher", "deli", "grocery",
})

# Tokens that only ever look like a truncated leading word of a longer
# business name — "A+", "Ad-Star", "Aecon", "Build" — plus connective junk.
FRAGMENT_TOKENS = frozenset({
    "ad", "star", "a", "plus", "pro", "co", "inc", "the", "of", "and", "for",
    "to", "at", "by", "in", "on", "no", "yes", "hey", "hi", "heyfilm",
    "act", "art", "artistic", "artisan", "atlas", "atom", "atomic", "avion",
    "blue", "bold", "brave", "bright", "brilliant", "brink", "burn", "casa",
    "casual", "chase", "chevron", "civic", "classy", "clever", "cloud",
    "cobalt", "cobaltblue", "colossal", "comet", "compass", "copper", "core",
    "craft", "creative", "crown", "crush", "dawn", "deep", "delta", "denim",
    "dial", "dignity", "divine", "dominion", "door", "dream", "drift",
    "driven", "dynamic", "eagle", "earth", "east", "echo", "edge", "elevate",
    "elite", "emerge", "empire", "enigma", "envy", "epic", "essence", "ever",
    "everest", "evergreen", "exalt", "excel", "exotic", "expert", "extreme",
    "fable", "fade", "fancy", "fathom", "federal", "feline", "fenix", "feral",
    "ferox", "fiber", "fidelity", "fierce", "finest", "finesse", "flair",
    "flare", "flint", "flourish", "flux", "forge", "foundry", "four", "fox",
    "freedom", "frontier", "fusion", "gala", "galaxy", "garden", "garnet",
    "gem", "genesis", "glacier", "glide", "glory", "glow", "golden", "granite",
    "graphic", "gravitas", "green", "grove", "grow", "guardian", "gulf",
    "halo", "haven", "hearth", "heaven", "hero", "highland", "hilton", "holo",
    "horizon", "horizon", "hunt", "hustle", "hydra", "ignite", "imagine",
    "impact", "impress", "indigo", "infinite", "ingenious", "innovation",
    "inspire", "intense", "invent", "iris", "iron", "jade", "jazz", "jolt",
    "juno", "kanso", "keen", "kicker", "kin", "kinesis", "klar", "lance",
    "lattice", "launch", "lava", "legend", "lemon", "level", "liberty",
    "light", "lily", "lumen", "lunar", "luminous", "luxe", "magnet", "majestic",
    "marble", "marlin", "marquee", "mason", "matrix", "meadow", "meridian",
    "mesa", "metropolitan", "midnight", "mighty", "momentum", "monarch",
    "monolith", "moon", "motion", "motive", "muse", "nautilus", "nebula",
    "nectar", "neon", "noble", "nomad", "north", "nouveau", "nova", "nucleus",
    "nurture", "oasis", "obsidian", "ocean", "oak", "onyx", "opal", "orbit",
    "orchid", "organic", "origin", "outlier", "outpost", "oxide", "pace",
    "pacifica", "palace", "palm", "panther", "paradigm", "paragon", "park",
    "peak", "pearl", "pebble", "pelican", "phantom", "phoenix", "pinnacle",
    "pioneer", "pivot", "plasma", "platinum", "plume", "polar", "polish",
    "port", "possibility", "praise", "prelude", "presta", "prime", "prism",
    "prolific", "proof", "prowess", "pulse", "pursuit", "quarry", "quartz",
    "quest", "radiant", "rally", "rampart", "rapid", "raven", "realm",
    "rebel", "redwood", "reef", "reform", "reign", "relic", "renew", "revere",
    "ridge", "rigor", "rival", "roam", "rocket", "rodeo", "roots", "rover",
    "royal", "ruby", "runway", "rustic", "sable", "saffron", "sage", "salient",
    "salon", "sanctuary", "satin", "saver", "scarlet", "schema", "scoff",
    "seabird", "seamless", "seeker", "sequoia", "serene", "shadow", "shimmer",
    "shock", "sierra", "silk", "silver", "simple", "sincere", "sky", "slick",
    "slipstream", "smart", "smith", "soar", "social", "solo", "sonic", "soul",
    "spark", "sparkle", "spectrum", "spire", "splendor", "sport", "sprout",
    "stark", "stellar", "still", "sting", "stone", "storm", "strata", "stream",
    "street", "stride", "studio", "summit", "sun", "sunrise", "sunset",
    "supreme", "surf", "swirl", "sylvan", "synergy", "tactile", "talon",
    "tandem", "tangent", "tempo", "tendril", "terra", "terrain", "thicket",
    "thread", "thrive", "thunder", "tidal", "tide", "timber", "titan",
    "topaz", "torch", "tornado", "total", "touch", "trace", "trail", "trajectory",
    "tranquil", "trek", "tribute", "triumph", "trout", "true", "truffle",
    "tumble", "tundra", "turbine", "tusk", "twilight", "ultra", "umber",
    "undertow", "unison", "unity", "untamed", "uplift", "upscale", "urban",
    "urbane", "vanguard", "vault", "velvet", "venerate", "verge", "vertex",
    "vertigo", "vestige", "veto", "vibe", "vibrant", "vigil", "vigor", "viking",
    "villa", "vintage", "violet", "vireo", "vista", "vital", "vivid", "vocal",
    "volition", "voltage", "voyage", "wander", "ward", "warmth", "watch",
    "waterfall", "wave", "waypoint", "weather", "weld", "welfare", "west",
    "wheat", "whisper", "wild", "willow", "wind", "wing", "wink", "win",
    "wins", "wire", "wisp", "wistful", "wonder", "wood", "work", "world",
    "worthy", "wrap", "wren", "wyrm", "yard", "yarrow", "yeast", "yield",
    "young", "zen", "zephyr", "zinc", "zone",
})

# Positive allowlist of given names, the one signal that actually scales.
# Denylists cannot: the Name column is raw GMB data, so "Hi Beemedia," and
# "Hi Aurevoir," are brands that no denylist will ever finish catching. Every
# name here is a real given name common enough on US business directories to
# appear in this market, across the name origins actually present in the lists
# (Anglo, Hispanic, French, German, Italian, Slavic, Nordic, South Asian,
# Middle Eastern, East and Southeast Asian).
#
# A false positive ("Hi Dental Clinic,") is far more damaging than a false
# negative ("Hi,"), so the list is deliberately generous but closed: a name
# that is not here falls back to "Hi," unless the address corroborates it
# (see name_matches_email).
GIVEN_NAMES = frozenset("""
aaron abigail adam adrian adriana agnes ahmed alan alba albert alberto alejandro
alex alexa alexander alexandra alexis alfonso alice alicia alina alison allen
allison alvaro amanda amber amelia amir amy ana anastasia anderson andre andrea
andrew angel angela angelo anita ann anna anne annette anthony antonio april
arjun arlo arthur asha ashley aubrey audrey august austin ava avery barbara barry
beatrice becky belinda ben benjamin bernard bernice beth bethany betty beverly
bianca bill billy blake bobby bonnie brad braden bradley brandon brenda brendan
brent brett brian brianna brooke bruce bryan caleb callie cameron camila candace
candice carlos carmen carol carolina carrie casey cassandra catherine cecilia
celeste chad charlene charles charlie charlotte chelsea cheryl chloe chris
christian christina christine christopher cindy claire clara clarence claude
clayton clifford clinton cody cole colin colleen connie connor conrad constance
cora corey courtney craig cristina crystal curtis cynthia daisy dale dallas
damian damon dana daniel daniela danny darren darryl dave david dawn dean deborah
declan delia denis denise dennis derek desmond devin diana diane diego dominic
donna dora doreen dorothy douglas duncan dylan earl ebony eddie edgar edith
edward edwin eileen elaine eleanor elena eli elijah elisa elisabeth elise eliza
elizabeth ella ellen elmer eloisa elsa elton emanuel emily emma emmanuel enrique
eric erica erik erin ernest esther ethan eugene eva evan evelyn ezra faith
farah felicia felix fernando fiona florence floyd frances francesca francis
francisco frank franklin fred freddie frederick gabriel gabriela gaetano gail
gale garrett gary gavin gemma gene geoffrey george georgia gerald gina giovanni
gladys glen glenn gloria gordon grace graham grant greg gregory guadalupe
guillermo gustavo guy gwen hailey hank hannah harold harper harry harvey
hassan hazel heather hector heidi helen helena henry herbert herman hilda holly
hope horace howard hubert hugh hunter ian ibrahim ida ignacio imani ines ingrid
irene irma isaac isabel isabella isaiah ismael ivan ivy jack jackie jackson
jacob jacqueline jade jaime jamal james jamie jan jane janet janice jasmine
jason javier jay jayden jean jeanette jeff jeffrey jenna jennifer jenny jeremy
jerome jerry jesse jessica jesus jill jim jimmy joan joann joanna joaquin
joel john johnny jon jonathan jordan jorge jose joseph josephine joshua joy
joyce juan juanita judith judy julia julian julie julien juliet julio june
justin kaitlyn kara karen karin karl kate katherine kathleen kathryn kathy
katie kay kayla keith kelly ken kendra kenneth kent kerry kevin khalid kim
kimberly kirk kristen kristi kristin kurt kyle lance larry latoya laura lauren
laurie lawrence leah lee leon leonard leslie lester leticia lewis liam lila
lillian lily linda lindsay lino lisa lloyd logan lois lola lonnie louis louise
lucas lucia lucille lucinda luis luke lydia lyle mabel mack madison mae maggie
mahmoud malcolm mandy manuel marcel marcus margaret maria mariah marie marilyn
marina mario marion marisa marisol marjorie mark marlene marsha marshall martha
martin marty marvin mary mason mathew matthew maureen maurice max maxine maya
megan meghan melanie melinda melissa melvin mercedes meredith micah michael
michele michelle miguel mike mila mildred miles milton mindy miranda miriam
misty mitchell molly monica monique morgan moses murray myra myron nadia nancy
naomi natalie natasha nathan neal neil nelson nicholas nicole nigel nina noah
noel nora norma norman oliver olivia omar opal oscar oscar owen pablo pamela
patricia patrick paul paula pauline pearl pedro peggy penny perry peter
petra philip phillip phoenix pierre preston priscilla quentin quinn rachel
rafael rahul raj ralph ramon ramona randall randy raquel ray raymond rebecca
regina reginald rene renee rex rhonda ricardo richard rick ricky rita robert
roberta robin rocco roger roland roman ron ronald rosa rosalie rose roy ruben
ruth ryan sabrina salvador sam samuel sandra santiago sara sarah scott sean
sebastian selena sergio shane shannon shari sharon sheila sheldon shelly
sherry shirley sidney sierra silvia simon sofia sonia sonya sophia stanley
stephanie stephen steve steven stewart sullivan susan suzanne sydney sylvia
tanya tara taylor ted terence teresa terry thelma theodore thomas tiffany
timothy tina toby todd tom tomas tommy toni tony tracey tracy travis trevor
tricia tristan tyler tyrone valerie vanessa vera vernon veronica vicki victor
victoria vincent viola violet virginia vivian wade wallace walter wanda warren
wayne wendy wesley whitney wilbur wilfred will willard william willie wilson
winston yolanda yvette zachary zoe
aisha akira aleksandr alexei amara amelia amir anis anwar aya ayesha aziz
bachir badia bagha benoit bianca bilge bjarne bojana branimir bruno camille
carlos cecilia chen chidi chiara chieko christos dalia daniela dario
davide deniz dilan dimitar dinesh dong dora dorian duc edin emanuele enes
erhan ersin esther fabio fatima fatih fawaz fernanda flavio gabor gabriele
gerhard giovanna gohan gonzalo guillermo guneet hanif hassan heike hiroko
hosni hung hyun ibrahim idris ike imani ines inga irfan isabel jacinta
janek javier jian jin joaquin jonas jorg josef kaan kadir kai kamil karim karl
katharina kawsar kenneth khaled khalil kibwe konstantin kosuke krishna kyoko
lachlan laetitia laila laurentine lars leila lena lenka leo leonor liam lincoln
ling lorenzo lotfi luca lucia maddalena mahdi maite malik manuel marcelo
marguerite mariam marisol mateusz mattia mauro mehdi melanie michelle milena
milica mirembe mirko mladen mohamed mohsen monica mubarak nadia naoki
natalia nathaniel neha nestor ngozi nia niaz niels nikolai nina noam norman
octavio oded olga oliver omar orhan osman oyelaran pablo paolo pascal pedro
petra philippo pierre piotr przemyslaw quentin radek rafael rahim rajesh
ramon rania reza ricardo rocco rodrigo roger rokas ronen rosa rudi rufus
saad sabine salma samer sana sangeeta sanjay sara sasha satish sebastian selin
sergei setha shadi shahab shamil shimon siddharth silvio simone sofia soren
sorin stefan stefano sudha sven sylvie taavi tadeusz takumi tamar tanvir
tarek tasos thabo thilo thomas tiberiu timo tino tobias tomasz tsvetan tuan
tunde ulrich ursula vadim valter velma victor viktor vilma vinay
vivek waleed wladek yara yasmin yong yu yusuf zaid zakaria zara zdenek zeynep
adolfo agustin alejandro alfonso angelica antonia aquiles araceli arjun arthur
bao bartholomew bernardo bo braden brenna bruno caleb calista carlos catalina
charlotte chen chloe christina cindy cintia dario dawn dean diego dong edith
elif erik fernando gabriel genevieve grace guadalupe hector hilde hoang hugo
ike imani ingrid irene isabel jacob janine joanna josef julia juliette kai
kathleen khalid kiran kristen kyra laura leyla ling lisa lorena lucas maia
marco margot maria mario marisa marta mateo mauro mei mei ming naomi nathan
norah octavia omar paola pedro peter priya rachel rafael rahul rania renata
reuben ricardo rita robert rocco rosa ruth sara sarah shawn sofia sophia steven
takeshi tariq thomas tomas toru tyler wei yuki yusuf zack zoe
""".split())

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
    local = (email or "").split("@", 1)[0].lower()
    local = re.sub(r"[^a-z0-9]", "", local)
    # Exact match, or the prefix followed by a digit run ("sales2"): bare
    # startswith collided with real names ("salesperson@", "teamlead@",
    # "helpful@"), mis-tiering person leads to company.
    return any(
        local == p or (local.startswith(p) and local[len(p):].isdigit())
        for p in GENERIC_EMAIL_PREFIXES
    )


def name_matches_email(first_name: str, email: str) -> bool:
    """True when the address local-part carries a person-shaped name (jane@).

    Used only to rescue a name that is not on ``GIVEN_NAMES``: an address like
    ``mckinley@northside.com`` is real corroboration that the token is a person,
    even when the allowlist does not carry it. Deliberately narrow:

    - the local-part must be the name, or the name plus a single initial
      ("jane", "jane.smith", "janeb"), so "info@", "sales1@" and "northside@"
      never qualify;
    - the domain must NOT be a restatement of the name ("zenith@zenith.com"),
      which is the signature of a business mailbox, not a person.
    """
    if not first_name or not email or "@" not in email:
        return False
    local_part, _, domain = email.partition("@")
    local = re.sub(r"[^a-z]", "", local_part.lower())
    name = re.sub(r"[^a-z]", "", (first_name or "").lower())
    if len(name) < 3 or not local:
        return False
    domain_base = re.sub(r"[^a-z]", "", domain.split(".", 1)[0].lower())
    if domain_base and (domain_base == name or domain_base.startswith(name)):
        return False
    # "sarah.jones@", "sarah_jones@", "jones.sarah@", "sarahjones@" are all
    # ordinary personal-address shapes, so the name may be the first or second
    # dot/underscore segment, or the whole local-part with the surname joined.
    segments = [re.sub(r"[^a-z]", "", s) for s in re.split(r"[._-]", local_part)]
    segments = [s for s in segments if s]
    if name in segments:
        return True
    for segment in segments:
        if segment.startswith(name) and len(segment) == len(name) + 1:
            return True
        if segment.endswith(name) and len(segment) == len(name) + 1:
            return True
    joined = "".join(segments)
    return joined.startswith(name) and len(joined) == len(name) + 1


def is_plausible_first_name(name: str, email: str = "") -> bool:
    """True only when ``name`` is safe to put in a "Hi {name}," greeting.

    The Name column is raw GMB data: it carries business names, category nouns,
    addresses, and CSV export artifacts. Anything that is not verifiably a human
    given name falls back to "Hi," — a safe, slightly colder greeting always
    beats "Hi Dental Clinic,".

    Order matters: cheap structural rejections first, then the allowlist, then
    the business-marker heuristic. ``email`` is optional corroboration that can
    rescue a real name the allowlist does not carry.
    """
    token = (name or "").strip().strip("'\"")
    if not token or " " in token or len(token) < 2 or len(token) > 18:
        return False

    # Non-alphabetic content means a fragment, not a name: "Become.",
    # "Bing's", "A+", "Hey!Film", "Soixan7e", "2401". Apostrophe-hyphenated
    # given names are rare in a GMB export and never worth the risk here.
    if not token.isalpha():
        return False

    # Two or three initial caps ("BH", "JR", "SW") are abbreviations, not names.
    if token.isupper() and len(token) <= 3:
        return False

    low = token.lower()

    # The allowlist is the decision. Everything below only guards the edge
    # cases that would let a brand through a lucky structural match.
    if low in GIVEN_NAMES:
        return True

    if not email:
        return False
    if low in NOT_PERSON_NAME_TOKENS or low in BUSINESS_FRAGMENT_WORDS:
        return False
    if low in PARSE_ARTIFACT_TOKENS or low in BUSINESS_NOUN_TOKENS:
        return False
    if low in FRAGMENT_TOKENS:
        return False
    # CamelCase / multiword brands: "Beemedia", "BioLogic", "MaxiLash".
    # Mc* is the one legitimate exception and is allowed through.
    if not low.startswith("mc"):
        for ch in token[1:]:
            if ch.isupper():
                return False
    return name_matches_email(token, email)


def is_plausible_last_name(name: str) -> bool:
    token = (name or "").strip().strip("'\"")
    if not token or " " in token or len(token) < 2 or len(token) > 22:
        return False
    low = token.lower()
    if low in NOT_PERSON_NAME_TOKENS or low in BUSINESS_FRAGMENT_WORDS:
        return False
    if low in BUSINESS_SURNAME_WORDS:
        # "Lovelenscapes Photography" split into first/last name.
        return False
    if looks_like_business(token):
        return False
    return True


# Category words that land in last_name when a brand is split as a person name.
BUSINESS_SURNAME_WORDS = frozenset({
    "photography", "photo", "photos", "films", "film", "video", "videos",
    "videography", "productions", "production", "weddings", "studios",
    "creative", "designs", "homes", "events", "pictures", "media", "realty",
})


def resolve_outreach_tier(
    first_name: str,
    last_name: str,
    primary_email: str,
    raw_name: str = "",
) -> str:
    """Person tier only when name + email clearly indicate a real contact."""
    if not primary_email or is_generic_email(primary_email):
        return "company"
    if not is_plausible_first_name(first_name, primary_email) or not is_plausible_last_name(last_name):
        return "company"
    if raw_name and looks_like_business(raw_name):
        return "company"
    return "person"


def _name_is_the_brand(first_name: str, company_name: str) -> bool:
    """"Lovelenscapes" from "Lovelenscapes Photography" is the brand, not a
    person. An allowlisted given name ("Jane" in "Jane Smith Photography") is
    still a person; anything else that also names the company is not."""
    name = (first_name or "").strip().lower()
    company_tokens = re.findall(r"[a-z]+", (company_name or "").lower())
    return bool(name) and name not in GIVEN_NAMES and name in company_tokens


COMPANY_GREETINGS = ("Hi,", "Hey,", "Hello,")
PERSON_GREETINGS = ("Hi {name},", "Hey {name},", "Hello {name},", "{name},")


def greeting_template(tier: str, first_name: str, company_name: str, email: str = "") -> str:
    """Rotated greeting, stable per lead (keyed on the address).

    Person tier: "Hi/Hey/Hello {name}," or "{name},". Everyone else gets a bare
    "Hi,/Hey,/Hello," and goes straight into the first line: never the company
    name, never "team". ``company_name`` is only used to catch a brand parsed
    as a first name ("Lovelenscapes" from "Lovelenscapes Photography").
    """
    import hashlib

    digest = int(hashlib.md5(f"greeting:{email}".encode(), usedforsecurity=False).hexdigest(), 16)
    if tier == "person" and is_plausible_first_name(first_name, email) and not _name_is_the_brand(
        first_name, company_name
    ):
        pattern = PERSON_GREETINGS[digest % len(PERSON_GREETINGS)]
        return pattern.format(name=first_name.strip())
    return COMPANY_GREETINGS[digest % len(COMPANY_GREETINGS)]


# GMB categories are singular and often end in a generic head noun
# ("Video production service"). Copy needs a plural peer group that reads
# naturally in "most {peer} in {loc}".
_PEER_HEAD_PLURALS = {
    "service": "businesses", "services": "businesses", "company": "companies",
    "agency": "agencies", "studio": "studios", "center": "centers",
    "centre": "centres", "shop": "shops", "store": "stores", "clinic": "clinics",
    "firm": "firms", "office": "offices", "venue": "venues", "school": "schools",
    "consultant": "consultants", "contractor": "contractors", "dealer": "dealers",
    "builder": "builders", "designer": "designers", "photographer": "photographers",
    "videographer": "videographers", "agent": "agents", "broker": "brokers",
    "dentist": "dentists", "lawyer": "lawyers", "attorney": "attorneys",
    "architect": "architects", "planner": "planners", "producer": "producers",
    "manufacturer": "manufacturers", "supplier": "suppliers", "salon": "salons",
    "spa": "spas", "gym": "gyms", "restaurant": "restaurants", "hotel": "hotels",
    "developer": "developers", "therapist": "therapists", "coach": "coaches",
    "trainer": "trainers", "practice": "practices", "group": "groups",
    "club": "clubs", "brand": "brands", "boutique": "boutiques",
    "booth": "booth businesses", "lab": "labs", "rental": "rental businesses",
    "chiropractor": "chiropractors", "realtor": "realtors", "gallery": "galleries",
}
PEER_FALLBACK = "businesses like yours"


def peer_phrase(category: str) -> str:
    """Plural peer group for a GMB category: "Wedding photographer" ->
    "wedding photographers", "Video production service" -> "video production
    businesses"."""
    cat = re.sub(r"\s+", " ", (category or "").strip().lower())
    if not cat:
        return PEER_FALLBACK
    words = cat.split()
    head = words[-1]
    if head in _PEER_HEAD_PLURALS:
        words[-1] = _PEER_HEAD_PLURALS[head]
    elif head.endswith("s"):
        pass
    elif head.endswith(("er", "or", "ist", "ian", "ant", "ent")):
        words[-1] = head + "s"
    elif head.endswith("y") and head[-2:-1] not in "aeiou":
        words[-1] = head[:-1] + "ies"
    else:
        words[-1] = head + " businesses"
    return " ".join(words)
