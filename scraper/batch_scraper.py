#!/usr/bin/env python3
"""
Batch Adobe Stock Scraper
Scrape multiple search queries and combine results
"""

import os
import sys
import csv
import json
from datetime import datetime
from typing import List, Dict
import pandas as pd
from tqdm import tqdm

from adobe_stock_scraper import AdobeStockScraper


def load_queries_from_file(filepath: str) -> List[str]:
    """Load search queries from a text file (one query per line)"""
    queries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            query = line.strip()
            if query and not query.startswith('#'):
                queries.append(query)
    return queries


def batch_scrape(
    queries: List[str],
    max_results_per_query: int = 100,
    scrape_details: bool = False,
    headless: bool = True,
    output_dir: str = "output/batch"
) -> str:
    """
    Scrape multiple queries and combine results
    
    Args:
        queries: List of search queries
        max_results_per_query: Max results per query
        scrape_details: Whether to scrape keyword details
        headless: Run browser in headless mode
        output_dir: Output directory
    
    Returns:
        Path to combined CSV file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    all_results = []
    failed_queries = []
    
    print(f"\n🚀 Batch scraping {len(queries)} queries...")
    print(f"   Max results per query: {max_results_per_query}")
    print(f"   Scrape details: {scrape_details}")
    print(f"   Output dir: {output_dir}\n")
    
    with AdobeStockScraper(headless=headless) as scraper:
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Scraping: '{query}'")
            
            try:
                results = scraper.search(
                    query=query,
                    max_results=max_results_per_query,
                    scrape_details=scrape_details
                )
                
                if results:
                    all_results.extend(results)
                    print(f"   ✅ Got {len(results)} results")
                else:
                    print(f"   ⚠️ No results found")
                    failed_queries.append(query)
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                failed_queries.append(query)
    
    if all_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        csv_path = os.path.join(output_dir, f"batch_results_{timestamp}.csv")
        df = pd.DataFrame(all_results)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        json_path = os.path.join(output_dir, f"batch_results_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "queries": queries,
                "total_results": len(all_results),
                "failed_queries": failed_queries,
                "scraped_at": datetime.utcnow().isoformat(),
                "results": all_results
            }, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*60)
        print("✅ BATCH SCRAPING COMPLETE!")
        print("="*60)
        print(f"\n📊 Summary:")
        print(f"   Queries processed: {len(queries)}")
        print(f"   Failed queries: {len(failed_queries)}")
        print(f"   Total results: {len(all_results)}")
        print(f"\n📁 Output files:")
        print(f"   CSV:  {csv_path}")
        print(f"   JSON: {json_path}")
        
        if failed_queries:
            print(f"\n⚠️ Failed queries:")
            for q in failed_queries:
                print(f"   - {q}")
        
        return csv_path
    else:
        print("\n❌ No results collected!")
        return ""


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch Adobe Stock Scraper")
    parser.add_argument("-f", "--file", help="File with queries (one per line)")
    parser.add_argument("-q", "--queries", nargs="+", help="List of queries")
    parser.add_argument("-n", "--max-results", type=int, default=100, help="Max results per query")
    parser.add_argument("-d", "--details", action="store_true", help="Scrape keyword details")
    parser.add_argument("-o", "--output", default="output/batch", help="Output directory")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window")
    
    args = parser.parse_args()
    
    queries = []
    
    if args.file:
        queries = load_queries_from_file(args.file)
        print(f"Loaded {len(queries)} queries from {args.file}")
    elif args.queries:
        queries = args.queries
    else:
        print("📝 Enter queries (one per line, empty line to finish):")
        while True:
            query = input().strip()
            if not query:
                break
            queries.append(query)
    
    if not queries:
        print("❌ No queries provided!")
        sys.exit(1)
    
    batch_scrape(
        queries=queries,
        max_results_per_query=args.max_results,
        scrape_details=args.details,
        headless=not args.no_headless,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
