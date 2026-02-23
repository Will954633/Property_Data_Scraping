#!/usr/bin/env python3
# Last Edit: 31/01/2026, Friday, 7:58 pm (Brisbane Time)
"""
Test Ollama with a single property to debug issues.
"""
import requests
import json
from mongodb_client_multi import MongoDBClientMulti
from worker_multi import PropertyWorkerMulti
from logger import logger

def main():
    print("=" * 80)
    print("OLLAMA SINGLE PROPERTY TEST")
    print("=" * 80)
    
    # Connect to MongoDB
    mongo_client = MongoDBClientMulti()
    
    # Get one unprocessed document
    all_docs = mongo_client.get_all_unprocessed_documents()
    
    if not all_docs:
        print("\nNo unprocessed documents found!")
        return
    
    suburb, document = all_docs[0]
    
    print(f"\nTesting with property from: {suburb}")
    print(f"Document ID: {document.get('_id')}")
    
    # Initialize worker
    worker = PropertyWorkerMulti(worker_id="test_worker")
    
    # Process single document
    print("\n" + "=" * 80)
    print("PROCESSING")
    print("=" * 80)
    
    success = worker.process_document(suburb, document)
    
    print("\n" + "=" * 80)
    print("RESULT")
    print("=" * 80)
    
    if success:
        print("\n✅ SUCCESS! Property processed successfully.")
    else:
        print("\n❌ FAILED! Check logs for details.")
    
    # Clean up
    worker.close()
    mongo_client.close()

if __name__ == "__main__":
    main()
