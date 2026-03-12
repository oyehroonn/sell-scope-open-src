#!/usr/bin/env python3
"""
Interactive Adobe Stock Scraper Runner
Easy-to-use script for scraping Adobe Stock search results
"""

import os
import sys
from datetime import datetime
from adobe_stock_scraper import AdobeStockScraper


def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║           Adobe Stock Scraper - SellScope                     ║
║           Scrape search results with all product data         ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def get_user_input():
    """Get search parameters from user"""
    print("\n📝 Enter search parameters:\n")
    
    query = input("🔍 Search query (e.g., 'minimalist home office'): ").strip()
    if not query:
        print("❌ Search query is required!")
        sys.exit(1)
    
    max_results_input = input("📊 Maximum results to scrape (default: 500): ").strip()
    try:
        digits = "".join(c for c in max_results_input if c.isdigit())
        max_results = int(digits) if digits else 500
        max_results = min(max(1, max_results), 2000)
    except (ValueError, TypeError):
        max_results = 500
    
    scrape_details_input = input("🏷️  Also scrape keywords from detail pages? (y/N): ").strip().lower()
    scrape_details = scrape_details_input == 'y'
    
    headless_input = input("👻 Run in headless mode (no browser window)? (y/N): ").strip().lower()
    headless = headless_input == 'y'
    
    print("\n📁 Filter by content type (comma-separated, or press Enter for all):")
    print("   Options: photo, illustration, vector, video")
    content_type_input = input("   Content types: ").strip()
    content_types = [ct.strip() for ct in content_type_input.split(',') if ct.strip()] if content_type_input else None
    
    orientation_input = input("📐 Filter by orientation (horizontal/vertical/square, or Enter for all): ").strip().lower()
    orientation = orientation_input if orientation_input in ['horizontal', 'vertical', 'square'] else None
    
    return {
        "query": query,
        "max_results": max_results,
        "scrape_details": scrape_details,
        "headless": headless,
        "filters": {
            "content_type": content_types,
            "orientation": orientation
        } if (content_types or orientation) else None
    }


def run_scraper(params):
    """Run the scraper with given parameters"""
    print("\n" + "="*60)
    print(f"🚀 Starting scraper for: '{params['query']}'")
    print(f"   Max results: {params['max_results']}")
    print(f"   Scrape details: {params['scrape_details']}")
    print(f"   Headless: {params['headless']}")
    if params['filters']:
        print(f"   Filters: {params['filters']}")
    print("="*60 + "\n")
    
    with AdobeStockScraper(headless=params['headless']) as scraper:
        results = scraper.search(
            query=params['query'],
            max_results=params['max_results'],
            filters=params['filters'],
            scrape_details=params['scrape_details']
        )
        
        if results:
            csv_path = scraper.export_to_csv()
            json_path = scraper.export_to_json()
            
            print("\n" + "="*60)
            print("✅ SCRAPING COMPLETE!")
            print("="*60)
            print(f"\n📊 Total results scraped: {len(results)}")
            print(f"\n📁 Output files:")
            print(f"   CSV:  {csv_path}")
            print(f"   JSON: {json_path}")
            
            print("\n📋 Sample data (first 3 results):")
            for i, result in enumerate(results[:3], 1):
                print(f"\n   [{i}] {result.get('title', 'No title')[:60]}...")
                print(f"       ID: {result.get('asset_id')} | Type: {result.get('asset_type')}")
                print(f"       Contributor: {result.get('contributor_name', 'Unknown')}")
                print(f"       Premium: {result.get('is_premium', False)}")
            
            return csv_path, json_path
        else:
            print("\n❌ No results found!")
            return None, None


def main():
    print_banner()
    
    if len(sys.argv) > 1:
        from adobe_stock_scraper import main as scraper_main
        scraper_main()
    else:
        params = get_user_input()
        
        print("\n⚠️  Ready to start scraping. This may take a while for large result sets.")
        confirm = input("   Press Enter to continue or 'q' to quit: ").strip().lower()
        
        if confirm == 'q':
            print("👋 Cancelled.")
            sys.exit(0)
        
        run_scraper(params)


if __name__ == "__main__":
    main()
