from __future__ import annotations

import json
import re
import webbrowser
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

MODEL = "qwen2.5-coder:7b"
BASE_DIR = Path(__file__).resolve().parent.parent
WEBSITES_DIR = BASE_DIR / "workspace" / "websites"
WEBSITES_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = (
    "coffee",
    "automotive",
    "restaurant",
    "salon",
    "fitness",
    "retail",
    "professional",
    "general",
)

CATEGORY_RULES = {
    "automotive": [
        "automotive garage", "car garage", "auto garage", "automotive service",
        "automotive repair", "car service", "car servicing", "car repair",
        "vehicle repair", "vehicle service", "mechanic", "mechanical workshop",
        "auto service", "auto repair", "transmission conversion",
        "manual-to-automatic", "manual to automatic", "automatic transmission conversion",
        "detailing", "body shop", "tyre shop", "tire shop",
    ],
    "fitness": [
        "fitness gym", "fitness center", "fitness centre", "personal training",
        "strength training", "weight loss program", "group fitness", "crossfit",
        "yoga studio", "pilates studio", "gym", "workout", "training studio",
    ],
    "coffee": [
        "coffee shop", "coffeehouse", "coffee house", "cafe", "café",
        "espresso bar", "coffee bar", "coffee", "espresso", "cappuccino", "latte",
    ],
    "restaurant": [
        "restaurant", "diner", "bistro", "eatery", "food house", "fine dining",
        "kitchen", "cuisine", "food truck",
    ],
    "salon": [
        "hair salon", "beauty salon", "salon", "barber", "beauty studio", "spa",
        "hair studio", "nail salon", "beauty",
    ],
    "retail": [
        "retail store", "boutique", "clothing store", "fashion store", "shop",
        "store", "retail", "fashion", "clothing", "jewelry", "jewellery",
    ],
    "professional": [
        "law firm", "lawyer", "accounting firm", "accountant", "consulting firm",
        "consulting", "real estate agency", "real estate", "architecture firm",
        "architect", "clinic", "doctor", "dentist", "agency", "studio",
    ],
}

THEMES = {
    "coffee": {"bg": "#17110D", "surface": "#211812", "surface2": "#2B2019", "text": "#FFF7ED", "muted": "#CDBEAF", "accent": "#D89B52", "accent2": "#F0C98E", "line": "#49382C"},
    "automotive": {"bg": "#090B0D", "surface": "#111519", "surface2": "#171C21", "text": "#F5F7FA", "muted": "#AAB3BE", "accent": "#F5B83D", "accent2": "#FFE09A", "line": "#2B333C"},
    "restaurant": {"bg": "#160C0B", "surface": "#211211", "surface2": "#2C1715", "text": "#FFF7F0", "muted": "#D2BEB4", "accent": "#E27A52", "accent2": "#F2B39A", "line": "#4B2A25"},
    "salon": {"bg": "#120F13", "surface": "#1C171E", "surface2": "#261F29", "text": "#FFF8FC", "muted": "#CDBFCB", "accent": "#D99BC4", "accent2": "#F0C8E1", "line": "#423642"},
    "fitness": {"bg": "#080D0B", "surface": "#101713", "surface2": "#172119", "text": "#F3FFF6", "muted": "#B4C5BA", "accent": "#8BE35A", "accent2": "#C4F7A7", "line": "#2D4132"},
    "retail": {"bg": "#0D0D10", "surface": "#15151A", "surface2": "#1D1D23", "text": "#FAFAFF", "muted": "#B8B8C5", "accent": "#B6A0FF", "accent2": "#D6CCFF", "line": "#34343F"},
    "professional": {"bg": "#0B1016", "surface": "#121923", "surface2": "#192330", "text": "#F5F8FC", "muted": "#B5C0CD", "accent": "#7DB5FF", "accent2": "#BBD8FF", "line": "#2C3948"},
    "general": {"bg": "#0D0F12", "surface": "#15181D", "surface2": "#1D2128", "text": "#F6F7F9", "muted": "#B2B8C2", "accent": "#D5A84B", "accent2": "#F0D28B", "line": "#303741"},
}

FALLBACKS = {
    "coffee": dict(headline="Coffee worth slowing down for.", sub="A warm, modern coffee experience built around good drinks, good food and good moments.", eyebrow="BREWED WITH INTENTION", cta="Explore the menu", secondary="Visit the cafe", section="Signature drinks", items=[("Espresso", "Rich, concentrated and made for the first sip."), ("Cappuccino", "Velvety espresso with a soft layer of milk foam."), ("Latte", "Smooth espresso and steamed milk, easy to settle into."), ("Mocha", "Deep chocolate notes balanced with espresso."), ("Cold Brew", "Slow, smooth and refreshing."), ("Fresh Pastries", "A simple companion for your coffee.")]),
    "automotive": dict(headline="Confident service for every drive.", sub="Practical diagnosis, careful repairs and multi-brand automotive support.", eyebrow="AUTOMOTIVE SERVICE / REPAIR", cta="Book a service", secondary="Explore services", section="What we handle", items=[("Car servicing", "Routine maintenance and preventative care."), ("Diagnostics & repair", "Find the problem first, then choose the right repair."), ("Brakes & suspension", "Inspection and repair for confident handling."), ("AC & electrical", "Fault-finding and service for comfort and reliability."), ("Transmission work", "Transmission-related inspection and repair."), ("Multi-brand service", "Support for vehicles across different brands.")]),
    "restaurant": dict(headline="A table worth coming back to.", sub="Thoughtful food, a welcoming room and a menu designed around the experience.", eyebrow="FOOD / FLAVOUR / EXPERIENCE", cta="View the menu", secondary="Plan your visit", section="From the kitchen", items=[("Signature plates", "Standout dishes made to be remembered."), ("Small plates", "Easy-to-share favourites for the table."), ("Mains", "Comforting, considered plates for a proper meal."), ("Desserts", "A sweet finish to the evening."), ("Drinks", "Pair your meal with something refreshing."), ("Seasonal specials", "Fresh ideas that change with the mood.")]),
    "salon": dict(headline="A little more like you.", sub="A considered beauty experience with thoughtful service and a polished finish.", eyebrow="BEAUTY / CARE / STYLE", cta="Book an appointment", secondary="Explore services", section="Our services", items=[("Hair styling", "A polished cut, style or refresh for your look."), ("Colour", "Thoughtful colour work tailored to your style."), ("Treatments", "Care-focused treatments for a healthy finish."), ("Beauty services", "Simple, refined details that complete the look."), ("Occasion styling", "A considered finish for important moments."), ("Consultation", "Start with a conversation about what you want.")]),
    "fitness": dict(headline="Train with purpose. Feel the difference.", sub="A focused training environment built around movement, consistency and progress.", eyebrow="TRAIN / MOVE / PROGRESS", cta="Start training", secondary="See programs", section="Training paths", items=[("Strength", "Build a stronger foundation with focused training."), ("Conditioning", "Improve fitness, stamina and everyday energy."), ("Mobility", "Move better and build useful range of motion."), ("Classes", "Structured sessions with a clear purpose."), ("Personal training", "Individual guidance built around your goals."), ("Recovery", "Make recovery part of the plan, not an afterthought.")]),
    "retail": dict(headline="Things worth taking home.", sub="A considered collection presented with a simple, enjoyable shopping experience.", eyebrow="SHOP / DISCOVER / CHOOSE", cta="Explore the collection", secondary="Visit the store", section="Featured collection", items=[("New arrivals", "Fresh pieces selected to stand out."), ("Best sellers", "Customer favourites worth another look."), ("Everyday essentials", "Useful, well-chosen pieces for daily life."), ("Statement pieces", "A little more character when you want it."), ("Gifts", "Easy ideas for someone worth thinking about."), ("Seasonal edit", "A changing selection for the moment.")]),
    "professional": dict(headline="Clear expertise. Better next steps.", sub="A polished professional experience designed to make expertise easier to understand and act on.", eyebrow="EXPERTISE / CLARITY / TRUST", cta="Start a conversation", secondary="Explore services", section="How we can help", items=[("Advisory", "Practical guidance shaped around the situation."), ("Strategy", "A clear way forward when the next step is complex."), ("Review", "Careful attention to the details that matter."), ("Planning", "Turn priorities into an actionable plan."), ("Support", "Ongoing help when you need a steady partner."), ("Consultation", "Begin with a focused conversation.")]),
    "general": dict(headline="Built around what matters to you.", sub="A clear, modern introduction to the business, its offer and the people it serves.", eyebrow="WELCOME", cta="Get started", secondary="Explore more", section="What we offer", items=[("What we do", "A clear introduction to the core offer."), ("What makes it different", "The details that make the business worth choosing."), ("A better experience", "Simple, thoughtful service from first contact onward."), ("For your needs", "An offer shaped around the customer."), ("Practical support", "Clear information without unnecessary friction."), ("Let’s talk", "Start with a simple conversation.")]),
}

ABOUT = {
    "coffee": ("More than a cup.", "A place to pause, order something you love and stay a little longer. The experience keeps the focus on drinks, atmosphere and the simple pleasure of a good cafe."),
    "automotive": ("Experience that stays practical.", "A strong service experience starts with understanding the problem. The experience puts clarity, practical expertise and the next useful step in front of the customer."),
    "restaurant": ("Made for the whole experience.", "Good dining is more than a list of dishes. It is the food, the room, the people and the reason you chose to come in."),
    "salon": ("Care, detail and a polished finish.", "The best beauty experiences feel considered rather than complicated. The focus stays on care, confidence and a finish that feels like you."),
    "fitness": ("Consistency creates progress.", "Progress is built from repeatable habits. The experience makes training feel focused, understandable and worth returning to."),
    "retail": ("A collection with a point of view.", "A good shop makes choosing feel easy. The collection is given space to breathe, with clear categories and a visual identity that feels intentional."),
    "professional": ("Expertise, without unnecessary complexity.", "People should be able to understand what you do, why it matters and what to do next. The experience keeps expertise clear and approachable."),
    "general": ("A clearer way to experience the business.", "A useful website should answer important questions quickly, make the business feel distinctive and give visitors an obvious next step."),
}


def _clean_request(request: Any) -> str:
    text = str(request or "")
    text = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _contains_phrase(text: str, phrase: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)", text.lower()))


def detect_category(request: Any) -> str:
    text = _clean_request(request).lower()
    for category, phrases in CATEGORY_RULES.items():
        if any(_contains_phrase(text, phrase) for phrase in phrases):
            return category
    return "general"


def _strip_wrapper_noise(text: str) -> str:
    """Remove internal agent handoff sections that must never become business data."""
    text = _clean_request(text)
    markers = [
        "============================================================ CURRENT WEBSITE PROJECT",
        "IMPORTANT CONTEXT RULE",
        "IGNORE unrelated previous website projects",
        "FACTUAL ACCURACY",
    ]
    for marker in markers:
        pos = text.lower().find(marker.lower())
        if pos >= 0:
            # Keep only the project requirements before the internal instruction block.
            if marker.lower().startswith("important"):
                text = text[:pos].strip()
                break
    text = re.sub(r"=+\s*IMPORTANT CONTEXT RULE.*$", "", text, flags=re.I)
    return text.strip()


def extract_name(request: Any, category: str = "general") -> str:
    """Extract a business/project name without swallowing the business type."""
    text = _strip_wrapper_noise(str(request or ""))

    named_patterns = [
        r"\bfor\s+(?:a|an|the)\s+(?:fitness\s+gym|gym|coffee\s+shop|restaurant|salon|retail\s+store|professional\s+firm)\s+(?:named|called)\s+[\"']?(.+?)[\"']?(?=\s+(?:for|with|that|which|it)\b|\s*[,.!?]|\s*$)",
        r"\b(?:named|called)\s+[\"']?([A-Za-z0-9][A-Za-z0-9 &'_.-]{0,80}?)[\"']?(?=\s+(?:for|with|that|which|it)\b|\s*[,.!?]|\s*$)",
    ]

    descriptor_pattern = r"\b(?:build|create|make|design|develop|generate)\b.*?\b(?:website|site|webpage)\b\s+for\s+(?:the\s+)?(?:business\s+)?[\"']?(.+?)[\"']?\s*,\s*(?:an?|the)\b"

    suffixes = [
        "coffee shop", "coffeehouse", "restaurant", "diner", "bistro", "eatery",
        "salon", "barber", "beauty studio", "spa", "fitness gym", "gym",
        "fitness center", "fitness centre", "automotive garage", "car garage",
        "garage", "mechanic", "workshop", "boutique store", "retail store",
        "clothing store", "fashion store", "shop", "store", "law firm",
        "accounting firm", "consulting firm", "consulting", "real estate agency",
        "architecture firm", "agency",
    ]
    suffix_union = "|".join(sorted((re.escape(x) for x in suffixes), key=len, reverse=True))

    business_suffix_pattern = rf"\b(?:build|create|make|design|develop|generate)\b.*?\b(?:website|site|webpage)\b\s+for\s+(?:the\s+)?[\"']?([A-Za-z0-9][A-Za-z0-9 &'_.-]{{0,80}}?)[\"']?\s+(?:{suffix_union})\b"
    end_pattern = r"\b(?:build|create|make|design|develop|generate)\b.*?\b(?:website|site|webpage)\b\s+for\s+(?:the\s+)?(?:business\s+)?[\"']?(.+?)[\"']?\s*$"

    # Highest-confidence patterns first.
    for pattern in named_patterns + [descriptor_pattern]:
        match = re.search(pattern, text, re.I | re.S)
        if match:
            name = re.sub(r"\s+", " ", match.group(1).strip(' "\'.,!?')).strip()
            name = re.split(r"\s+(?:an?|the)\s+(?:automotive|fitness|coffee|restaurant|salon|retail|professional)\b", name, maxsplit=1, flags=re.I)[0]
            name = re.split(r"\s+(?:specializing|specialises|specializes|offering|offers|provides)\b", name, maxsplit=1, flags=re.I)[0]
            if name and name.lower() not in {"a", "an", "the", "business", "website", "site"}:
                return name

    # If the request ends with "for <name> <generic type>", strip the generic
    # type only when it is clearly descriptive. Preserve title-cased service
    # names such as "Royal Car Service".
    match = re.search(business_suffix_pattern, text, re.I | re.S)
    if match:
        candidate = re.sub(r"\s+", " ", match.group(1).strip(' "\'.,!?')).strip()
        full_match = match.group(0)
        suffix_match = re.search(r"\s+(?:" + suffix_union + r")\s*$", full_match, re.I)
        if suffix_match:
            suffix_text = suffix_match.group(0).strip()
            # A capitalized suffix can be part of a brand name. For example,
            # "Royal Car Service" should remain intact.
            if suffix_text and all(word[:1].isupper() for word in suffix_text.split() if word):
                candidate = re.sub(r"\s+", " ", re.search(end_pattern, text, re.I | re.S).group(1).strip(' "\'.,!?')).strip() if re.search(end_pattern, text, re.I | re.S) else candidate
        if candidate and candidate.lower() not in {"a", "an", "the", "business", "website", "site"}:
            return candidate

    # Plain trailing "for <name>".
    match = re.search(end_pattern, text, re.I | re.S)
    if match:
        name = re.sub(r"\s+", " ", match.group(1).strip(' "\'.,!?')).strip()
        generic = {x.lower() for x in suffixes}
        for suffix in sorted(generic, key=len, reverse=True):
            if name.lower().endswith(" " + suffix):
                prefix = name[:-(len(suffix) + 1)].rstrip()
                # Strip lowercase generic descriptors such as "Ember Table restaurant".
                if suffix.split()[-1].islower() and prefix:
                    name = prefix
                break
        if name and name.lower() not in {"a", "an", "the", "business", "website", "site"}:
            return name

    return "Your Business"


def _extract_explicit_details(request: str) -> dict[str, Any]:
    text = _strip_wrapper_noise(request)
    details: dict[str, Any] = {}
    for key, pattern in {
        "phone": r"\b(?:phone|mobile|tel(?:ephone)?)\s*[:\-]?\s*([+()\d][+()\d\s.-]{6,})",
        "address": r"\baddress\s*[:\-]\s*(.+?)(?=\s+(?:phone|mobile|hours?|whatsapp)\s*[:\-]|$)",
        "hours": r"\b(?:hours?|opening hours?)\s*[:\-]\s*(.+?)(?=\s+(?:phone|mobile|address|whatsapp)\s*[:\-]|$)",
        "whatsapp": r"\bwhatsapp\s*[:\-]?\s*([+()\d][+()\d\s.-]{6,})",
    }.items():
        m = re.search(pattern, text, re.I)
        if m:
            details[key] = m.group(1).strip(' ,.;')
    return details


def _fallback_plan(category: str, name: str) -> dict[str, Any]:
    base = FALLBACKS.get(category, FALLBACKS["general"])
    return {
        "headline": base["headline"],
        "sub": base["sub"],
        "eyebrow": base["eyebrow"],
        "cta": base["cta"],
        "secondary": base["secondary"],
        "section": base["section"],
        "items": list(base["items"]),
    }


def plan_with_ai(request: str, category: str, name: str) -> dict[str, Any]:
    fallback = _fallback_plan(category, name)
    try:
        from ollama import chat
        prompt = (
            "Return ONLY valid JSON. Create copy for a website. "
            f"Category: {category}. Business: {name}. Request: {request}\n"
            "Never invent factual contact details, prices, ratings, hours, awards, certifications, "
            "years, statistics, guarantees, addresses or phone numbers. "
            "Keys: headline, sub, eyebrow, cta, secondary, section, items. "
            "items must be exactly 6 objects with name and description."
        )
        response = chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
        raw = str(getattr(response.message, "content", "") or "").strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I | re.S).strip()
        start, end = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[start:end + 1]) if start >= 0 and end > start else {}
        if not isinstance(data, dict):
            return fallback
        out = dict(fallback)
        for key in ("headline", "sub", "eyebrow", "cta", "secondary", "section"):
            if isinstance(data.get(key), str) and data[key].strip():
                out[key] = data[key].strip()
        items = []
        for item in data.get("items", []):
            if isinstance(item, dict) and item.get("name") and item.get("description"):
                items.append((str(item["name"]).strip(), str(item["description"]).strip()))
        if len(items) == 6:
            out["items"] = items
        return out
    except Exception:
        return fallback


def esc(value: Any) -> str:
    return escape(str(value), quote=True)


def svg_art(category: str) -> str:
    common = '<svg viewBox="0 0 620 460" role="img" aria-label="Decorative business illustration" class="art" preserveAspectRatio="xMidYMid meet">'
    art = {
        "coffee": '<circle cx="310" cy="250" r="175" fill="var(--surface2)"/><path d="M230 160h160v115c0 62-34 96-80 96s-80-34-80-96z" fill="var(--accent)"/><ellipse cx="310" cy="160" rx="80" ry="28" fill="#3b1e13" stroke="var(--accent2)" stroke-width="8"/><path d="M390 195c85-20 98 90 8 92" fill="none" stroke="var(--accent2)" stroke-width="18" stroke-linecap="round"/><path d="M270 115c-30-45 30-60 0-98M320 115c-30-45 30-60 0-98M370 115c-30-45 30-60 0-98" fill="none" stroke="var(--accent2)" stroke-width="9" stroke-linecap="round"/>',
        "automotive": '<rect x="80" y="85" width="460" height="300" rx="30" fill="var(--surface2)" stroke="var(--line)"/><path d="M140 285l35-80c10-23 30-36 58-39h155c27 2 47 16 59 39l38 80" fill="none" stroke="var(--accent)" stroke-width="12"/><path d="M125 285h370v48H125z" fill="var(--bg)" stroke="var(--accent)" stroke-width="7"/><circle cx="195" cy="343" r="34" fill="var(--bg)" stroke="var(--text)" stroke-width="8"/><circle cx="425" cy="343" r="34" fill="var(--bg)" stroke="var(--text)" stroke-width="8"/><path d="M220 187l32-20h116l32 20" fill="none" stroke="var(--muted)" stroke-width="6"/>',
        "restaurant": '<circle cx="310" cy="245" r="180" fill="var(--surface2)"/><ellipse cx="310" cy="275" rx="145" ry="55" fill="var(--text)"/><ellipse cx="310" cy="260" rx="105" ry="35" fill="var(--accent)"/><path d="M230 255c30-45 55 20 80-12 28-35 52 35 80-10" fill="none" stroke="var(--bg)" stroke-width="13" stroke-linecap="round"/>',
        "salon": '<circle cx="310" cy="230" r="170" fill="var(--surface2)"/><path d="M230 95c-75 105-50 240 80 300 130-60 155-195 80-300" fill="none" stroke="var(--accent)" stroke-width="16"/><circle cx="245" cy="220" r="27" fill="none" stroke="var(--accent2)" stroke-width="9"/><circle cx="375" cy="220" r="27" fill="none" stroke="var(--accent2)" stroke-width="9"/><path d="M265 240l90 90M355 240l-90 90" stroke="var(--accent)" stroke-width="11" stroke-linecap="round"/>',
        "fitness": '<circle cx="310" cy="230" r="170" fill="var(--surface2)"/><path d="M120 230h380" stroke="var(--text)" stroke-width="16"/><path d="M175 165v130M145 180v100M445 165v130M475 180v100" stroke="var(--accent)" stroke-width="24" stroke-linecap="round"/><path d="M260 355h100" stroke="var(--accent2)" stroke-width="8" stroke-linecap="round"/>',
        "retail": '<rect x="125" y="70" width="370" height="330" rx="34" fill="var(--surface2)"/><path d="M220 190c0-95 180-95 180 0" fill="none" stroke="var(--accent2)" stroke-width="13"/><path d="M175 175h270l-28 225H203z" fill="var(--accent)"/><path d="M240 275h140" stroke="var(--bg)" stroke-width="12" stroke-linecap="round"/>',
        "professional": '<rect x="175" y="55" width="270" height="350" rx="24" fill="var(--surface2)" stroke="var(--accent)" stroke-width="6"/><path d="M230 145h160M230 195h160M230 245h115" stroke="var(--muted)" stroke-width="12" stroke-linecap="round"/><path d="M225 315l55 50 110-120" fill="none" stroke="var(--accent)" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>',
        "general": '<circle cx="310" cy="230" r="170" fill="var(--surface2)"/><circle cx="310" cy="230" r="105" fill="none" stroke="var(--accent)" stroke-width="8"/><path d="M205 290l72-72 48 48 92-100" fill="none" stroke="var(--accent2)" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>',
    }
    return common + art.get(category, art["general"]) + "</svg>"


def get_design_strategy(category: str, request: str = "") -> dict[str, str]:
    strategies = {
        "coffee": {"template": "editorial", "cta": "visit-focused"},
        "automotive": {"template": "industrial", "cta": "booking-focused"},
        "restaurant": {"template": "culinary", "cta": "reservation-focused"},
        "salon": {"template": "luxury", "cta": "booking-focused"},
        "fitness": {"template": "athletic", "cta": "signup-focused"},
        "retail": {"template": "bento", "cta": "shopping-focused"},
        "professional": {"template": "structured", "cta": "consultation-focused"},
        "general": {"template": "modular", "cta": "contact-focused"},
    }
    strategy = dict(strategies.get(category, strategies["general"]))
    lower = _clean_request(request).lower()
    if any(_contains_phrase(lower, x) for x in ("portfolio", "photography", "photographer", "creative portfolio")):
        strategy["template"] = "portfolio"
    if any(_contains_phrase(lower, x) for x in ("luxury", "premium", "exclusive", "high-end")):
        strategy["template"] = "luxury"
    return strategy


def _nav(label: str = "Explore") -> str:
    initial = esc(label[:1].upper())
    return f'''<nav class="nav" aria-label="Primary navigation"><div class="wrap nav-inner"><a class="brand" href="#top" aria-label="{esc(label)} home"><span class="brand-mark">{initial}</span><span class="brand-name">{esc(label)}</span></a><div class="nav-center"><div class="nav-links" id="nav-links"><a href="#offer">Offer</a><a href="#about">About</a><a href="#contact">Contact</a></div></div><div class="nav-right"><a class="nav-cta" href="#contact">Get started <span>↗</span></a><button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav-links" aria-label="Open navigation">Menu <span>☰</span></button></div></div></nav>'''


def _item_cards(items: list[tuple[str, str]], numbered: bool = True) -> str:
    cards = []
    for i, (name, desc) in enumerate(items, 1):
        prefix = f'<span class="num">{i:02d}</span>' if numbered else '<span class="dot">•</span>'
        cards.append(f'<article class="card">{prefix}<div><h3>{esc(name)}</h3><p>{esc(desc)}</p></div><span class="card-arrow">→</span></article>')
    return "".join(cards)


PERSONALITY = {
    "coffee": ("CRAFT / COMFORT / CONVERSATION", "Warm drinks, easy moments, a place to linger."),
    "automotive": ("CHECK / FIX / DRIVE", "Clear diagnosis. Careful work. A confident return to the road."),
    "restaurant": ("TASTE / SHARE / RETURN", "Thoughtful plates, generous moments, a table worth sharing."),
    "salon": ("CARE / STYLE / CONFIDENCE", "Thoughtful care, polished details, confidence that feels like you."),
    "fitness": ("MOVE / BUILD / REPEAT", "Focused training, useful movement, progress you can feel."),
    "retail": ("DISCOVER / EDIT / CHOOSE", "A curated edit for people who know what they like."),
    "professional": ("CLARITY / EXPERTISE / ACTION", "Clear thinking, practical guidance, better next steps."),
    "general": ("CLEAR / DISTINCT / USEFUL", "A simple experience built around what customers need."),
}

def _hero_meta(category: str) -> str:
    label, desc = PERSONALITY.get(category, PERSONALITY["general"])
    parts = [x.strip() for x in label.split("/")]
    return '<div class="hero-meta"><span class="hero-meta-label">' + esc(parts[0]) + '</span><i></i><span>' + esc(parts[1]) + '</span><i></i><span>' + esc(parts[2]) + '</span><p>' + esc(desc) + '</p></div>'


def _layout_markup(plan: dict[str, Any], name: str, category: str, strategy: dict[str, str]) -> str:
    art = svg_art(category)
    items = plan["items"]
    title = esc(plan["headline"])
    sub = esc(plan["sub"])
    eyebrow = esc(plan["eyebrow"])
    cta = esc(plan["cta"])
    secondary = esc(plan["secondary"])
    section = esc(plan["section"])
    about_title, about_text = ABOUT.get(category, ABOUT["general"])
    name_e = esc(name)
    cards = _item_cards(items, numbered=category not in {"retail", "salon"})

    if strategy["template"] == "industrial":
        return f'''<section class="hero industrial-hero"><div class="hero-copy"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p class="lead">{sub}</p><div class="actions"><a class="btn primary" href="#contact">{cta} →</a><a class="btn ghost" href="#offer">{secondary}</a></div><div class="status-row"><span>01 / DIAGNOSE</span><span>02 / REPAIR</span><span>03 / RETURN</span></div>{_hero_meta(category)}</div><div class="hero-panel">{art}<div class="panel-tag">{esc(category.upper())} / SERVICE BAY</div></div></section><section class="section industrial-services" id="offer"><div class="wrap"><div class="section-head"><div><span class="kicker">{section.upper()}</span><h2>Built for the work.</h2></div><p>Clear service paths help visitors understand what happens next.</p></div><div class="service-grid">{cards}</div></div></section>'''

    if strategy["template"] == "culinary":
        return f'''<section class="hero culinary-hero"><div class="culinary-art">{art}<span class="floating-note">FRESH / THOUGHTFUL / LOCAL</span></div><div class="hero-copy"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p class="lead">{sub}</p><div class="actions"><a class="btn primary" href="#offer">{cta} →</a><a class="btn ghost" href="#contact">{secondary}</a></div></div></section><section class="section" id="offer"><div class="wrap"><div class="menu-heading"><span class="kicker">{section.upper()}</span><h2>Made for the table.</h2></div><div class="menu-list">{cards}</div></div></section>'''

    if strategy["template"] == "luxury":
        return f'''<section class="hero luxury-hero"><div class="hero-copy"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p class="lead">{sub}</p><div class="actions"><a class="btn primary" href="#contact">{cta} →</a><a class="btn ghost" href="#offer">{secondary}</a></div>{_hero_meta(category)}</div><div class="luxury-frame">{art}<span>CURATED / {esc(category.upper())}</span></div></section><section class="section" id="offer"><div class="wrap"><div class="luxury-heading"><span class="kicker">{section.upper()}</span><h2>Considered from first contact to final detail.</h2></div><div class="luxury-list">{cards}</div></div></section>'''

    if strategy["template"] == "athletic":
        return f'''<section class="hero athletic-hero"><div class="athletic-copy"><span class="eyebrow">{eyebrow}</span><h1>{title}</h1><p class="lead">{sub}</p><div class="actions"><a class="btn primary" href="#contact">{cta} →</a><a class="btn ghost" href="#offer">{secondary}</a></div>{_hero_meta(category)}</div><div class="athletic-art">{art}<div class="metric"><strong>01</strong><span>SHOW UP</span></div><div class="metric m2"><strong>02</strong><span>BUILD</span></div></div></section><section class="section" id="offer"><div class="wrap"><div class="section-head"><div><span class="kicker">{section.upper()}</span><h2>Train with intent.</h2></div><p>A direct, energetic structure built to move visitors toward action.</p></div><div class="program-grid">{cards}</div></div></section>'''

    if strategy["template"] == "bento":
        return f'''<section class="hero bento-hero"><div class="hero-copy"><span class="eyebrow">{eyebrow}</span><h1>{title}</h1><p class="lead">{sub}</p><div class="actions"><a class="btn primary" href="#offer">{cta} →</a><a class="btn ghost" href="#contact">{secondary}</a></div>{_hero_meta(category)}</div><div class="bento-art">{art}<div class="bento-tag">{esc(name_e)}</div></div></section><section class="section" id="offer"><div class="wrap"><div class="section-head"><div><span class="kicker">{section.upper()}</span><h2>Browse the collection.</h2></div><p>Visual grouping makes discovery faster without turning the page into a generic grid.</p></div><div class="bento-grid">{cards}</div></div></section>'''

    if strategy["template"] == "structured":
        return f'''<section class="hero structured-hero"><div class="hero-copy"><span class="eyebrow">{eyebrow}</span><h1>{title}</h1><p class="lead">{sub}</p><div class="actions"><a class="btn primary" href="#contact">{cta} →</a><a class="btn ghost" href="#offer">{secondary}</a></div>{_hero_meta(category)}</div><aside class="trust-panel"><div class="trust-icon">✓</div><strong>Clear next steps</strong><p>Understand the offer, see where you fit, then choose the next useful action.</p>{art}</aside></section><section class="section" id="offer"><div class="wrap"><div class="section-head"><div><span class="kicker">{section.upper()}</span><h2>Expertise, organized.</h2></div><p>Structured information helps professional visitors make decisions with less friction.</p></div><div class="expertise-list">{cards}</div></div></section>'''

    if strategy["template"] == "portfolio":
        return f'''<section class="hero portfolio-hero"><div class="portfolio-copy"><span class="eyebrow">{eyebrow}</span><h1>{title}</h1><p class="lead">{sub}</p><div class="actions"><a class="btn primary" href="#offer">{cta} →</a><a class="btn ghost" href="#contact">{secondary}</a></div>{_hero_meta(category)}</div><div class="portfolio-art">{art}</div></section><section class="section" id="offer"><div class="wrap"><div class="section-head"><div><span class="kicker">{section.upper()}</span><h2>Selected work & capabilities.</h2></div><p>A gallery-oriented composition for creative or portfolio-led requests.</p></div><div class="portfolio-grid">{cards}</div></div></section>'''

    # Editorial / modular default family.
    if strategy["template"] == "editorial":
        return f'''<section class="hero editorial-hero"><div class="hero-copy"><span class="eyebrow">{eyebrow}</span><h1>{title}</h1><p class="lead">{sub}</p><div class="actions"><a class="btn primary" href="#offer">{cta} →</a><a class="btn ghost" href="#contact">{secondary}</a></div>{_hero_meta(category)}</div><div class="editorial-art">{art}<span class="art-caption">{esc(category.upper())} / DETAIL / EXPERIENCE</span></div></section><section class="section" id="offer"><div class="wrap"><div class="section-head"><div><span class="kicker">{section.upper()}</span><h2>Thoughtfully presented.</h2></div><p>Clear choices and a calm visual rhythm built around the customer experience.</p></div><div class="editorial-grid">{cards}</div></div></section>'''

    return f'''<section class="hero modular-hero"><div class="hero-copy"><span class="eyebrow">{eyebrow}</span><h1>{title}</h1><p class="lead">{sub}</p><div class="actions"><a class="btn primary" href="#offer">{cta} →</a><a class="btn ghost" href="#contact">{secondary}</a></div>{_hero_meta(category)}</div><div class="modular-art">{art}<span>{esc(category.upper())} / DETAIL / EXPERIENCE</span></div></section><section class="section" id="offer"><div class="wrap"><div class="section-head"><div><span class="kicker">{section.upper()}</span><h2>What matters, made clear.</h2></div><p>A flexible business-first layout with a strong visual hierarchy.</p></div><div class="modular-grid">{cards}</div></div></section>'''


def render(plan: dict[str, Any], name: str, category: str, request: str = "") -> str:
    strategy = get_design_strategy(category, request)
    theme = THEMES.get(category, THEMES["general"])
    about_title, about_text = ABOUT.get(category, ABOUT["general"])
    body = _layout_markup(plan, name, category, strategy)
    name_e = esc(name)
    brand_traits = {
        "coffee": ("Warm editorial", "Menu-first", "Visit-focused"),
        "automotive": ("Technical", "Service-first", "Action-led"),
        "restaurant": ("Sensory", "Menu-led", "Experience-first"),
        "salon": ("Refined", "Care-led", "Booking-focused"),
        "fitness": ("Energetic", "Program-first", "Action-led"),
        "retail": ("Curated", "Collection-led", "Discovery-first"),
        "professional": ("Calm", "Expertise-led", "Trust-focused"),
        "general": ("Clear", "Modern", "Customer-first"),
    }
    chips = "".join(f'<span>{esc(x)}</span>' for x in brand_traits.get(category, brand_traits["general"]))
    contact = f'''<section class="section contact" id="contact"><div class="wrap contact-box"><div><span class="kicker">NEXT STEP</span><h2>Make the next step feel easy.</h2><p>Explore the offer, understand what fits, and move naturally toward the action that matters.</p></div><a class="btn primary" href="#offer">{esc(plan["cta"])} ↗</a></div></section>'''
    about = f'''<section class="section about" id="about"><div class="wrap about-grid"><div class="about-art">{svg_art(category)}</div><div><span class="kicker">THE EXPERIENCE</span><h2>{esc(about_title)}</h2><p>{esc(about_text)}</p><div class="chips">{chips}</div></div></div></section>'''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(name)} — {esc(category.title())}</title>
<meta name="description" content="{esc(plan['sub'])}">
<style>
:root{{--bg:{theme['bg']};--surface:{theme['surface']};--surface2:{theme['surface2']};--text:{theme['text']};--muted:{theme['muted']};--accent:{theme['accent']};--accent2:{theme['accent2']};--line:{theme['line']}}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;background:radial-gradient(circle at 82% 6%,color-mix(in srgb,var(--accent) 8%,transparent),transparent 28%),radial-gradient(circle at 12% 34%,rgba(255,255,255,.025),transparent 24%),var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5;overflow-x:hidden}}
body:before{{content:"";position:fixed;inset:0;pointer-events:none;opacity:.22;background:linear-gradient(rgba(255,255,255,.018) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.018) 1px,transparent 1px);background-size:64px 64px;mask-image:linear-gradient(to bottom,black,transparent 72%);z-index:-1}}
a{{color:inherit;text-decoration:none}}
button{{font:inherit}}
.wrap{{width:min(1180px,calc(100% - 40px));margin:auto}}
.nav{{position:sticky;top:0;z-index:50;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(18px);border-bottom:1px solid color-mix(in srgb,var(--line) 75%,transparent);box-shadow:0 10px 35px rgba(0,0,0,.08)}}
.nav-inner{{min-height:78px;display:flex;align-items:center;gap:22px;justify-content:space-between}}
.nav-center{{display:flex;align-items:center;justify-content:center;flex:1}}
.nav-right{{display:flex;align-items:center;gap:10px}}
.brand{{display:flex;align-items:center;gap:12px;font-weight:950;letter-spacing:-.04em;min-width:180px}}
.brand-name{{font-size:15px}}
.brand-mark{{width:42px;height:42px;border-radius:14px;background:linear-gradient(145deg,var(--accent2),var(--accent));color:var(--bg);display:grid;place-items:center;box-shadow:0 10px 26px color-mix(in srgb,var(--accent) 22%,transparent);font-size:14px}}
.nav-links{{display:flex;gap:5px;color:var(--muted);font-size:13px}}
.nav-links a{{padding:9px 12px;border-radius:999px;transition:color .2s ease,background .2s ease,transform .2s ease}}
.nav-links a:hover{{color:var(--text);background:var(--surface);transform:translateY(-1px)}}
.nav-cta,.btn{{display:inline-flex;align-items:center;justify-content:center;gap:9px;padding:13px 18px;border:1px solid var(--line);border-radius:14px;font-weight:850;transition:transform .2s ease,background .2s ease,border-color .2s ease,box-shadow .2s ease}}
.nav-cta,.primary{{background:linear-gradient(135deg,var(--accent2),var(--accent));color:var(--bg);border-color:transparent;box-shadow:0 10px 28px color-mix(in srgb,var(--accent) 18%,transparent)}}
.btn:hover,.nav-cta:hover{{transform:translateY(-3px);box-shadow:0 14px 30px rgba(0,0,0,.18)}}
.btn:focus-visible,.nav-cta:focus-visible,.nav-links a:focus-visible,.menu-btn:focus-visible{{outline:2px solid var(--accent2);outline-offset:3px}}
.ghost{{background:color-mix(in srgb,var(--surface) 78%,transparent)}}
.ghost:hover{{border-color:var(--accent);background:var(--surface2)}}
.menu-btn{{display:none;background:var(--surface);border:1px solid var(--line);color:var(--text);border-radius:12px;padding:9px 12px;cursor:pointer}}
.hero{{min-height:660px;padding:78px 0 64px;display:grid;gap:58px;align-items:center;position:relative;overflow:hidden}}
.hero:before{{content:"";position:absolute;width:420px;height:420px;border-radius:50%;background:color-mix(in srgb,var(--accent) 8%,transparent);filter:blur(70px);top:8%;right:-10%;pointer-events:none}}
.hero-copy{{max-width:760px;position:relative;z-index:2}}
.eyebrow,.kicker{{font-size:11px;font-weight:950;letter-spacing:.2em;color:var(--accent);text-transform:uppercase}}
h1{{font-size:clamp(56px,7.2vw,108px);line-height:.9;letter-spacing:-.075em;margin:20px 0 26px}}
.lead{{font-size:clamp(17px,1.6vw,20px);color:var(--muted);max-width:680px;line-height:1.7}}
.actions{{display:flex;gap:11px;flex-wrap:wrap;margin-top:30px}}
.art{{width:min(100%,560px);height:auto;filter:drop-shadow(0 30px 50px rgba(0,0,0,.25));position:relative;z-index:2}}
.hero-meta{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:30px;color:var(--muted);font-size:10px;font-weight:900;letter-spacing:.12em}}
.hero-meta i{{width:4px;height:4px;border-radius:50%;background:var(--accent);display:block}}
.hero-meta-label{{color:var(--text)}}
.hero-meta p{{flex-basis:100%;max-width:620px;margin:4px 0 0;color:var(--muted);font-size:12px;line-height:1.6;font-weight:500;letter-spacing:0}}
.section{{padding:105px 0;position:relative}}
.section + .section{{border-top:1px solid color-mix(in srgb,var(--line) 38%,transparent)}}
.section-head{{display:flex;justify-content:space-between;align-items:end;gap:50px;margin-bottom:46px}}
.section-head h2,.about h2,.contact h2{{font-size:clamp(44px,5.4vw,78px);line-height:.94;letter-spacing:-.068em;margin:12px 0 0}}
.section-head p,.about p,.contact p{{color:var(--muted);max-width:480px;font-size:17px;line-height:1.65}}
.card{{position:relative;background:linear-gradient(145deg,color-mix(in srgb,var(--surface2) 55%,var(--surface)),var(--surface));border:1px solid var(--line);padding:30px;min-height:235px;display:flex;flex-direction:column;justify-content:space-between;transition:transform .25s cubic-bezier(.2,.7,.2,1),background .25s ease,border-color .25s ease,box-shadow .25s ease;overflow:hidden}}
.card:before{{content:"";position:absolute;inset:0 auto auto 0;width:100%;height:2px;background:linear-gradient(90deg,var(--accent),transparent);opacity:.55}}
.card:after{{content:"";position:absolute;width:130px;height:130px;border-radius:50%;right:-70px;bottom:-75px;background:color-mix(in srgb,var(--accent) 9%,transparent);filter:blur(2px);transition:transform .3s ease}}
.card:hover{{transform:translateY(-7px);background:linear-gradient(145deg,var(--surface2),var(--surface));border-color:color-mix(in srgb,var(--accent) 70%,var(--line));box-shadow:0 20px 45px rgba(0,0,0,.18)}}
.card:hover:after{{transform:scale(1.35)}}
.card h3{{font-size:22px;line-height:1.15;margin:24px 0 9px;letter-spacing:-.03em}}
.card p{{margin:0;color:var(--muted);max-width:340px;line-height:1.65}}
.num,.dot{{color:var(--accent);font-weight:950;font-size:12px;letter-spacing:.12em}}
.card-arrow{{align-self:flex-end;color:var(--accent);font-size:23px}}
.about-grid{{display:grid;grid-template-columns:.9fr 1.1fr;gap:70px;align-items:center}}
.about-art{{min-height:470px;border:1px solid var(--line);border-radius:34px;background:radial-gradient(circle at 50% 40%,color-mix(in srgb,var(--accent) 10%,transparent),transparent 40%),linear-gradient(145deg,var(--surface2),var(--surface));display:grid;place-items:center;overflow:hidden;position:relative;box-shadow:0 25px 60px rgba(0,0,0,.14)}}
.about-art:before,.about-art:after{{content:"";position:absolute;border:1px solid var(--line);border-radius:50%;opacity:.55}}
.about-art:before{{width:330px;height:330px}}
.about-art:after{{width:500px;height:500px}}
.about-art .art{{width:65%}}
.chips{{display:flex;gap:8px;flex-wrap:wrap;margin-top:26px}}
.chips span{{padding:8px 11px;border:1px solid var(--line);border-radius:999px;background:var(--surface);color:var(--muted);font-size:12px}}
.contact-box{{position:relative;overflow:hidden;border:1px solid var(--line);background:radial-gradient(circle at 85% 30%,color-mix(in srgb,var(--accent) 13%,transparent),transparent 32%),linear-gradient(145deg,var(--surface2),var(--surface));border-radius:34px;padding:70px;display:flex;align-items:end;justify-content:space-between;gap:40px;box-shadow:0 30px 80px rgba(0,0,0,.16)}}
.contact-box:before{{content:"";position:absolute;width:260px;height:260px;border:1px solid color-mix(in srgb,var(--accent) 30%,var(--line));border-radius:50%;right:-110px;top:-110px}}
.contact-box:after{{content:"↗";position:absolute;right:36px;top:30px;color:color-mix(in srgb,var(--accent2) 70%,transparent);font-size:40px;font-weight:200}}
.contact-box h2{{max-width:820px;position:relative;z-index:1}}
.contact-box .btn{{white-space:nowrap;min-width:170px}}
.contact-box p{{position:relative;z-index:1}}
footer{{border-top:1px solid var(--line);padding:32px 0 54px;color:var(--muted);font-size:12px;display:flex;justify-content:space-between;gap:20px;letter-spacing:.01em}}
/* REAL LAYOUT VARIANTS */
.editorial-hero{{grid-template-columns:1.15fr .85fr}}
.editorial-art{{min-height:610px;border:1px solid var(--line);border-radius:42px;background:radial-gradient(circle at 60% 20%,color-mix(in srgb,var(--accent) 18%,transparent),transparent 36%),linear-gradient(145deg,var(--surface2),var(--surface));display:grid;place-items:center;position:relative;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.18)}}
.editorial-art:before,.hero-panel:before,.culinary-art:before,.luxury-frame:before,.athletic-art:before,.bento-art:before,.trust-panel:before,.portfolio-art:before,.modular-art:before{{content:"";position:absolute;inset:18px;border:1px solid color-mix(in srgb,var(--line) 70%,transparent);border-radius:inherit;pointer-events:none}}
.art-caption,.modular-art>span,.bento-tag,.luxury-frame>span,.panel-tag{{position:absolute;top:24px;left:25px;color:var(--muted);font-size:11px;font-weight:900;letter-spacing:.14em}}
.editorial-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:24px;overflow:hidden}}
.industrial-hero{{grid-template-columns:.8fr 1.2fr}}
.industrial-hero .hero-copy{{order:2}}
.hero-panel{{order:1;min-height:600px;background:linear-gradient(145deg,var(--surface2),var(--surface));border:1px solid var(--line);border-radius:20px;display:grid;place-items:center;position:relative;overflow:hidden}}
.service-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}
.status-row{{display:flex;gap:18px;flex-wrap:wrap;color:var(--muted);font-size:11px;font-weight:900;letter-spacing:.13em;margin-top:30px}}
.culinary-hero{{grid-template-columns:1fr 1fr;align-items:stretch}}
.culinary-art{{min-height:620px;position:relative;border-radius:38px;overflow:hidden;background:linear-gradient(145deg,var(--surface2),var(--surface));display:grid;place-items:center;border:1px solid var(--line)}}
.floating-note{{position:absolute;bottom:22px;left:25px;color:var(--muted);font-size:11px;letter-spacing:.16em;font-weight:900}}
.menu-heading{{max-width:700px;margin-bottom:42px}}
.menu-list{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}
.luxury-hero{{grid-template-columns:1.1fr .9fr}}
.luxury-frame{{min-height:620px;border:1px solid var(--line);border-radius:120px 120px 30px 30px;background:linear-gradient(160deg,var(--surface2),var(--surface));display:grid;place-items:center;position:relative;overflow:hidden}}
.luxury-list{{display:grid;grid-template-columns:1fr;gap:0;border-top:1px solid var(--line)}}
.luxury-list .card{{border-top:0;border-left:0;border-right:0;min-height:150px;display:grid;grid-template-columns:80px 1fr 30px;align-items:center}}
.athletic-hero{{grid-template-columns:1fr 1fr}}
.athletic-art{{min-height:600px;border:1px solid var(--line);border-radius:30px;background:linear-gradient(145deg,var(--surface2),var(--surface));display:grid;place-items:center;position:relative;overflow:hidden}}
.metric{{position:absolute;top:22px;right:22px;border:1px solid var(--line);background:var(--bg);padding:12px 15px;border-radius:15px;display:flex;gap:10px;align-items:baseline}}
.metric strong{{font-size:24px;color:var(--accent)}}
.metric span{{font-size:10px;letter-spacing:.14em;color:var(--muted);font-weight:900}}
.metric.m2{{top:auto;right:auto;bottom:22px;left:22px}}
.program-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.bento-hero{{grid-template-columns:1fr .9fr}}
.bento-art{{min-height:560px;position:relative;border:1px solid var(--line);border-radius:30px;background:var(--surface2);display:grid;place-items:center;overflow:hidden}}
.bento-tag{{top:auto;left:auto;bottom:20px;right:20px;background:var(--bg);padding:10px 13px;border-radius:12px}}
.bento-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.bento-grid .card:nth-child(1){{grid-column:span 2;grid-row:span 2;min-height:330px}}
.bento-grid .card:nth-child(4){{grid-column:span 2}}
.structured-hero{{grid-template-columns:1.2fr .8fr}}
.trust-panel{{min-height:560px;border:1px solid var(--line);border-radius:24px;background:var(--surface);padding:30px;position:relative;overflow:hidden}}
.trust-icon{{width:50px;height:50px;border-radius:15px;background:var(--accent);color:var(--bg);display:grid;place-items:center;font-weight:950;font-size:24px}}
.trust-panel strong{{display:block;margin-top:22px;font-size:24px}}
.trust-panel p{{color:var(--muted);max-width:350px}}
.trust-panel .art{{position:absolute;right:-100px;bottom:-50px;width:360px;opacity:.55}}
.expertise-list{{border-top:1px solid var(--line)}}
.expertise-list .card{{border-top:0;border-left:0;border-right:0;min-height:150px;display:grid;grid-template-columns:80px 1fr 30px;align-items:center}}
.portfolio-hero{{grid-template-columns:1fr 1fr}}
.portfolio-art{{min-height:580px;background:repeating-linear-gradient(135deg,var(--surface),var(--surface) 30px,var(--surface2) 30px,var(--surface2) 60px);border:1px solid var(--line);border-radius:18px;display:grid;place-items:center}}
.portfolio-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.portfolio-grid .card{{min-height:260px}}
.modular-hero{{grid-template-columns:1.05fr .95fr}}
.modular-art{{min-height:560px;border:1px solid var(--line);border-radius:34px;background:radial-gradient(circle at 50% 50%,rgba(255,255,255,.06),transparent 38%),var(--surface);display:grid;place-items:center;position:relative;overflow:hidden}}
.modular-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
@media(max-width:900px){{.nav-center{{justify-content:flex-end}}.nav-links{{display:none;position:absolute;left:12px;right:12px;top:calc(100% + 8px);padding:10px;background:color-mix(in srgb,var(--surface) 96%,transparent);border:1px solid var(--line);border-radius:18px;box-shadow:0 22px 50px rgba(0,0,0,.25);flex-direction:column;gap:3px}}.nav.open .nav-links{{display:flex}}.menu-btn{{display:inline-flex;align-items:center;gap:8px}}.nav-cta{{display:none}}.hero,.industrial-hero,.culinary-hero,.luxury-hero,.athletic-hero,.bento-hero,.structured-hero,.portfolio-hero,.modular-hero,.about-grid{{grid-template-columns:1fr}}.industrial-hero .hero-copy{{order:1}}.hero-panel{{order:2}}.editorial-grid,.program-grid,.modular-grid,.portfolio-grid,.service-grid,.menu-list{{grid-template-columns:1fr 1fr}}.bento-grid{{grid-template-columns:1fr 1fr}}.bento-grid .card:nth-child(1),.bento-grid .card:nth-child(4){{grid-column:span 2}}.section-head{{display:block}}.section-head p{{margin-top:18px}}}}
@media(max-width:600px){{.wrap{{width:calc(100% - 24px)}}.nav-inner{{min-height:68px}}.hero{{padding:62px 0 58px;min-height:auto}}h1{{font-size:clamp(50px,15vw,78px)}}.lead{{font-size:17px}}.editorial-art,.hero-panel,.culinary-art,.luxury-frame,.athletic-art,.bento-art,.trust-panel,.portfolio-art,.modular-art{{min-height:380px;border-radius:26px}}.editorial-grid,.service-grid,.menu-list,.program-grid,.portfolio-grid,.modular-grid,.bento-grid{{grid-template-columns:1fr}}.bento-grid .card:nth-child(1),.bento-grid .card:nth-child(4){{grid-column:span 1}}.luxury-list .card,.expertise-list .card{{grid-template-columns:55px 1fr 25px}}.contact-box{{display:block;padding:42px 24px;border-radius:26px}}.contact-box .btn{{margin-top:24px;width:100%}}.about-art{{min-height:320px}}footer{{display:block}}footer span{{display:block;margin-top:8px}}}}
 .card,.about-grid,.contact-box{{animation:riseIn .65s cubic-bezier(.2,.7,.2,1) both}}
.card:nth-child(2){{animation-delay:.05s}}
.card:nth-child(3){{animation-delay:.1s}}
.card:nth-child(4){{animation-delay:.15s}}
.card:nth-child(5){{animation-delay:.2s}}
.card:nth-child(6){{animation-delay:.25s}}
@keyframes riseIn{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@media(prefers-reduced-motion:reduce){{*,*::before,*::after{{scroll-behavior:auto!important;animation:none!important;transition:none!important}}}}
</style>
</head>
<body>
{_nav(name)}
<main id="top">
<div class="wrap">{body}</div>
{about}
{contact}
</main>
<footer class="wrap"><span>© {name_e}. Built for a clear customer experience.</span><span>Local-first · Responsive · Self-contained</span></footer>
<script>
(function() {{
  const nav = document.querySelector('.nav');
  const button = document.querySelector('.menu-btn');
  const links = document.getElementById('nav-links');
  if (nav && button && links) {{
    button.addEventListener('click', function() {{
      const open = button.getAttribute('aria-expanded') === 'true';
      button.setAttribute('aria-expanded', String(!open));
      nav.classList.toggle('open', !open);
    }});
    links.querySelectorAll('a').forEach(function(link) {{
      link.addEventListener('click', function() {{
        nav.classList.remove('open');
        button.setAttribute('aria-expanded', 'false');
      }});
    }});
  }}
}})();
</script>
</body>
</html>'''


class _Validator(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.errors: list[str] = []
        self.script_count = 0
        self.style_count = 0

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        self.tags.append(tag)
        attrs_dict = dict(attrs)
        if "id" in attrs_dict:
            if attrs_dict["id"] in self.ids:
                self.errors.append(f"duplicate id: {attrs_dict['id']}")
            self.ids.add(attrs_dict["id"])
        if "href" in attrs_dict and attrs_dict["href"]:
            self.hrefs.append(attrs_dict["href"])
        if tag == "script": self.script_count += 1
        if tag == "style": self.style_count += 1


def validate_website_html(html: str) -> tuple[bool, str]:
    if not html or not html.lstrip().lower().startswith("<!doctype html"):
        return False, "Document must start with <!DOCTYPE html>."
    lower = html.lower()
    required = ["<html", "<head", "<body", "</html>", "<style", "</style>", "<script", "</script>"]
    missing = [x for x in required if x not in lower]
    if missing:
        return False, "Missing required markers: " + ", ".join(missing)
    forbidden = ["<img", "<picture", "<source", "<iframe", "<embed", "<object", "<frame", "<frameset", "<video", "<audio", "background-image", "@import", "url(", "<link"]
    hits = [x for x in forbidden if x in lower]
    if re.search(r"https?://", lower):
        return False, "External URL found; self-contained websites must not load remote resources."
    if re.search(r"(?:^|[\"'\s])(?:[^\"'\s]+\.(?:jpg|jpeg|png|webp|gif|avif|bmp|ico|tiff|svg))(?:$|[\"'\s])", lower):
        return False, "External/local asset filename found."
    if hits:
        return False, "Forbidden features: " + ", ".join(hits)
    parser = _Validator()
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:
        return False, f"HTML parser error: {exc}"
    if parser.errors:
        return False, "; ".join(parser.errors)
    target_ids = {href[1:] for href in parser.hrefs if href.startswith("#") and len(href) > 1}
    missing_targets = sorted(target_ids - parser.ids)
    if missing_targets:
        return False, "Broken internal links: " + ", ".join(missing_targets)
    return True, ""


def save_html(content: str, filename: str = "shaqs_website.html") -> Path:
    safe_name = Path(str(filename or "shaqs_website.html")).name
    if Path(safe_name).suffix.lower() != ".html":
        safe_name += ".html"
    output = WEBSITES_DIR / safe_name
    output.write_text(str(content), encoding="utf-8")
    return output


def create_website(request: str, filename: str = "shaqs_website.html", open_browser: bool = True) -> str:
    request = _clean_request(request)
    if not request:
        return "Website creation failed: empty request."
    category = detect_category(request)
    name = extract_name(request, category)
    strategy = get_design_strategy(category, request)
    plan = plan_with_ai(request, category, name)
    html = render(plan, name, category, request)
    ok, error = validate_website_html(html)
    if not ok:
        return f"Website creation failed quality validation: {error}"
    output = save_html(html, filename)
    if open_browser:
        try:
            webbrowser.open(output.resolve().as_uri())
        except Exception:
            pass
    print("=" * 64)
    print("SHAQS WEBSITE BUILDER")
    print("=" * 64)
    print(f"Business : {name}")
    print(f"Category : {category}")
    print(f"Layout   : {strategy['template']}")
    print(f"File     : {output.resolve()}")
    print("Validation: PASS")
    print("=" * 64)
    return f"Website created successfully at: {output.resolve()}"


def build_website(request: str, filename: str = "shaqs_website.html") -> str:
    return create_website(request, filename)


def create_html(content: str, filename: str = "shaqs_website.html"):
    value = str(content or "").lstrip()
    if value.lower().startswith("<!doctype html"):
        ok, error = validate_website_html(value)
        if not ok:
            raise ValueError(error)
        return save_html(value, filename)
    return create_website(value, filename)


def smoke_test_parser() -> str:
    tests = [
        ("Build a website for Royal Car Service, an automotive garage specializing in car servicing, diagnostics, repairs, and manual-to-automatic transmission conversions.", "Royal Car Service", "automotive"),
        ("Build a website for a fitness gym called Titan Fitness. It offers personal training, strength training, weight loss programs, and group fitness classes.", "Titan Fitness", "fitness"),
        ("Build a website for a coffee shop named KOPIEEE.", "KOPIEEE", "coffee"),
        ("Create a website for Royal Car Service", "Royal Car Service", "automotive"),
        ("Make a site called Titan Fitness for personal training and group fitness.", "Titan Fitness", "fitness"),
        ("Create a website for KOPIEEE. IMPORTANT CONTEXT RULE = IGNORE unrelated previous website projects.", "KOPIEEE", "coffee"),
    ]
    for request, expected_name, expected_category in tests:
        category = detect_category(request)
        name = extract_name(request, category)
        assert category == expected_category, (category, expected_category)
        assert name == expected_name, (name, expected_name)
    return "Parser smoke tests passed."


if __name__ == "__main__":
    print(smoke_test_parser())
    print(create_website("Build a website for a coffee shop named KOPIEEE", open_browser=False))
