#!/usr/bin/env python3
"""
Quick test script for the Adobe Stock Scraper
Tests basic functionality with a small number of results
"""

import sys
from adobe_stock_scraper import AdobeStockScraper


def test_basic_search():
    """Test basic search functionality"""
    print("=" * 60)
    print("Testing Adobe Stock Scraper")
    print("=" * 60)
    
    query = "home office"
    max_results = 20
    
    print(f"\n🔍 Testing search for: '{query}'")
    print(f"   Max results: {max_results}")
    print(f"   Headless: False (visible browser for debugging)\n")
    
    try:
        with AdobeStockScraper(headless=False) as scraper:
            results = scraper.search(
                query=query,
                max_results=max_results,
                scrape_details=False,
            )
            
            if results:
                print(f"\n✅ SUCCESS! Found {len(results)} results")
                
                csv_path = scraper.export_to_csv()
                print(f"\n📁 Exported to: {csv_path}")
                
                print("\n📋 Sample results:")
                for i, result in enumerate(results[:5], 1):
                    print(f"\n   [{i}] {result.get('title', 'No title')[:50]}...")
                    print(f"       Asset ID: {result.get('asset_id')}")
                    print(f"       Type: {result.get('asset_type')}")
                    print(f"       Contributor: {result.get('contributor_name', 'Unknown')}")
                    print(f"       Premium: {result.get('is_premium', False)}")
                    print(f"       Size: {result.get('width')}x{result.get('height')}")
                
                return True
            else:
                print("\n❌ No results found!")
                return False
                
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_search()
    sys.exit(0 if success else 1)
