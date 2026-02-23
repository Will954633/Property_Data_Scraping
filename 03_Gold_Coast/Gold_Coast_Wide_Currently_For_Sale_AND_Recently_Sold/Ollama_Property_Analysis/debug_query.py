# Last Edit: 01/02/2026, Saturday, 8:33 am (Brisbane Time)
# Debug script to check MongoDB query

from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['Gold_Coast_Currently_For_Sale']

# Check robina collection directly
collection = db['robina']
print('Testing robina collection:')
print(f'Total documents: {collection.count_documents({})}')
print(f'With ollama_image_analysis: {collection.count_documents({"ollama_image_analysis": {"$exists": True}})}')
print(f'With non-empty ollama_image_analysis: {collection.count_documents({"ollama_image_analysis": {"$exists": True, "$ne": []}})}')

# Get one sample
sample = collection.find_one({"ollama_image_analysis": {"$exists": True, "$ne": []}})
if sample:
    print(f'\nSample property found:')
    print(f'  ID: {sample.get("_id")}')
    print(f'  Has ollama_image_analysis: {"ollama_image_analysis" in sample}')
    print(f'  Number of images analyzed: {len(sample.get("ollama_image_analysis", []))}')
    print(f'  Has ollama_photo_tour_order: {"ollama_photo_tour_order" in sample}')
else:
    print('\nNo sample found!')

client.close()
