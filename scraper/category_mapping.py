"""
Adobe Stock Category Mapping and Niche Detection

This module provides:
1. Adobe Stock's category taxonomy with IDs
2. Keyword-to-category inference logic
3. Smart niche detection from keyword frequencies
"""

from typing import Dict, List, Any, Optional

# Adobe Stock's main categories with their IDs (from Adobe Stock URLs)
# These are the primary categories used for filtering on stock.adobe.com
ADOBE_STOCK_CATEGORIES = {
    "Animals": {
        "id": 1,
        "keywords": ["animal", "pet", "dog", "cat", "bird", "wildlife", "zoo", "farm", "horse", "fish", "insect", "butterfly", "lion", "tiger", "elephant"],
        "subcategories": ["Pets", "Wildlife", "Farm Animals", "Insects", "Marine Life", "Birds"]
    },
    "Buildings & Architecture": {
        "id": 2,
        "keywords": ["building", "architecture", "house", "home", "interior", "exterior", "room", "apartment", "skyscraper", "bridge", "landmark", "castle", "church", "temple"],
        "subcategories": ["Interiors", "Exteriors", "Landmarks", "Residential", "Commercial", "Historical"]
    },
    "Business": {
        "id": 3,
        "keywords": ["business", "office", "meeting", "corporate", "professional", "teamwork", "finance", "money", "bank", "investment", "startup", "entrepreneur", "handshake", "contract"],
        "subcategories": ["Office", "Meetings", "Finance", "Teamwork", "Leadership", "Startup"]
    },
    "Drinks": {
        "id": 4,
        "keywords": ["drink", "beverage", "coffee", "tea", "wine", "beer", "cocktail", "juice", "water", "soda", "smoothie", "espresso", "latte", "cappuccino", "alcohol", "bar"],
        "subcategories": ["Coffee & Tea", "Alcoholic", "Non-Alcoholic", "Smoothies", "Water"]
    },
    "Environment": {
        "id": 5,
        "keywords": ["environment", "ecology", "green", "sustainable", "recycle", "climate", "pollution", "conservation", "renewable", "solar", "wind", "earth", "planet"],
        "subcategories": ["Conservation", "Climate", "Renewable Energy", "Pollution", "Sustainability"]
    },
    "Food": {
        "id": 6,
        "keywords": ["food", "meal", "dish", "cuisine", "restaurant", "cooking", "recipe", "ingredient", "fruit", "vegetable", "meat", "fish", "dessert", "cake", "bread", "pizza", "pasta", "salad", "breakfast", "lunch", "dinner"],
        "subcategories": ["Fruits & Vegetables", "Meat & Seafood", "Desserts", "Baked Goods", "International Cuisine", "Healthy Food"]
    },
    "Graphic Resources": {
        "id": 7,
        "keywords": ["background", "texture", "pattern", "abstract", "geometric", "gradient", "wallpaper", "banner", "frame", "border", "template", "mockup", "overlay"],
        "subcategories": ["Backgrounds", "Textures", "Patterns", "Templates", "Mockups", "Overlays"]
    },
    "Hobbies & Leisure": {
        "id": 8,
        "keywords": ["hobby", "leisure", "game", "gaming", "craft", "diy", "garden", "fishing", "camping", "hiking", "photography", "music", "art", "painting", "reading", "collection"],
        "subcategories": ["Gaming", "Arts & Crafts", "Gardening", "Outdoor Activities", "Music", "Reading"]
    },
    "Industry": {
        "id": 9,
        "keywords": ["industry", "factory", "manufacturing", "construction", "engineering", "machinery", "production", "warehouse", "logistics", "supply chain", "worker", "safety"],
        "subcategories": ["Manufacturing", "Construction", "Engineering", "Logistics", "Mining", "Energy"]
    },
    "Landscapes": {
        "id": 10,
        "keywords": ["landscape", "scenery", "mountain", "beach", "ocean", "sea", "lake", "river", "forest", "desert", "valley", "hill", "sunset", "sunrise", "horizon", "panorama", "vista"],
        "subcategories": ["Mountains", "Beaches", "Forests", "Deserts", "Urban Landscapes", "Rural"]
    },
    "Lifestyle": {
        "id": 11,
        "keywords": ["lifestyle", "wellness", "fitness", "yoga", "meditation", "spa", "relaxation", "fashion", "beauty", "shopping", "luxury", "minimalist", "modern", "vintage"],
        "subcategories": ["Wellness", "Fitness", "Fashion", "Beauty", "Home Life", "Minimalism"]
    },
    "People": {
        "id": 12,
        "keywords": ["people", "person", "man", "woman", "child", "family", "couple", "group", "portrait", "face", "smile", "emotion", "diversity", "senior", "teenager", "baby"],
        "subcategories": ["Portraits", "Families", "Children", "Seniors", "Couples", "Groups", "Diversity"]
    },
    "Plants & Flowers": {
        "id": 13,
        "keywords": ["plant", "flower", "tree", "leaf", "garden", "botanical", "floral", "rose", "tulip", "sunflower", "bouquet", "blossom", "nature", "green", "foliage"],
        "subcategories": ["Flowers", "Trees", "Gardens", "Houseplants", "Botanical", "Foliage"]
    },
    "Culture & Religion": {
        "id": 14,
        "keywords": ["culture", "religion", "tradition", "holiday", "celebration", "festival", "christmas", "easter", "halloween", "thanksgiving", "wedding", "ceremony", "ritual", "spiritual"],
        "subcategories": ["Holidays", "Traditions", "Ceremonies", "Spiritual", "Cultural Events"]
    },
    "Science": {
        "id": 15,
        "keywords": ["science", "research", "laboratory", "experiment", "medical", "healthcare", "doctor", "hospital", "dna", "molecule", "chemistry", "biology", "physics", "space", "astronomy"],
        "subcategories": ["Medical", "Research", "Space", "Chemistry", "Biology", "Physics"]
    },
    "Social Issues": {
        "id": 16,
        "keywords": ["social", "community", "equality", "diversity", "inclusion", "protest", "activism", "charity", "volunteer", "education", "poverty", "health", "awareness"],
        "subcategories": ["Equality", "Community", "Education", "Health Awareness", "Activism"]
    },
    "Sports": {
        "id": 17,
        "keywords": ["sport", "athlete", "fitness", "gym", "running", "football", "soccer", "basketball", "tennis", "golf", "swimming", "cycling", "yoga", "exercise", "competition", "team"],
        "subcategories": ["Team Sports", "Individual Sports", "Fitness", "Extreme Sports", "Water Sports"]
    },
    "Technology": {
        "id": 18,
        "keywords": ["technology", "tech", "computer", "laptop", "phone", "smartphone", "tablet", "digital", "internet", "software", "app", "ai", "artificial intelligence", "robot", "data", "cloud", "cyber", "network"],
        "subcategories": ["Computers", "Mobile", "AI & Robotics", "Internet", "Software", "Data"]
    },
    "Transport": {
        "id": 19,
        "keywords": ["transport", "transportation", "car", "vehicle", "automobile", "truck", "bus", "train", "plane", "airplane", "aircraft", "ship", "boat", "motorcycle", "bicycle", "road", "highway"],
        "subcategories": ["Cars", "Aviation", "Maritime", "Public Transport", "Motorcycles", "Bicycles"]
    },
    "Travel": {
        "id": 20,
        "keywords": ["travel", "vacation", "holiday", "tourism", "tourist", "destination", "adventure", "explore", "journey", "trip", "hotel", "resort", "beach", "passport", "luggage", "backpack"],
        "subcategories": ["Destinations", "Adventure", "Tourism", "Hotels & Resorts", "Backpacking"]
    },
}

# Niche patterns for grouping related keywords into meaningful niches
NICHE_PATTERNS = {
    "Coffee & Cafe Culture": {
        "keywords": ["coffee", "cafe", "espresso", "latte", "cappuccino", "barista", "roast", "bean", "brew", "mocha", "americano"],
        "category": "Drinks",
        "description": "Coffee beverages, cafe scenes, and barista culture"
    },
    "Food Photography": {
        "keywords": ["food", "dish", "meal", "plate", "restaurant", "cuisine", "gourmet", "chef", "cooking", "recipe", "ingredient"],
        "category": "Food",
        "description": "Professional food styling and culinary photography"
    },
    "Business & Corporate": {
        "keywords": ["office", "business", "corporate", "meeting", "professional", "teamwork", "workplace", "desk", "conference"],
        "category": "Business",
        "description": "Office environments, business meetings, and corporate culture"
    },
    "Remote Work & Home Office": {
        "keywords": ["remote", "work from home", "home office", "laptop", "freelance", "digital nomad", "workspace"],
        "category": "Business",
        "description": "Remote work setups and home office environments"
    },
    "Nature & Outdoors": {
        "keywords": ["nature", "outdoor", "landscape", "mountain", "forest", "hiking", "adventure", "wilderness", "scenic"],
        "category": "Landscapes",
        "description": "Natural landscapes and outdoor adventures"
    },
    "Technology & Digital": {
        "keywords": ["technology", "digital", "computer", "laptop", "phone", "app", "software", "tech", "device", "screen"],
        "category": "Technology",
        "description": "Digital devices, software, and technology concepts"
    },
    "AI & Future Tech": {
        "keywords": ["ai", "artificial intelligence", "robot", "automation", "machine learning", "futuristic", "cyber", "neural"],
        "category": "Technology",
        "description": "AI, robotics, and futuristic technology"
    },
    "Health & Wellness": {
        "keywords": ["health", "wellness", "fitness", "yoga", "meditation", "spa", "relaxation", "healthy", "exercise", "workout"],
        "category": "Lifestyle",
        "description": "Health, fitness, and wellness lifestyle"
    },
    "Family & Relationships": {
        "keywords": ["family", "couple", "love", "relationship", "parent", "child", "baby", "together", "happy", "home"],
        "category": "People",
        "description": "Family moments and relationship dynamics"
    },
    "Travel & Adventure": {
        "keywords": ["travel", "vacation", "adventure", "explore", "destination", "journey", "trip", "tourism", "backpack"],
        "category": "Travel",
        "description": "Travel destinations and adventure experiences"
    },
    "Abstract & Backgrounds": {
        "keywords": ["abstract", "background", "texture", "pattern", "geometric", "gradient", "minimal", "artistic"],
        "category": "Graphic Resources",
        "description": "Abstract art and background textures"
    },
    "Seasonal & Holidays": {
        "keywords": ["christmas", "holiday", "winter", "summer", "spring", "autumn", "fall", "seasonal", "festive", "celebration"],
        "category": "Culture & Religion",
        "description": "Seasonal themes and holiday celebrations"
    },
    "Sustainable & Eco": {
        "keywords": ["sustainable", "eco", "green", "environment", "recycle", "organic", "natural", "renewable", "earth"],
        "category": "Environment",
        "description": "Sustainability and environmental themes"
    },
    "Urban & City Life": {
        "keywords": ["urban", "city", "street", "downtown", "metropolitan", "skyline", "building", "architecture"],
        "category": "Buildings & Architecture",
        "description": "Urban environments and city scenes"
    },
    "Minimalist & Modern": {
        "keywords": ["minimalist", "minimal", "modern", "clean", "simple", "white", "scandinavian", "contemporary"],
        "category": "Lifestyle",
        "description": "Minimalist aesthetics and modern design"
    },
}


def infer_category_from_keywords(keywords: List[str]) -> Dict[str, Any]:
    """
    Infer Adobe Stock category from asset keywords.
    
    Args:
        keywords: List of keywords from the asset
        
    Returns:
        Dict with category name, id, confidence score, and matched keywords
    """
    if not keywords:
        return {
            "name": "Graphic Resources",
            "id": 7,
            "confidence": 0,
            "matched_keywords": []
        }
    
    # Normalize keywords
    keywords_lower = [kw.lower().strip() for kw in keywords if kw]
    
    # Score each category
    category_scores = {}
    category_matches = {}
    
    for cat_name, cat_data in ADOBE_STOCK_CATEGORIES.items():
        score = 0
        matches = []
        
        for kw in keywords_lower:
            for cat_kw in cat_data["keywords"]:
                if cat_kw in kw or kw in cat_kw:
                    score += 1
                    if kw not in matches:
                        matches.append(kw)
                    break
        
        if score > 0:
            category_scores[cat_name] = score
            category_matches[cat_name] = matches
    
    if not category_scores:
        return {
            "name": "Graphic Resources",
            "id": 7,
            "confidence": 0,
            "matched_keywords": []
        }
    
    # Get best category
    best_category = max(category_scores.items(), key=lambda x: x[1])
    cat_name = best_category[0]
    
    return {
        "name": cat_name,
        "id": ADOBE_STOCK_CATEGORIES[cat_name]["id"],
        "confidence": min(best_category[1], 10),  # Cap at 10
        "matched_keywords": category_matches.get(cat_name, [])[:5]
    }


def detect_niches_from_keywords(keyword_freq: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Detect niches by grouping related keywords into meaningful categories.
    
    Args:
        keyword_freq: Dictionary of keyword -> frequency count
        
    Returns:
        List of detected niches with scores and metadata
    """
    if not keyword_freq:
        return []
    
    niche_scores = {}
    
    for niche_name, niche_data in NICHE_PATTERNS.items():
        score = 0
        matching_keywords = []
        
        for kw, count in keyword_freq.items():
            kw_lower = kw.lower()
            for pattern in niche_data["keywords"]:
                if pattern in kw_lower or kw_lower in pattern:
                    score += count
                    if kw not in matching_keywords:
                        matching_keywords.append(kw)
                    break
        
        if score > 0:
            niche_scores[niche_name] = {
                "name": niche_name,
                "score": score,
                "keywords": matching_keywords[:10],
                "keyword_count": len(matching_keywords),
                "category": niche_data["category"],
                "description": niche_data["description"],
            }
    
    # Sort by score descending
    sorted_niches = sorted(
        niche_scores.values(),
        key=lambda x: x["score"],
        reverse=True
    )
    
    return sorted_niches


def get_category_by_id(category_id: int) -> Optional[Dict[str, Any]]:
    """Get category details by Adobe Stock category ID."""
    for cat_name, cat_data in ADOBE_STOCK_CATEGORIES.items():
        if cat_data["id"] == category_id:
            return {
                "name": cat_name,
                "id": category_id,
                "keywords": cat_data["keywords"],
                "subcategories": cat_data["subcategories"]
            }
    return None


def get_all_categories() -> List[Dict[str, Any]]:
    """Get all Adobe Stock categories."""
    return [
        {
            "name": name,
            "id": data["id"],
            "subcategories": data["subcategories"]
        }
        for name, data in ADOBE_STOCK_CATEGORIES.items()
    ]


def calculate_category_distribution(assets: List[Dict]) -> Dict[str, Any]:
    """
    Calculate category distribution from a list of assets.
    
    Args:
        assets: List of asset dictionaries with keywords
        
    Returns:
        Dict with category counts, percentages, and top categories
    """
    category_counts = {}
    category_assets = {}
    
    for asset in assets:
        keywords = asset.get("keywords", [])
        
        # Try to get explicit category first
        explicit_cat = asset.get("category")
        if explicit_cat:
            cat_name = explicit_cat
        else:
            # Infer from keywords
            inferred = infer_category_from_keywords(keywords)
            cat_name = inferred["name"]
        
        category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
        
        if cat_name not in category_assets:
            category_assets[cat_name] = []
        category_assets[cat_name].append(asset.get("asset_id"))
    
    total = len(assets) or 1
    
    # Build distribution
    distribution = []
    for cat_name, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        cat_data = ADOBE_STOCK_CATEGORIES.get(cat_name, {})
        distribution.append({
            "name": cat_name,
            "id": cat_data.get("id", 0),
            "count": count,
            "percentage": round(count / total * 100, 1),
            "asset_ids": category_assets.get(cat_name, [])[:10],
        })
    
    return {
        "total_assets": len(assets),
        "categories": distribution,
        "top_category": distribution[0] if distribution else None,
        "category_count": len(distribution),
    }
