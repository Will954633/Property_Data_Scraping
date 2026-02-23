#!/usr/bin/env python3
"""
Test GPT enrichment on actual scraped sold property data.
Last Edit: 13/02/2026, 2:42 PM (Thursday) — Brisbane Time

Description: Test script to validate GPT-based enrichment approaches using
real scraped data from the 12-month sold properties.

This script will:
1. Load a sample property from the scraped JSON
2. Test building condition analysis
3. Test building age estimation
4. Test corner block detection
5. Test busy road detection
6. Test garage/carport identification
7. Test outdoor entertainment scoring
8. Test renovation status analysis

Usage:
    cd /Users/projects/Documents/Property_Data_Scraping/GapAnalysis_13thFeb && \
    python3 test_enrichment_on_scraped_data.py
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv(Path(__file__).parent.parent / "01.1_Floor_Plan_Data" / ".env")

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-5-nano-2025-08-07"
MAX_TOKENS = 16000

# Sample property data file
SAMPLE_DATA_FILE = Path(__file__).parent.parent / "02_Domain_Scaping" / "Sold_In_Last_12_Months_8_Suburbs" / "property_data" / "sold_scrape_robina_20260213_135837.json"


class PropertyEnrichmentTester:
    """Test GPT enrichment on scraped property data."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = GPT_MODEL
        print(f"✅ Initialized GPT client with model: {self.model}\n")
    
    def load_sample_property(self) -> Dict[str, Any]:
        """Load first property from scraped data."""
        print(f"📂 Loading sample property from: {SAMPLE_DATA_FILE}")
        
        with open(SAMPLE_DATA_FILE, 'r') as f:
            data = json.load(f)
        
        # Get first property
        property_data = data['results'][0]['property_data']
        
        print(f"✅ Loaded property: {property_data['address']}")
        print(f"   - Bedrooms: {property_data.get('bedrooms')}")
        print(f"   - Bathrooms: {property_data.get('bathrooms')}")
        print(f"   - Sale Price: {property_data.get('sale_price')}")
        print(f"   - Photos: {len(property_data.get('property_images', []))} images")
        print(f"   - Floor Plans: {len(property_data.get('floor_plans', []))} plans\n")
        
        return property_data
    
    def analyze_with_gpt(self, prompt: str, image_urls: List[str] = None, 
                        description: str = None) -> Dict[str, Any]:
        """
        Generic GPT analysis function.
        
        Args:
            prompt: The analysis prompt
            image_urls: Optional list of image URLs to analyze
            description: Optional text description to include
            
        Returns:
            Parsed JSON response
        """
        message_content = []
        
        # Add text prompt
        full_prompt = prompt
        if description:
            full_prompt += f"\n\nProperty Description:\n{description}"
        
        message_content.append({"type": "text", "text": full_prompt})
        
        # Add images if provided (limit to first 5 for testing)
        if image_urls:
            for url in image_urls[:5]:
                message_content.append({
                    "type": "image_url",
                    "image_url": {"url": url, "detail": "high"}
                })
        
        messages = [
            {
                "role": "system",
                "content": "You are a professional property analyst with expertise in real estate valuation and property assessment."
            },
            {"role": "user", "content": message_content}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=MAX_TOKENS,
                response_format={"type": "json_object"},
                timeout=120
            )
            
            content = response.choices[0].message.content.strip()
            return json.loads(content)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"error": str(e)}
    
    def test_building_condition(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test building condition analysis."""
        print("=" * 80)
        print("TEST 1: Building Condition Analysis")
        print("=" * 80)
        
        prompt = """Analyze these property photos and assess the building condition.

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
        
        images = property_data.get('property_images', [])
        result = self.analyze_with_gpt(prompt, images)
        
        print(f"\n📊 Result:")
        print(json.dumps(result, indent=2))
        print()
        
        return result
    
    def test_building_age(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test building age estimation."""
        print("=" * 80)
        print("TEST 2: Building Age Estimation")
        print("=" * 80)
        
        prompt = """Estimate the building age of this property.

Analyze:
- Description mentions of "built in YYYY" or "circa YYYY"
- Architectural style visible in photos
- Materials and construction methods
- Fixtures and fittings style
- Kitchen/bathroom modernization level

Provide a JSON response with:
{
    "year_built": 2018,
    "year_range": "2017-2019",
    "confidence": "high|medium|low",
    "evidence": ["evidence1", "evidence2"],
    "era": "modern|contemporary|established|older"
}"""
        
        images = property_data.get('property_images', [])
        description = property_data.get('agents_description', '')
        result = self.analyze_with_gpt(prompt, images, description)
        
        print(f"\n📊 Result:")
        print(json.dumps(result, indent=2))
        print()
        
        return result
    
    def test_corner_block(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test corner block detection."""
        print("=" * 80)
        print("TEST 3: Corner Block Detection")
        print("=" * 80)
        
        address = property_data.get('address', '')
        description = property_data.get('agents_description', '')
        
        prompt = f"""Determine if this property is on a corner block.

Address: {address}

Analyze:
- Address: Does it mention two street names or "corner of X and Y"?
- Description: Keywords like "corner", "corner block", "dual street frontage"
- Photos: Visual evidence of property facing two streets
- Photos: Driveway access from side street
- Photos: Fencing configuration suggesting corner position

Provide a JSON response with:
{{
    "is_corner": true|false,
    "confidence": "high|medium|low",
    "evidence": ["evidence1", "evidence2"],
    "street_names": ["street1", "street2"] or null
}}"""
        
        images = property_data.get('property_images', [])
        result = self.analyze_with_gpt(prompt, images, description)
        
        print(f"\n📊 Result:")
        print(json.dumps(result, indent=2))
        print()
        
        return result
    
    def test_busy_road(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test busy road detection."""
        print("=" * 80)
        print("TEST 4: Busy Road Detection")
        print("=" * 80)
        
        address = property_data.get('address', '')
        description = property_data.get('agents_description', '')
        
        prompt = f"""Assess if this property is located on a busy road.

Address: {address}

Analyze:
- Address: Road name suggests major thoroughfare (Highway, Boulevard, Main Road, etc.)
- Description: Mentions of "quiet street", "cul-de-sac", "no through road" (negative indicators)
- Description: Mentions of "main road", "busy street" (positive indicators)
- Photos: Visual traffic indicators (road width, lane markings, traffic signs)
- Photos: Noise barriers, high fences (suggesting traffic mitigation)

Provide a JSON response with:
{{
    "is_busy": true|false,
    "confidence": "high|medium|low",
    "road_type": "residential|collector|arterial|highway|unknown",
    "evidence": ["evidence1", "evidence2"]
}}"""
        
        images = property_data.get('property_images', [])
        result = self.analyze_with_gpt(prompt, images, description)
        
        print(f"\n📊 Result:")
        print(json.dumps(result, indent=2))
        print()
        
        return result
    
    def test_garage_carport(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test garage vs carport identification."""
        print("=" * 80)
        print("TEST 5: Garage vs Carport Identification")
        print("=" * 80)
        
        features = property_data.get('features', [])
        description = property_data.get('agents_description', '')
        
        prompt = f"""Identify the parking type for this property.

Features list: {', '.join(features)}

Analyze:
- Features list: Look for "garage", "carport", "covered parking"
- Description: Mentions of parking type
- Photos: Visual identification of enclosed garage vs open carport
- Photos: Number of spaces visible

Provide a JSON response with:
{{
    "parking_type": "garage|carport|mixed|unknown",
    "garage_spaces": 2,
    "carport_spaces": 0,
    "garage_type": "single|double|triple|tandem",
    "confidence": "high|medium|low",
    "evidence": "What you observed"
}}"""
        
        images = property_data.get('property_images', [])
        result = self.analyze_with_gpt(prompt, images, description)
        
        print(f"\n📊 Result:")
        print(json.dumps(result, indent=2))
        print()
        
        return result
    
    def test_outdoor_entertainment(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test outdoor entertainment scoring."""
        print("=" * 80)
        print("TEST 6: Outdoor Entertainment Scoring")
        print("=" * 80)
        
        prompt = """Score the outdoor entertainment area quality.

Analyze:
- Size: Small/medium/large outdoor space
- Features: Deck, patio, alfresco, BBQ area, pool, spa
- Quality: Materials, finishes, design
- Functionality: Covered areas, lighting, seating capacity
- Landscaping: Gardens, privacy, aesthetics

Provide a JSON response with:
{
    "score": 8,
    "size": "small|medium|large",
    "features": ["feature1", "feature2"],
    "quality": "basic|good|premium|luxury",
    "confidence": "high|medium|low"
}"""
        
        images = property_data.get('property_images', [])
        result = self.analyze_with_gpt(prompt, images)
        
        print(f"\n📊 Result:")
        print(json.dumps(result, indent=2))
        print()
        
        return result
    
    def test_renovation_status(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test renovation status analysis."""
        print("=" * 80)
        print("TEST 7: Renovation Status Analysis")
        print("=" * 80)
        
        description = property_data.get('agents_description', '')
        
        prompt = """Assess the renovation status of this property.

Analyze:
- Description: Keywords "renovated", "updated", "modernized", "original condition"
- Photos: Kitchen - modern appliances, benchtops, cabinetry
- Photos: Bathrooms - fixtures, tiles, vanities
- Photos: Flooring - new/old, type
- Photos: Paint - fresh/dated
- Photos: Fixtures - modern/dated light fittings, door handles

Provide a JSON response with:
{
    "status": "fully-renovated|partially-renovated|original|mixed",
    "renovated_areas": ["kitchen", "bathrooms", "flooring"],
    "quality": "budget|mid-range|high-end",
    "age": "recent|moderate|older",
    "confidence": "high|medium|low"
}"""
        
        images = property_data.get('property_images', [])
        result = self.analyze_with_gpt(prompt, images, description)
        
        print(f"\n📊 Result:")
        print(json.dumps(result, indent=2))
        print()
        
        return result
    
    def run_all_tests(self):
        """Run all enrichment tests."""
        print("\n" + "=" * 80)
        print("GPT ENRICHMENT TESTING ON SCRAPED DATA")
        print("=" * 80 + "\n")
        
        # Load sample property
        property_data = self.load_sample_property()
        
        # Run all tests
        results = {
            "property_address": property_data.get('address'),
            "tests": {}
        }
        
        try:
            results["tests"]["building_condition"] = self.test_building_condition(property_data)
            results["tests"]["building_age"] = self.test_building_age(property_data)
            results["tests"]["corner_block"] = self.test_corner_block(property_data)
            results["tests"]["busy_road"] = self.test_busy_road(property_data)
            results["tests"]["garage_carport"] = self.test_garage_carport(property_data)
            results["tests"]["outdoor_entertainment"] = self.test_outdoor_entertainment(property_data)
            results["tests"]["renovation_status"] = self.test_renovation_status(property_data)
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            results["error"] = str(e)
        
        # Save results
        output_file = Path(__file__).parent / "test_enrichment_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 80)
        print("TESTING COMPLETE")
        print("=" * 80)
        print(f"\n✅ Results saved to: {output_file}")
        print(f"\n📊 Summary:")
        print(f"   - Property: {results['property_address']}")
        print(f"   - Tests run: {len(results['tests'])}")
        print(f"   - Errors: {'Yes' if 'error' in results else 'No'}")
        print()


def main():
    """Main entry point."""
    try:
        tester = PropertyEnrichmentTester()
        tester.run_all_tests()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
