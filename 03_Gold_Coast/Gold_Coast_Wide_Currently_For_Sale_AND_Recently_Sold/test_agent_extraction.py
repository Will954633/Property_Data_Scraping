#!/usr/bin/env python3
"""
Test Agent and Agency Extraction
Last Updated: 31/01/2026, 9:44 am (Brisbane Time)

Tests the updated extract_agent_info() function to verify it properly
extracts agency name and agent names from Domain.com.au listing pages.

Example: 7 Turnberry Court, Robina QLD 4226
Expected: Agency = Ray White, Agents = Ricky Agent, Shaquille Gafa
"""

import sys
import json
from datetime import datetime

# Add path to html_parser
sys.path.append('../../07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search')

try:
    from headless_forsale_mongodb_scraper import HeadlessForSaleMongoDBScraper
except ImportError as e:
    print(f"ERROR: Could not import scraper: {e}")
    exit(1)


def test_single_property(url: str, expected_agency: str = None, expected_agents: list = None):
    """Test agent extraction for a single property"""
    print("\n" + "=" * 80)
    print("TESTING AGENT & AGENCY EXTRACTION")
    print("=" * 80)
    print(f"\nURL: {url}")
    if expected_agency:
        print(f"Expected Agency: {expected_agency}")
    if expected_agents:
        print(f"Expected Agents: {', '.join(expected_agents)}")
    print("\n" + "-" * 80)
    
    # Initialize scraper (won't save to MongoDB, just scrape)
    scraper = None
    try:
        # Use 'test' as suburb to avoid polluting real data
        scraper = HeadlessForSaleMongoDBScraper('test')
        
        # Scrape the property
        property_data = scraper.scrape_property(url)
        
        if not property_data:
            print("\n✗ FAILED: Could not scrape property data")
            return False
        
        # Extract agent information
        agency = property_data.get('agency')
        agent_name = property_data.get('agent_name')
        agent_names = property_data.get('agent_names', [])
        
        print("\n" + "=" * 80)
        print("EXTRACTION RESULTS")
        print("=" * 80)
        print(f"\n📍 Address: {property_data.get('address', 'N/A')}")
        print(f"🏢 Agency: {agency if agency else '❌ NOT FOUND'}")
        print(f"👤 Agent Name (string): {agent_name if agent_name else '❌ NOT FOUND'}")
        print(f"👥 Agent Names (array): {agent_names if agent_names else '❌ NOT FOUND'}")
        
        # Additional property details for context
        print(f"\n🏠 Property Details:")
        print(f"   - Bedrooms: {property_data.get('bedrooms', 'N/A')}")
        print(f"   - Bathrooms: {property_data.get('bathrooms', 'N/A')}")
        print(f"   - Price: {property_data.get('price', 'N/A')}")
        print(f"   - Property Type: {property_data.get('property_type', 'N/A')}")
        
        # Validation
        print("\n" + "=" * 80)
        print("VALIDATION")
        print("=" * 80)
        
        success = True
        
        if expected_agency:
            if agency and expected_agency.lower() in agency.lower():
                print(f"✓ Agency matches expected: {agency}")
            else:
                print(f"✗ Agency mismatch - Expected: {expected_agency}, Got: {agency}")
                success = False
        else:
            if agency:
                print(f"✓ Agency extracted: {agency}")
            else:
                print(f"⚠ No agency found (no expected value to compare)")
        
        if expected_agents:
            if agent_names:
                found_agents = []
                missing_agents = []
                for expected in expected_agents:
                    found = any(expected.lower() in agent.lower() for agent in agent_names)
                    if found:
                        found_agents.append(expected)
                    else:
                        missing_agents.append(expected)
                
                if found_agents:
                    print(f"✓ Found agents: {', '.join(found_agents)}")
                if missing_agents:
                    print(f"✗ Missing agents: {', '.join(missing_agents)}")
                    success = False
            else:
                print(f"✗ No agents found - Expected: {', '.join(expected_agents)}")
                success = False
        else:
            if agent_names:
                print(f"✓ Agents extracted: {', '.join(agent_names)}")
            else:
                print(f"⚠ No agents found (no expected value to compare)")
        
        # Save test results to JSON
        test_result = {
            'url': url,
            'test_date': datetime.now().isoformat(),
            'extracted_data': {
                'agency': agency,
                'agent_name': agent_name,
                'agent_names': agent_names,
                'address': property_data.get('address'),
                'bedrooms': property_data.get('bedrooms'),
                'bathrooms': property_data.get('bathrooms'),
                'price': property_data.get('price')
            },
            'expected': {
                'agency': expected_agency,
                'agents': expected_agents
            },
            'validation': {
                'success': success,
                'agency_found': bool(agency),
                'agents_found': bool(agent_names)
            }
        }
        
        output_file = 'test_agent_extraction_result.json'
        with open(output_file, 'w') as f:
            json.dump(test_result, f, indent=2)
        
        print(f"\n💾 Test results saved to: {output_file}")
        print("\n" + "=" * 80)
        
        if success:
            print("✅ TEST PASSED")
        else:
            print("❌ TEST FAILED")
        
        print("=" * 80 + "\n")
        
        return success
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if scraper:
            scraper.close()


def main():
    """Main test execution"""
    # Test with the example property: 7 Turnberry Court, Robina
    # Note: You'll need to provide the actual Domain.com.au URL for this property
    
    print("\n" + "=" * 80)
    print("AGENT & AGENCY EXTRACTION TEST SUITE")
    print("=" * 80)
    print("\nThis test verifies that the updated extract_agent_info() function")
    print("properly extracts agency names and agent names from Domain listings.")
    print("\n" + "=" * 80)
    
    # Example URL - replace with actual URL for 7 Turnberry Court, Robina
    test_url = input("\nEnter the Domain.com.au URL for 7 Turnberry Court, Robina: ").strip()
    
    if not test_url:
        print("\n⚠ No URL provided. Using test URL from test_robina_single.json if available...")
        try:
            with open('03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/test_robina_single.json', 'r') as f:
                data = json.load(f)
                if 'urls' in data and len(data['urls']) > 0:
                    test_url = data['urls'][0]
                    print(f"✓ Using URL: {test_url}")
                else:
                    print("✗ No URLs found in test file")
                    return 1
        except Exception as e:
            print(f"✗ Could not load test URL: {e}")
            return 1
    
    # Expected values (based on your example)
    expected_agency = "Ray White"
    expected_agents = ["Ricky Agent", "Shaquille Gafa"]
    
    # Run the test
    success = test_single_property(
        url=test_url,
        expected_agency=expected_agency,
        expected_agents=expected_agents
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
