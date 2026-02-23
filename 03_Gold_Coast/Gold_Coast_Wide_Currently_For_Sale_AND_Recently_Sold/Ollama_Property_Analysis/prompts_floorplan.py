# Last Edit: 01/02/2026, Thursday, 11:32 am (Brisbane Time)
# Floor plan analysis prompts for Ollama Vision API
# OPTIMIZED: Split into two focused calls to avoid timeouts
# Call 1: Essential measurements (fast)
# Call 2: Detailed features (optional, slower)

"""
Prompts for floor plan analysis using Ollama Vision API.
Optimized to avoid timeouts by splitting complex analysis into focused calls.
"""

def get_floor_plan_basic_prompt():
    """
    Get the prompt for extracting ESSENTIAL floor plan measurements only.
    This is a fast, focused prompt that should complete quickly.
    
    Returns:
        str: The basic analysis prompt
    """
    return """You are a professional floor plan analyst. Analyze this floor plan and extract ONLY the essential measurements and room counts.

Provide your analysis in this EXACT JSON format:

{
    "internal_floor_area": {
        "value": <number or null>,
        "unit": "sqm",
        "notes": "Internal living area only"
    },
    "total_floor_area": {
        "value": <number or null>,
        "unit": "sqm",
        "notes": "Total including garage"
    },
    "total_land_area": {
        "value": <number or null>,
        "unit": "sqm"
    },
    "bedrooms": {
        "total_count": <number>,
        "list": ["Master Bedroom", "Bedroom 2", "Bedroom 3", etc]
    },
    "bathrooms": {
        "total_count": <number>,
        "full_bathrooms": <number>,
        "powder_rooms": <number>,
        "ensuites": <number>
    },
    "parking": {
        "garage_spaces": <number>,
        "carport_spaces": <number>,
        "garage_type": "single" | "double" | "triple" | null
    },
    "levels": {
        "total_levels": <number>,
        "level_names": ["Ground Floor", "First Floor", etc]
    },
    "rooms": [
        {
            "room_name": "Master Bedroom",
            "room_type": "bedroom",
            "level": "Ground Floor",
            "dimensions": {
                "length": <number or null>,
                "width": <number or null>,
                "area": <number or null>,
                "unit": "m"
            }
        }
    ]
}

INSTRUCTIONS:
1. Extract ALL room dimensions shown on the floor plan
2. Count ALL bedrooms (no limit - could be 1, 2, 3, 4, 5, 6+)
3. Distinguish internal floor area from total floor area
4. List every room with its dimensions if shown
5. Use null for missing data
6. Be accurate and thorough with measurements

Return ONLY valid JSON, no additional text."""


def get_floor_plan_detailed_prompt():
    """
    Get the prompt for extracting DETAILED features and insights.
    This is a slower, more comprehensive analysis (optional second call).
    
    Returns:
        str: The detailed analysis prompt
    """
    return """You are a professional floor plan analyst. Analyze this floor plan and provide detailed features and buyer insights.

Provide your analysis in this EXACT JSON format:

{
    "room_features": [
        {
            "room_name": "Master Bedroom",
            "features": ["ensuite", "walk-in robe", "balcony access", etc]
        }
    ],
    "outdoor_spaces": [
        {
            "type": "balcony" | "patio" | "deck" | "alfresco" | "pool",
            "level": "Ground Floor",
            "dimensions": {
                "area": <number or null>,
                "unit": "sqm"
            },
            "features": ["covered", "access from living", etc]
        }
    ],
    "layout_features": {
        "open_plan": true | false,
        "split_level": true | false,
        "flow_description": "brief description of layout flow"
    },
    "additional_features": [
        "butler's pantry", "study nook", "wine cellar", etc
    ],
    "buyer_insights": {
        "ideal_for": ["families", "couples", "retirees", etc],
        "key_benefits": ["spacious living", "good separation", etc],
        "lifestyle_suitability": "brief description"
    },
    "data_quality": {
        "floor_plan_clarity": "excellent" | "good" | "fair" | "poor",
        "measurements_available": true | false,
        "confidence_overall": "high" | "medium" | "low"
    }
}

INSTRUCTIONS:
1. Focus on features and benefits, not measurements
2. Identify special features (butler's pantry, study nooks, etc)
3. Describe layout flow and open-plan areas
4. Provide buyer insights and lifestyle suitability
5. Use null for missing data

Return ONLY valid JSON, no additional text."""


def get_floor_plan_analysis_prompt():
    """
    Get the LEGACY comprehensive prompt (kept for backward compatibility).
    WARNING: This prompt is too complex and causes timeouts.
    Use get_floor_plan_basic_prompt() instead for production.
    
    Returns:
        str: The legacy comprehensive analysis prompt
    """
    return """You are a professional floor plan analyst. Analyze the provided floor plan image and extract ALL useful information that a home buyer would want to know.

Please provide a comprehensive analysis in JSON format with the following structure:

{
    "internal_floor_area": {
        "value": <number or null>,
        "unit": "sqm" or "m2" or null,
        "confidence": "high" | "medium" | "low",
        "notes": "Internal living area only - excludes garage, porches, external storage"
    },
    "total_floor_area": {
        "value": <number or null>,
        "unit": "sqm" or "m2" or null,
        "confidence": "high" | "medium" | "low",
        "notes": "Total building footprint including garage, porches, covered areas"
    },
    "total_land_area": {
        "value": <number or null>,
        "unit": "sqm" or "m2" or null,
        "confidence": "high" | "medium" | "low",
        "notes": "any relevant notes"
    },
    "levels": {
        "total_levels": <number>,
        "level_details": [
            {
                "level_name": "Ground Floor" | "First Floor" | "Second Floor" | etc,
                "floor_area": {
                    "value": <number or null>,
                    "unit": "sqm" or "m2" or null
                }
            }
        ]
    },
    "rooms": [
        {
            "room_type": "living_room" | "kitchen" | "dining_room" | "bedroom" | "bathroom" | "laundry" | "garage" | "study" | "family_room" | "rumpus" | "media_room" | "powder_room" | "ensuite" | "walk_in_robe" | "balcony" | "patio" | "deck" | "alfresco" | "entry" | "hallway" | "storage" | "other",
            "room_name": "specific name from floor plan (e.g., 'Master Bedroom', 'Bedroom 1', 'Main Bathroom')",
            "level": "Ground Floor" | "First Floor" | etc,
            "dimensions": {
                "length": <number or null>,
                "width": <number or null>,
                "unit": "m" | "meters" | null,
                "area": <number or null>,
                "area_unit": "sqm" | "m2" | null
            },
            "features": [
                "list of features like 'ensuite', 'walk-in robe', 'built-in wardrobes', 'air conditioning', etc"
            ],
            "notes": "any additional relevant information"
        }
    ],
    "bedrooms": {
        "total_count": <number>,
        "details": "summary of all bedrooms"
    },
    "bathrooms": {
        "total_count": <number>,
        "full_bathrooms": <number>,
        "powder_rooms": <number>,
        "ensuites": <number>,
        "details": "summary of all bathrooms"
    },
    "parking": {
        "garage_spaces": <number>,
        "carport_spaces": <number>,
        "total_spaces": <number>,
        "garage_type": "single" | "double" | "triple" | "tandem" | null,
        "notes": "any relevant parking details"
    },
    "outdoor_spaces": [
        {
            "type": "balcony" | "patio" | "deck" | "alfresco" | "courtyard" | "garden" | "terrace" | "pool",
            "level": "Ground Floor" | "First Floor" | etc,
            "dimensions": {
                "length": <number or null>,
                "width": <number or null>,
                "area": <number or null>,
                "unit": "sqm" | "m2" | null
            },
            "features": ["covered", "uncovered", "access from living room", etc]
        }
    ],
    "layout_features": {
        "open_plan": true | false,
        "split_level": true | false,
        "flow_description": "description of how rooms connect and flow",
        "highlights": ["key selling points of the layout"]
    },
    "additional_features": [
        "any other notable features like 'study nook', 'butler's pantry', 'wine cellar', 'home office', 'gym area', etc"
    ],
    "buyer_insights": {
        "ideal_for": ["families", "couples", "retirees", "investors", etc],
        "key_benefits": ["list of main selling points"],
        "considerations": ["any potential drawbacks or things to note"],
        "lifestyle_suitability": "description of lifestyle this property suits"
    },
    "data_quality": {
        "floor_plan_clarity": "excellent" | "good" | "fair" | "poor",
        "measurements_available": true | false,
        "missing_information": ["list of information that couldn't be determined"],
        "confidence_overall": "high" | "medium" | "low"
    }
}

IMPORTANT INSTRUCTIONS:
1. FLOOR AREA DISTINCTION:
   - Internal floor area = Living spaces only (bedrooms, living, kitchen, bathrooms, laundry, hallways)
   - Total floor area = Internal area PLUS garage, porches, covered patios, external storage
   - Look for labels like "Internal Floor Area" vs "Total Floor Area" or "Building Area"
   - If only one measurement is provided, note which type it represents

2. Extract ALL measurements shown on the floor plan - don't miss any room dimensions

3. Count ALL bedrooms - there is no upper limit, extract however many exist (could be 1, 2, 3, 4, 5, 6, or more)

4. For each room, capture:
   - Exact dimensions if shown (length x width)
   - Calculated or stated area
   - All features mentioned (ensuite, robe, island, pantry, etc.)

5. Be thorough - extract every piece of useful information visible
6. If information is not available or unclear, use null and note it in the appropriate field
7. Provide confidence levels honestly based on available information
8. In buyer_insights, think about what makes this property unique and valuable
9. Include all room types, not just bedrooms - living areas, outdoor spaces, storage, etc.
10. For outdoor spaces, include pools, patios, decks, alfresco areas, etc.
11. Note any special features like butler's pantry, study nooks, storage areas, etc.

Return ONLY valid JSON, no additional text or explanation outside the JSON structure."""
