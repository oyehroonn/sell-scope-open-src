#!/usr/bin/env python3
"""
API Integration for Adobe Stock Scraper
Connects scraper results to the SellScope FastAPI backend
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

from adobe_stock_scraper import AdobeStockScraper

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", "")


class APIClient:
    """Client for SellScope API"""
    
    def __init__(self, base_url: str = None, token: str = None):
        self.base_url = base_url or API_BASE_URL
        self.token = token or API_TOKEN
        self.session = requests.Session()
        
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"
        
        self.session.headers["Content-Type"] = "application/json"
    
    def health_check(self) -> bool:
        """Check if API is reachable"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False
    
    def create_keyword(self, keyword: str, search_volume: int = None) -> Optional[Dict]:
        """Create or update a keyword record"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/keywords/",
                json={
                    "keyword": keyword,
                    "search_volume_estimate": search_volume,
                    "last_scraped": datetime.utcnow().isoformat()
                }
            )
            if response.status_code in [200, 201]:
                return response.json()
        except Exception as e:
            print(f"Error creating keyword: {e}")
        return None
    
    def save_asset(self, asset_data: Dict) -> Optional[Dict]:
        """Save an asset to the database"""
        try:
            payload = {
                "adobe_id": asset_data.get("asset_id"),
                "title": asset_data.get("title", ""),
                "asset_type": asset_data.get("asset_type", "photo"),
                "thumbnail_url": asset_data.get("thumbnail_url", ""),
                "preview_url": asset_data.get("asset_url", ""),
                "contributor_id": asset_data.get("contributor_id"),
                "contributor_name": asset_data.get("contributor_name", ""),
                "keywords": asset_data.get("keywords", "").split("|") if asset_data.get("keywords") else [],
                "category": asset_data.get("category", ""),
                "width": asset_data.get("width"),
                "height": asset_data.get("height"),
                "is_premium": asset_data.get("is_premium", False),
                "scraped_data": asset_data
            }
            
            response = self.session.post(
                f"{self.base_url}/api/assets/",
                json=payload
            )
            
            if response.status_code in [200, 201]:
                return response.json()
        except Exception as e:
            print(f"Error saving asset: {e}")
        return None
    
    def save_keyword_ranking(
        self, 
        keyword: str, 
        asset_id: str, 
        position: int,
        page: int = 1
    ) -> Optional[Dict]:
        """Save keyword ranking data"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/keywords/rankings/",
                json={
                    "keyword": keyword,
                    "asset_adobe_id": asset_id,
                    "position": position,
                    "page": page,
                    "recorded_at": datetime.utcnow().isoformat()
                }
            )
            if response.status_code in [200, 201]:
                return response.json()
        except Exception as e:
            print(f"Error saving ranking: {e}")
        return None
    
    def bulk_save_scrape_results(self, results: List[Dict], query: str) -> Dict:
        """Bulk save (legacy endpoint)"""
        try:
            response = self.session.post(
                f"{self.base_url}/scraper/bulk-import",
                json={
                    "query": query,
                    "results": results,
                    "scraped_at": datetime.utcnow().isoformat()
                }
            )
            if response.status_code in [200, 201]:
                return response.json()
        except Exception as e:
            print(f"Error bulk saving: {e}")
        return {"status": "error", "message": str(e)}

    def full_import(self, query: str, results: List[Dict], similar_results: List[Dict] = None) -> Dict:
        """Full import: Search, Contributors, Assets, Keywords, SimilarAssets, Categories."""
        try:
            response = self.session.post(
                f"{self.base_url}/scraper/full-import",
                json={
                    "query": query,
                    "results": results,
                    "similar_results": similar_results or [],
                    "scraped_at": datetime.utcnow().isoformat()
                }
            )
            if response.status_code in [200, 201]:
                return response.json()
        except Exception as e:
            print(f"Error full import: {e}")
        return {"status": "error", "message": str(e)}


def scrape_and_sync(
    query: str,
    max_results: int = 500,
    scrape_details: bool = True,
    scrape_similar: bool = False,
    max_similar_per_asset: int = 5,
    headless: bool = False,
    sync_to_api: bool = True,
    use_full_import: bool = True,
) -> List[Dict]:
    """
    Scrape Adobe Stock and optionally sync to API (full import: searches, assets, keywords, similar).
    """
    print(f"\n🔍 Scraping Adobe Stock for: '{query}'")
    print(f"   Max results: {max_results}")
    print(f"   Scrape details: {scrape_details}")
    print(f"   Scrape similar: {scrape_similar}")
    
    with AdobeStockScraper(headless=headless) as scraper:
        results = scraper.search(
            query=query,
            max_results=max_results,
            scrape_details=scrape_details,
            scrape_similar=scrape_similar,
            max_similar_per_asset=max_similar_per_asset,
        )
        
        csv_path = scraper.export_to_csv()
        json_path = scraper.export_to_json()
        similar_results = list(scraper.similar_results)
        
        print(f"\n📁 Exported to:")
        print(f"   CSV:  {csv_path}")
        print(f"   JSON: {json_path}")
    
    if sync_to_api and results:
        print(f"\n🔄 Syncing to API ({len(results)} results, {len(similar_results)} similar)...")
        client = APIClient()
        if not client.health_check():
            print("⚠️  API not reachable. Results saved to files only.")
            print(f"   Make sure the API is running at {API_BASE_URL}")
        elif use_full_import:
            sync_result = client.full_import(
                query=query,
                results=results,
                similar_results=similar_results,
            )
            print(f"   Full import result: {sync_result}")
        else:
            sync_result = client.bulk_save_scrape_results(results, query)
            print(f"   Bulk import result: {sync_result}")
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape and sync Adobe Stock data")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--max-results", type=int, default=500, help="Max results")
    parser.add_argument("-d", "--details", action="store_true", help="Scrape keywords")
    parser.add_argument("--similar", action="store_true", help="Scrape similar assets too")
    parser.add_argument("--max-similar", type=int, default=5, help="Max similar per asset")
    parser.add_argument("--headless", action="store_true", help="Headless mode")
    parser.add_argument("--no-sync", action="store_true", help="Don't sync to API")
    parser.add_argument("--bulk-only", action="store_true", help="Use legacy bulk-import instead of full-import")
    
    args = parser.parse_args()
    
    results = scrape_and_sync(
        query=args.query,
        max_results=args.max_results,
        scrape_details=args.details,
        scrape_similar=args.similar,
        max_similar_per_asset=args.max_similar,
        headless=args.headless,
        sync_to_api=not args.no_sync,
        use_full_import=not args.bulk_only,
    )
    
    print(f"\n✅ Complete! Scraped {len(results)} results.")


if __name__ == "__main__":
    main()
