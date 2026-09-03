import re
from typing import Any
from .rag import retrieve, enrich

PATTERNS = {
    "non_consensual_intimate_image": [
        r"nude", r"naked", r"intimate image", r"private photo", r"private video",
        r"sexual photo", r"sexual video", r"shared.*without.*consent", r"posted.*without.*consent"
    ],
    "deepfake_or_synthetic_media": [
        r"deepfake", r"synthetic", r"ai[- ]generated", r"fake audio", r"fake video",
        r"voice clone", r"generated voice", r"fabricated video"
    ],
    "impersonation": [r"impersonat", r"pretend(ed)? to be me", r"fake account", r"my account"],
    "harassment_or_stalking": [
        r"harass", r"stalk", r"follow(ed|ing)? me", r"constant messages", r"won't stop",
        r"keeps contacting", r"watching me"
    ],
    "doxxing_or_privacy": [r"doxx", r"home address", r"phone number", r"personal details", r"private information"],
    "threats_or_incitement": [
        r"threat", r"kill me", r"hurt me", r"violence", r"come after me", r"attack me"
    ],
    "sextortion_or_extortion": [r"extort", r"sextort", r"pay.*or", r"money.*or.*share", r"send money"],
    "cyberbullying": [r"bully", r"humiliat", r"pile[- ]on", r"targeted online abuse"],
    "coercive_or_domestic_abuse": [
        r"partner", r"ex[- ]partner", r"boyfriend", r"girlfriend", r"husband", r"wife",
        r"controlling", r"coerc", r"domestic"
    ]
}

def classify(text: str) -> list[str]:
    found = []
    low = text.lower()
    for label, patterns in PATTERNS.items():
        if any(re.search(p, low) for p in patterns):
            found.append(label)
    return found

def assess(incident: dict[str, Any]) -> dict[str, Any]:
    combined = " ".join([
        incident.get("description", ""),
        incident.get("relationship", ""),
        incident.get("platform", "")
    ])
    categories = classify(combined)

    urgency = "low"
    if any(x in categories for x in ["threats_or_incitement", "sextortion_or_extortion"]):
        urgency = "high"
    elif categories:
        urgency = "medium"
    if incident.get("immediate_danger") is True:
        urgency = "high"

    query_terms = " ".join(categories + [
        "GBV" if incident.get("relationship") in {"partner", "ex-partner", "family"} else "",
        incident.get("description", "")
    ])
    retrieved = enrich(retrieve(query_terms, limit=6))

    actions = [
        "Preserve the original evidence and keep a dated record of what happened.",
        "Avoid escalating contact with the alleged perpetrator if doing so could increase risk.",
        "Use the platform's reporting and safety tools where appropriate."
    ]
    if "non_consensual_intimate_image" in categories:
        actions.append("Consider asking the relevant service provider to remove or disable access to the material.")
    if "harassment_or_stalking" in categories:
        actions.append("Consider whether a protection-order route may be relevant.")
    if "threats_or_incitement" in categories or incident.get("immediate_danger"):
        actions.insert(0, "If there is immediate danger, seek emergency assistance now.")
    if incident.get("relationship") in {"partner", "ex-partner", "family"}:
        actions.append("Because the relationship context may be relevant to GBV/domestic-violence protections, consider specialist GBV support.")

    gbv = incident.get("relationship") in {"partner", "ex-partner", "family"} or any(
        c in categories for c in ["coercive_or_domestic_abuse"]
    )

    return {
        "categories": categories,
        "urgency": urgency,
        "gbv_relevant": gbv,
        "actions": actions,
        "retrieved_sources": retrieved,
        "legal_boundary": "This is issue spotting and source retrieval, not a legal determination. The facts and statutory elements must be assessed by an appropriate authority or legal professional."
    }
