# Last Edit: 31/01/2026, Friday, 8:19 pm (Brisbane Time)
"""
Script to inspect what analysis data is actually being stored in MongoDB.
This will help diagnose why all properties are getting 8/10 scores.
"""
import json
from pymongo import MongoClient
from config import MONGODB_URI, DATABASE_NAME, TARGET_SUBURBS

def inspect_analysis_data():
    """Inspect the actual analysis data stored in MongoDB."""
    
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    print("\n" + "="*80)
    print("INSPECTING OLLAMA ANALYSIS DATA")
    print("="*80)
    
    # Get one processed document from each suburb
    for suburb in TARGET_SUBURBS:
        collection = db[suburb]
        
        # Find one processed document
        doc = collection.find_one({"ollama_analysis.processed": True})
        
        if not doc:
            print(f"\n{suburb.upper()}: No processed documents found")
            continue
        
        print(f"\n{suburb.upper()}: {doc.get('address', 'Unknown Address')}")
        print("-" * 80)
        
        # Check what fields exist
        print("\nFields in document:")
        print(f"  - ollama_analysis: {bool(doc.get('ollama_analysis'))}")
        print(f"  - ollama_image_analysis: {bool(doc.get('ollama_image_analysis'))}")
        print(f"  - ollama_property_data: {bool(doc.get('ollama_property_data'))}")
        
        # Show ollama_analysis metadata
        if "ollama_analysis" in doc:
            print("\nOllama Analysis Metadata:")
            print(json.dumps(doc["ollama_analysis"], indent=2, default=str))
        
        # Show image analysis (first 2 images)
        if "ollama_image_analysis" in doc:
            image_analyses = doc["ollama_image_analysis"]
            print(f"\nImage Analysis ({len(image_analyses)} images analyzed):")
            
            for i, img_analysis in enumerate(image_analyses[:3]):  # Show first 3
                print(f"\n  Image {i}:")
                print(f"    URL: {img_analysis.get('url', 'N/A')[:80]}...")
                print(f"    Type: {img_analysis.get('image_type', 'N/A')}")
                print(f"    Usefulness Score: {img_analysis.get('usefulness_score', 'N/A')}/10")
                print(f"    Quality Score: {img_analysis.get('quality_score', 'N/A')}/10")
                print(f"    Marketing Value: {img_analysis.get('marketing_value', 'N/A')}")
                print(f"    Description: {img_analysis.get('description', 'N/A')}")
                print(f"    Features: {img_analysis.get('features_visible', [])}")
        
        # Show property data structure
        if "ollama_property_data" in doc:
            print("\nProperty Data Structure:")
            prop_data = doc["ollama_property_data"]
            print(f"  - structural: {list(prop_data.get('structural', {}).keys())}")
            print(f"  - exterior: {list(prop_data.get('exterior', {}).keys())}")
            print(f"  - interior: {list(prop_data.get('interior', {}).keys())}")
            print(f"  - renovation: {list(prop_data.get('renovation', {}).keys())}")
            print(f"  - outdoor: {list(prop_data.get('outdoor', {}).keys())}")
            print(f"  - layout: {list(prop_data.get('layout', {}).keys())}")
            print(f"  - overall: {list(prop_data.get('overall', {}).keys())}")
            
            # Show unique features
            if "overall" in prop_data and "unique_features" in prop_data["overall"]:
                features = prop_data["overall"]["unique_features"]
                print(f"\n  Unique Features ({len(features)}): {features[:10]}")
        
        # Only show first suburb in detail
        break
    
    # Now check if scores are all the same
    print("\n" + "="*80)
    print("SCORE DISTRIBUTION ANALYSIS")
    print("="*80)
    
    for suburb in TARGET_SUBURBS:
        collection = db[suburb]
        
        # Get all processed documents
        docs = list(collection.find(
            {"ollama_analysis.processed": True},
            {"ollama_image_analysis": 1, "address": 1}
        ))
        
        if not docs:
            continue
        
        print(f"\n{suburb.upper()}: {len(docs)} processed properties")
        
        # Collect all scores
        all_usefulness_scores = []
        all_quality_scores = []
        
        for doc in docs:
            if "ollama_image_analysis" in doc:
                for img in doc["ollama_image_analysis"]:
                    usefulness = img.get("usefulness_score")
                    quality = img.get("quality_score")
                    if usefulness is not None:
                        all_usefulness_scores.append(usefulness)
                    if quality is not None:
                        all_quality_scores.append(quality)
        
        if all_usefulness_scores:
            print(f"  Usefulness scores: min={min(all_usefulness_scores)}, max={max(all_usefulness_scores)}, avg={sum(all_usefulness_scores)/len(all_usefulness_scores):.1f}")
            print(f"  Unique usefulness scores: {sorted(set(all_usefulness_scores))}")
        
        if all_quality_scores:
            print(f"  Quality scores: min={min(all_quality_scores)}, max={max(all_quality_scores)}, avg={sum(all_quality_scores)/len(all_quality_scores):.1f}")
            print(f"  Unique quality scores: {sorted(set(all_quality_scores))}")
    
    # Check if different images are being analyzed
    print("\n" + "="*80)
    print("IMAGE URL VERIFICATION")
    print("="*80)
    
    for suburb in TARGET_SUBURBS[:2]:  # Check first 2 suburbs
        collection = db[suburb]
        
        docs = list(collection.find(
            {"ollama_analysis.processed": True},
            {"ollama_image_analysis": 1, "address": 1}
        ).limit(3))
        
        for doc in docs:
            print(f"\n{doc.get('address', 'Unknown')}")
            if "ollama_image_analysis" in doc:
                for i, img in enumerate(doc["ollama_image_analysis"][:3]):
                    url = img.get('url', 'N/A')
                    # Show last 50 chars of URL to see if they're different
                    print(f"  Image {i}: ...{url[-50:]}")
    
    client.close()

if __name__ == "__main__":
    inspect_analysis_data()
