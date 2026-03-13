"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { HolographicLoader } from "@/components/ui/holographic-loader";
import { AssetCard, AssetCardSkeleton, AssetData } from "@/components/ui/asset-card";
import {
  Search,
  Sparkles,
  SlidersHorizontal,
  X,
  ImageIcon,
  Video,
  Layers,
  TrendingUp,
  Clock,
  Zap,
  Database,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Track which assets have been added to library in this session
const addedToLibrary = new Set<string>();

const SUGGESTED_SEARCHES = [
  "nature landscape",
  "business meeting",
  "technology abstract",
  "food photography",
  "minimalist design",
  "urban architecture",
];

// Session cache for search results
const searchCache = new Map<string, { assets: AssetData[]; timestamp: number }>();
const CACHE_DURATION = 30 * 60 * 1000; // 30 minutes

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [maxResults, setMaxResults] = useState(20);
  const [isSearching, setIsSearching] = useState(false);
  const [progress, setProgress] = useState(0);
  const [loadingMessage, setLoadingMessage] = useState("Initializing search...");
  const [results, setResults] = useState<AssetData[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [fromCache, setFromCache] = useState(false);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("recentSearches");
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  const saveRecentSearch = (search: string) => {
    const updated = [search, ...recentSearches.filter(s => s !== search)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem("recentSearches", JSON.stringify(updated));
  };

  const getCacheKey = (q: string, max: number) => `${q.toLowerCase().trim()}_${max}`;

  const checkCache = (q: string, max: number): AssetData[] | null => {
    const key = getCacheKey(q, max);
    const cached = searchCache.get(key);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      return cached.assets;
    }
    searchCache.delete(key);
    return null;
  };

  const setCache = (q: string, max: number, assets: AssetData[]) => {
    const key = getCacheKey(q, max);
    searchCache.set(key, { assets, timestamp: Date.now() });
  };

  const simulateProgress = useCallback(() => {
    const messages = [
      "Connecting to Adobe Stock...",
      "Scanning search results...",
      "Extracting asset data...",
      "Fetching keywords and metadata...",
      "Processing images...",
      "Analyzing content...",
      "Finalizing results...",
    ];
    
    let currentProgress = 0;
    progressIntervalRef.current = setInterval(() => {
      currentProgress += Math.random() * 12;
      if (currentProgress > 95) currentProgress = 95;
      setProgress(currentProgress);
      
      const messageIndex = Math.min(
        Math.floor((currentProgress / 100) * messages.length),
        messages.length - 1
      );
      setLoadingMessage(messages[messageIndex]);
    }, 600);
    
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    const searchQuery = query.trim();
    saveRecentSearch(searchQuery);
    
    // Check cache first
    const cachedResults = checkCache(searchQuery, maxResults);
    if (cachedResults && cachedResults.length > 0) {
      setFromCache(true);
      setResults(cachedResults);
      setHasSearched(true);
      return;
    }
    
    setFromCache(false);
    setIsSearching(true);
    setHasSearched(true);
    setProgress(0);
    setResults([]);
    
    const stopProgress = simulateProgress();
    
    try {
      const response = await fetch(`${API_BASE}/scraper/live-scrape`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: searchQuery,
          max_results: maxResults,
          scrape_details: true,
        }),
      });
      
      if (!response.ok) throw new Error("Search failed");
      
      const data = await response.json();
      setProgress(100);
      setLoadingMessage("Complete!");
      
      await new Promise(resolve => setTimeout(resolve, 500));
      
      let mappedAssets: AssetData[] = [];
      
      if (data.assets && data.assets.length > 0) {
        mappedAssets = data.assets.map((a: any) => ({
          adobe_id: a.adobe_id,
          title: a.title,
          thumbnail_url: a.thumbnail_url,
          preview_url: a.preview_url,
          asset_type: a.asset_type || "photo",
          contributor_name: a.contributor_name,
          contributor_id: a.contributor_id,
          is_premium: a.is_premium,
          is_ai_generated: a.is_ai_generated,
          is_editorial: a.is_editorial,
          width: a.width,
          height: a.height,
          orientation: a.orientation,
          keyword_count: a.keyword_count || 0,
        }));
      } else {
        // Fallback: fetch from assets endpoint
        const assetsResponse = await fetch(
          `${API_BASE}/assets/?limit=${maxResults}&search=${encodeURIComponent(searchQuery)}`
        );
        
        if (assetsResponse.ok) {
          const assetsData = await assetsResponse.json();
          mappedAssets = (assetsData.assets || []).map((a: any) => ({
            adobe_id: a.adobe_id,
            title: a.title,
            thumbnail_url: a.thumbnail_url,
            preview_url: a.preview_url,
            asset_type: a.asset_type || "photo",
            contributor_name: a.contributor_name,
            contributor_id: a.contributor_id,
            is_premium: a.is_premium,
            is_ai_generated: a.is_ai_generated,
            is_editorial: a.is_editorial,
            width: a.width,
            height: a.height,
            orientation: a.orientation,
            keyword_count: a.keywords?.length || 0,
            keywords: a.keywords,
          }));
        }
      }
      
      // Cache the results
      if (mappedAssets.length > 0) {
        setCache(searchQuery, maxResults, mappedAssets);
      }
      
      setResults(mappedAssets);
    } catch (error) {
      console.error("Search error:", error);
      setLoadingMessage("Search failed. Please try again.");
    } finally {
      stopProgress();
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch();
  };

  const clearCache = () => {
    searchCache.clear();
    setFromCache(false);
  };

  const handleAddToLibrary = async (asset: AssetData) => {
    // Call API to add asset to library
    const response = await fetch(`${API_BASE}/assets/${asset.adobe_id}/library`, {
      method: "POST",
    });
    
    if (!response.ok) {
      throw new Error("Failed to add to library");
    }
    
    // Mark it as added in the session tracker
    addedToLibrary.add(asset.adobe_id);
  };
  
  const isInLibrary = (assetId: string) => addedToLibrary.has(assetId);

  return (
    <div className="min-h-screen">
      {/* Hero Search Section */}
      <div className={`transition-all duration-500 ${hasSearched ? "py-6" : "py-20"}`}>
        <AnimatePresence mode="wait">
          {!hasSearched && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="text-center mb-8"
            >
              <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-violet-600 via-blue-600 to-emerald-600 bg-clip-text text-transparent mb-4">
                Discover Stock Assets
              </h1>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Search and analyze millions of stock photos, videos, and vectors from Adobe Stock
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Search Bar */}
        <motion.div
          layout
          className={`max-w-3xl mx-auto ${hasSearched ? "" : "px-4"}`}
        >
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-violet-500/20 via-blue-500/20 to-emerald-500/20 rounded-2xl blur-xl" />
            <div className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-800 p-2">
              <div className="flex items-center gap-2">
                <div className="flex-1 flex items-center gap-3 px-4">
                  <Search className="h-5 w-5 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Search for stock assets..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="border-0 bg-transparent text-lg focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-muted-foreground/60"
                    disabled={isSearching}
                  />
                  {query && (
                    <button
                      onClick={() => setQuery("")}
                      className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
                    >
                      <X className="h-4 w-4 text-muted-foreground" />
                    </button>
                  )}
                </div>
                
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowFilters(!showFilters)}
                  className={showFilters ? "bg-violet-100 dark:bg-violet-900/30" : ""}
                >
                  <SlidersHorizontal className="h-5 w-5" />
                </Button>
                
                <Button
                  onClick={handleSearch}
                  disabled={!query.trim() || isSearching}
                  className="bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-700 hover:to-blue-700 text-white px-6 rounded-xl"
                >
                  {isSearching ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    >
                      <Sparkles className="h-5 w-5" />
                    </motion.div>
                  ) : (
                    "Search"
                  )}
                </Button>
              </div>
              
              {/* Filters panel */}
              <AnimatePresence>
                {showFilters && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="pt-4 mt-2 border-t border-gray-200 dark:border-gray-800">
                      <div className="flex flex-wrap items-center gap-4">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-muted-foreground">Results:</span>
                          <select
                            value={maxResults}
                            onChange={(e) => setMaxResults(parseInt(e.target.value))}
                            className="bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-1.5 text-sm border-0 focus:ring-2 focus:ring-violet-500"
                          >
                            <option value={10}>10</option>
                            <option value={20}>20</option>
                            <option value={50}>50</option>
                            <option value={100}>100</option>
                          </select>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="cursor-pointer hover:bg-violet-100 dark:hover:bg-violet-900/30">
                            <ImageIcon className="h-3 w-3 mr-1" />
                            Photos
                          </Badge>
                          <Badge variant="outline" className="cursor-pointer hover:bg-violet-100 dark:hover:bg-violet-900/30">
                            <Video className="h-3 w-3 mr-1" />
                            Videos
                          </Badge>
                          <Badge variant="outline" className="cursor-pointer hover:bg-violet-100 dark:hover:bg-violet-900/30">
                            <Layers className="h-3 w-3 mr-1" />
                            Vectors
                          </Badge>
                        </div>
                        
                        {searchCache.size > 0 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={clearCache}
                            className="ml-auto text-xs"
                          >
                            <Database className="h-3 w-3 mr-1" />
                            Clear Cache ({searchCache.size})
                          </Button>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>

        {/* Suggestions */}
        <AnimatePresence>
          {!hasSearched && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mt-8 text-center"
            >
              {recentSearches.length > 0 && (
                <div className="mb-6">
                  <p className="text-sm text-muted-foreground mb-3 flex items-center justify-center gap-2">
                    <Clock className="h-4 w-4" />
                    Recent searches
                  </p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {recentSearches.map((search) => (
                      <Badge
                        key={search}
                        variant="secondary"
                        className="cursor-pointer hover:bg-violet-100 dark:hover:bg-violet-900/30 transition-colors"
                        onClick={() => {
                          setQuery(search);
                        }}
                      >
                        {checkCache(search, maxResults) && (
                          <Zap className="h-3 w-3 mr-1 text-amber-500" />
                        )}
                        {search}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              <p className="text-sm text-muted-foreground mb-3 flex items-center justify-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Popular searches
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTED_SEARCHES.map((suggestion) => (
                  <Badge
                    key={suggestion}
                    variant="outline"
                    className="cursor-pointer hover:bg-violet-100 dark:hover:bg-violet-900/30 transition-colors"
                    onClick={() => setQuery(suggestion)}
                  >
                    {suggestion}
                  </Badge>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Loading State */}
      <AnimatePresence>
        {isSearching && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <HolographicLoader progress={progress} message={loadingMessage} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Grid */}
      <AnimatePresence>
        {!isSearching && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  Search Results
                  {fromCache && (
                    <Badge variant="secondary" className="text-xs font-normal">
                      <Zap className="h-3 w-3 mr-1 text-amber-500" />
                      From Cache
                    </Badge>
                  )}
                </h2>
                <p className="text-muted-foreground">
                  Found {results.length} assets for "{query}"
                </p>
              </div>
              <Badge variant="secondary" className="text-sm">
                {results.length} results
              </Badge>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {results.map((asset, index) => (
                <AssetCard 
                  key={asset.adobe_id} 
                  asset={asset} 
                  index={index}
                  showAddToLibrary={true}
                  inLibrary={isInLibrary(asset.adobe_id)}
                  onAddToLibrary={handleAddToLibrary}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty state after search */}
      {!isSearching && hasSearched && results.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-violet-500/20 to-blue-500/20 flex items-center justify-center">
            <Search className="h-10 w-10 text-muted-foreground" />
          </div>
          <h3 className="text-xl font-semibold mb-2">No results found</h3>
          <p className="text-muted-foreground mb-6">
            Try adjusting your search terms or browse popular categories
          </p>
          <Button
            variant="outline"
            onClick={() => {
              setHasSearched(false);
              setQuery("");
            }}
          >
            Start New Search
          </Button>
        </motion.div>
      )}
    </div>
  );
}
