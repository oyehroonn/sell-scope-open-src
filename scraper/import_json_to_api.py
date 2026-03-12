#!/usr/bin/env python3
"""
Import a scraper JSON file into the SellScope API (full import).
Usage: python3 import_json_to_api.py output/adobe_stock_fruit_20260313_001527.json
"""

import sys
import json
import os
from dotenv import load_dotenv
from api_integration import APIClient

load_dotenv()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 import_json_to_api.py <path-to-scraper-output.json>")
        sys.exit(1)
    
    path = sys.argv[1]
    if not os.path.isfile(path):
        print(f"File not found: {path}")
        sys.exit(1)
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    query = data.get("query", "")
    results = data.get("results", [])
    similar_results = data.get("similar_results", [])
    
    if not query or not results:
        print("JSON must have 'query' and 'results'.")
        sys.exit(1)
    
    print(f"Importing: query='{query}', {len(results)} results, {len(similar_results)} similar")
    
    client = APIClient()
    if not client.health_check():
        print("API not reachable. Check API_BASE_URL and that the API is running.")
        sys.exit(1)
    
    out = client.full_import(query=query, results=results, similar_results=similar_results)
    print("Result:", out)
    print("Done.")


if __name__ == "__main__":
    main()
