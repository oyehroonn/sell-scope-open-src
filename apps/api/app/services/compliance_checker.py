"""Compliance Checker Service - Pre-submission review risk assessment"""

from typing import List, Dict, Any, Optional
import re


TRADEMARK_KEYWORDS = {
    "nike", "adidas", "puma", "reebok", "under armour",
    "apple", "iphone", "ipad", "macbook", "airpods",
    "google", "android", "chrome", "gmail", "youtube",
    "microsoft", "windows", "xbox", "office",
    "amazon", "alexa", "kindle", "aws",
    "facebook", "instagram", "whatsapp", "meta",
    "twitter", "x",
    "tiktok", "snapchat", "linkedin",
    "coca-cola", "pepsi", "sprite", "fanta",
    "mcdonalds", "burger king", "starbucks", "subway",
    "disney", "marvel", "pixar", "star wars",
    "pokemon", "nintendo", "playstation", "sony",
    "ferrari", "lamborghini", "porsche", "bmw", "mercedes",
    "louis vuitton", "gucci", "prada", "chanel", "hermes",
    "rolex", "omega", "cartier",
    "nfl", "nba", "mlb", "nhl", "fifa", "olympics",
}

SENSITIVE_KEYWORDS = {
    "political", "politician", "president", "election",
    "religion", "religious", "church", "mosque", "temple",
    "nude", "naked", "explicit", "adult",
    "weapon", "gun", "rifle", "pistol", "knife",
    "drugs", "cannabis", "marijuana", "cocaine",
    "violence", "violent", "blood", "gore",
    "hate", "racist", "discrimination",
}

SPAM_PATTERNS = [
    r"buy\s+now",
    r"free\s+download",
    r"click\s+here",
    r"limited\s+time",
    r"act\s+now",
    r"cheap\s+price",
    r"best\s+quality",
]


def check_metadata_compliance(
    title: str,
    keywords: List[str],
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Check metadata for compliance issues"""
    
    issues = []
    warnings = []
    risk_score = 0
    
    title_lower = title.lower()
    for trademark in TRADEMARK_KEYWORDS:
        if trademark in title_lower:
            issues.append({
                "type": "trademark",
                "severity": "high",
                "message": f"Title contains potential trademark: '{trademark}'",
                "suggestion": f"Remove '{trademark}' from title or ensure content doesn't show the brand",
            })
            risk_score += 30
    
    for trademark in TRADEMARK_KEYWORDS:
        matching_keywords = [kw for kw in keywords if trademark in kw.lower()]
        if matching_keywords:
            issues.append({
                "type": "trademark",
                "severity": "high",
                "message": f"Keywords contain potential trademark: {matching_keywords}",
                "suggestion": "Remove brand-specific keywords unless content is generic",
            })
            risk_score += 20
    
    for sensitive in SENSITIVE_KEYWORDS:
        if sensitive in title_lower:
            warnings.append({
                "type": "sensitive_content",
                "severity": "medium",
                "message": f"Title contains sensitive term: '{sensitive}'",
                "suggestion": "Ensure content complies with Adobe Stock policies",
            })
            risk_score += 15
    
    if len(title) < 10:
        warnings.append({
            "type": "title_length",
            "severity": "low",
            "message": "Title is very short",
            "suggestion": "Use descriptive titles of 30-70 characters for better discoverability",
        })
        risk_score += 5
    elif len(title) > 200:
        warnings.append({
            "type": "title_length",
            "severity": "low",
            "message": "Title is very long",
            "suggestion": "Keep titles under 200 characters",
        })
        risk_score += 5
    
    if len(keywords) < 15:
        warnings.append({
            "type": "keyword_count",
            "severity": "medium",
            "message": f"Only {len(keywords)} keywords provided",
            "suggestion": "Add more relevant keywords (25-45 recommended)",
        })
        risk_score += 10
    elif len(keywords) > 49:
        warnings.append({
            "type": "keyword_count",
            "severity": "medium",
            "message": f"{len(keywords)} keywords provided",
            "suggestion": "Adobe Stock allows max 49 keywords",
        })
        risk_score += 10
    
    unique_keywords = set(kw.lower().strip() for kw in keywords)
    if len(unique_keywords) < len(keywords) * 0.9:
        warnings.append({
            "type": "duplicate_keywords",
            "severity": "low",
            "message": "Some keywords appear to be duplicates",
            "suggestion": "Remove duplicate or very similar keywords",
        })
        risk_score += 5
    
    all_text = f"{title} {' '.join(keywords)} {description or ''}"
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, all_text.lower()):
            issues.append({
                "type": "spam",
                "severity": "high",
                "message": f"Content contains spam-like pattern",
                "suggestion": "Remove promotional or spam-like language",
            })
            risk_score += 25
            break
    
    person_keywords = {"person", "people", "man", "woman", "child", "portrait", "face", "model"}
    if any(kw.lower() in person_keywords for kw in keywords):
        warnings.append({
            "type": "model_release",
            "severity": "medium",
            "message": "Content may include recognizable people",
            "suggestion": "Ensure you have a model release for any identifiable individuals",
        })
    
    property_keywords = {"building", "architecture", "interior", "property", "landmark"}
    if any(kw.lower() in property_keywords for kw in keywords):
        warnings.append({
            "type": "property_release",
            "severity": "medium",
            "message": "Content may include identifiable property",
            "suggestion": "Check if property release is required for identifiable private buildings",
        })
    
    risk_score = min(100, risk_score)
    
    if risk_score >= 50:
        risk_level = "high"
    elif risk_score >= 25:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "issues": issues,
        "warnings": warnings,
        "passed": len(issues) == 0,
        "recommendations": _generate_recommendations(issues, warnings),
    }


def _generate_recommendations(
    issues: List[Dict[str, Any]],
    warnings: List[Dict[str, Any]],
) -> List[str]:
    """Generate actionable recommendations"""
    
    recommendations = []
    
    if any(i["type"] == "trademark" for i in issues):
        recommendations.append(
            "Review content for any visible brand logos, trademarks, or identifiable products. "
            "Either remove them from the image or use generic descriptions."
        )
    
    if any(i["type"] == "spam" for i in issues):
        recommendations.append(
            "Remove any promotional or marketing language from metadata. "
            "Focus on descriptive, factual keywords."
        )
    
    if any(w["type"] == "keyword_count" for w in warnings):
        recommendations.append(
            "Optimize your keyword count: 25-45 relevant keywords performs best. "
            "Include both broad and specific terms."
        )
    
    if any(w["type"] == "model_release" for w in warnings):
        recommendations.append(
            "If people are recognizable in the image, upload the model release document "
            "during submission to avoid rejection."
        )
    
    if not recommendations:
        recommendations.append(
            "Metadata looks good! Consider A/B testing different title approaches "
            "to optimize discoverability."
        )
    
    return recommendations
