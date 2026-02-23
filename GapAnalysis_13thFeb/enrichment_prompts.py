"""
Enrichment prompts module for GPT-based property data enrichment.
Last Edit: 13/02/2026, 3:40 PM (Thursday) — Brisbane Time

Description: Contains all validated GPT prompts for enriching property data
with building condition, age, parking, outdoor entertainment, and renovation status.

Edit History:
- 13/02/2026 3:40 PM: Initial creation with all 7 validated prompts
"""

def get_building_condition_prompt() -> str:
    """
    Prompt for analyzing building condition from property photos.
    
    Returns validated JSON with:
    - overall_condition: excellent|good|fair|poor
    - confidence: high|medium|low
    - observations: list of specific observations
    - maintenance_level: well-maintained|average|needs-work
    - evidence: what was observed in photos
    """
    return """Analyze these property photos and assess the building condition.

Consider:
- Exterior: Paint condition, roof state, landscaping, general maintenance
- Interior: Finishes, fixtures, flooring, walls, overall presentation
- Age indicators: Wear and tear, outdated features, modernization

Provide a JSON response with:
{
    "overall_condition": "excellent|good|fair|poor",
    "confidence": "high|medium|low",
    "observations": ["observation1", "observation2", "observation3"],
    "maintenance_level": "well-maintained|average|needs-work",
    "evidence": "What you observed in the photos"
}"""


def get_building_age_prompt() -> str:
    """
    Prompt for estimating building age from property photos.
    
    Returns validated JSON with:
    - year_built: estimated year (integer)
    - year_range: range estimate (string)
    - confidence: high|medium|low
    - evidence: list of age indicators
    - era: architectural era classification
    """
    return """Analyze these property photos and estimate the building age.

Consider:
- Architectural style and design elements
- Construction materials and techniques
- Fixtures, fittings, and finishes
- Modernization and renovation indicators
- Landscaping maturity

Provide a JSON response with:
{
    "year_built": 2010,
    "year_range": "2008-2012",
    "confidence": "high|medium|low",
    "evidence": ["indicator1", "indicator2", "indicator3"],
    "era": "modern|contemporary|established|heritage"
}"""


def get_parking_prompt() -> str:
    """
    Prompt for identifying parking type and capacity.
    
    Returns validated JSON with:
    - type: garage|carport|open|mixed
    - garage_spaces: number of garage spaces
    - carport_spaces: number of carport spaces
    - garage_type: single|double|triple|tandem
    - confidence: high|medium|low
    """
    return """Analyze these property photos and identify the parking facilities.

Look for:
- Garage doors and enclosed parking
- Carport structures (covered but not enclosed)
- Open parking spaces
- Number of vehicles that can be accommodated

Provide a JSON response with:
{
    "type": "garage|carport|open|mixed",
    "garage_spaces": 2,
    "carport_spaces": 0,
    "total_spaces": 2,
    "garage_type": "single|double|triple|tandem",
    "notes": "Any additional parking details",
    "confidence": "high|medium|low"
}"""


def get_outdoor_entertainment_prompt() -> str:
    """
    Prompt for scoring outdoor entertainment areas.
    
    Returns validated JSON with:
    - score: 0-10 rating
    - size: small|medium|large
    - features: list of entertainment features
    - quality: basic|standard|premium
    - confidence: high|medium|low
    """
    return """Analyze these property photos and rate the outdoor entertainment areas.

Consider:
- Covered outdoor areas (patios, alfresco, verandas)
- Pool and spa facilities
- Outdoor kitchen/BBQ areas
- Landscaping and garden features
- Size and quality of spaces

Rate from 0-10 where:
- 0-2: Minimal or no outdoor entertainment
- 3-4: Basic outdoor space
- 5-6: Good outdoor area with some features
- 7-8: Excellent outdoor entertainment with multiple features
- 9-10: Outstanding resort-style outdoor living

Provide a JSON response with:
{
    "score": 8,
    "size": "small|medium|large",
    "features": ["covered patio", "pool", "outdoor kitchen"],
    "quality": "basic|standard|premium",
    "confidence": "high|medium|low",
    "notes": "Description of outdoor areas"
}"""


def get_renovation_status_prompt() -> str:
    """
    Prompt for assessing renovation status and quality.
    
    Returns validated JSON with:
    - status: original|partially-renovated|fully-renovated|new
    - renovated_areas: list of renovated spaces
    - quality: budget|standard|high-end
    - age: recent|moderate|dated
    - confidence: high|medium|low
    """
    return """Analyze these property photos and assess the renovation status.

Consider:
- Kitchen: Appliances, cabinetry, benchtops, finishes
- Bathrooms: Fixtures, tiles, vanities, quality
- Flooring: Type, condition, consistency
- Paint and finishes: Freshness, quality
- Overall presentation: Modern vs dated

Provide a JSON response with:
{
    "status": "original|partially-renovated|fully-renovated|new",
    "renovated_areas": ["kitchen", "bathrooms", "flooring"],
    "quality": "budget|standard|high-end",
    "age": "recent|moderate|dated",
    "confidence": "high|medium|low",
    "evidence": ["observation1", "observation2"]
}"""


def get_corner_block_prompt() -> str:
    """
    Prompt for determining if property is on a corner block (GPT fallback).
    
    Note: This is a fallback. Primary detection uses Google Maps API.
    
    Returns validated JSON with:
    - is_corner: true|false
    - confidence: high|medium|low
    - evidence: list of indicators
    """
    return """Determine if this property is on a corner block.

Analyze:
- Address: Does it mention two street names or "corner of X and Y"?
- Description: Keywords like "corner", "corner block", "dual street frontage"
- Photos: Can you see two street frontages?

Provide a JSON response with:
{
    "is_corner": true,
    "confidence": "high|medium|low",
    "evidence": ["Two street names in address", "Dual frontage visible in photos"],
    "data_source": "GPT Vision"
}"""


def get_north_facing_prompt() -> str:
    """
    Prompt for determining if property has north-facing living areas.
    
    Returns validated JSON with:
    - north_facing: true|false|unknown
    - confidence: high|medium|low
    - evidence: list of indicators
    - living_areas: which areas face north
    """
    return """Analyze these property photos and description to determine if the main living areas face north.

Consider:
- Property description mentions of "north-facing"
- Sun exposure visible in photos
- Living room and outdoor area orientation
- Natural light patterns

Note: In Australia, north-facing is highly desirable for natural light and warmth.

Provide a JSON response with:
{
    "north_facing": true,
    "confidence": "high|medium|low",
    "evidence": ["Description mentions north-facing", "Bright living areas in photos"],
    "living_areas": ["living room", "alfresco", "pool area"]
}"""


# ============================================================================
# PROMPT VALIDATION
# ============================================================================

def validate_prompts():
    """Validate that all prompts are properly formatted."""
    prompts = {
        "building_condition": get_building_condition_prompt(),
        "building_age": get_building_age_prompt(),
        "parking": get_parking_prompt(),
        "outdoor_entertainment": get_outdoor_entertainment_prompt(),
        "renovation_status": get_renovation_status_prompt(),
        "corner_block": get_corner_block_prompt(),
        "north_facing": get_north_facing_prompt()
    }
    
    for name, prompt in prompts.items():
        if not prompt or len(prompt) < 50:
            raise ValueError(f"Invalid prompt for {name}")
    
    return True


# Validate on import
if __name__ != "__main__":
    validate_prompts()
