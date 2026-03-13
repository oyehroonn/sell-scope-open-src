"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ArrowUp,
  ArrowDown,
  Minus,
  Filter,
  Lightbulb,
  Loader2,
  Search,
  Sparkles,
  Target,
  TrendingUp,
  RefreshCw,
  Zap,
  BarChart3,
  Users,
  Hash,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface KeywordResult {
  keyword: string;
  nb_results: number;
  unique_contributors: number;
  demand_score: number;
  competition_score: number;
  gap_score: number;
  freshness_score: number;
  opportunity_score: number;
  trend: string;
  urgency: string;
  related_searches: string[];
  categories: { name: string }[];
}

interface TrendingKeyword {
  keyword: string;
  nb_results: number;
  asset_count: number;
  demand_score: number;
  competition_score: number;
  opportunity_score: number;
  trend: string;
  urgency: string;
}

export default function KeywordsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<KeywordResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [trendingKeywords, setTrendingKeywords] = useState<TrendingKeyword[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loadingTrending, setLoadingTrending] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTrendingKeywords();
  }, []);

  const fetchTrendingKeywords = async () => {
    setLoadingTrending(true);
    try {
      const response = await fetch(`${API_BASE}/keywords/trending?limit=12`);
      if (response.ok) {
        const data = await response.json();
        setTrendingKeywords(data);
      }
    } catch (e) {
      console.error("Failed to fetch trending keywords:", e);
    } finally {
      setLoadingTrending(false);
    }
  };

  const fetchSuggestions = async (query: string) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/keywords/suggestions?q=${encodeURIComponent(query)}&limit=8`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data);
      }
    } catch (e) {
      console.error("Failed to fetch suggestions:", e);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    setError(null);
    setHasSearched(true);
    
    try {
      const response = await fetch(`${API_BASE}/keywords/analyze/${encodeURIComponent(searchQuery.trim())}`);
      
      if (response.ok) {
        const data = await response.json();
        setResults([data]);
        
        // Also search for related keywords
        const searchResponse = await fetch(`${API_BASE}/keywords/search?q=${encodeURIComponent(searchQuery.trim())}&page_size=10`);
        if (searchResponse.ok) {
          const searchData = await searchResponse.json();
          if (searchData.keywords && searchData.keywords.length > 0) {
            const existingKeyword = data.keyword.toLowerCase();
            const additionalResults = searchData.keywords.filter(
              (k: KeywordResult) => k.keyword.toLowerCase() !== existingKeyword
            );
            setResults([data, ...additionalResults]);
          }
        }
      } else {
        setError("Failed to analyze keyword. Try again.");
      }
    } catch (e) {
      console.error("Search error:", e);
      setError("Failed to connect to the API. Make sure the backend is running.");
    } finally {
      setIsSearching(false);
    }
  };

  const handleSuggestionClick = (keyword: string) => {
    setSearchQuery(keyword);
    setSuggestions([]);
  };

  const handleInputChange = (value: string) => {
    setSearchQuery(value);
    fetchSuggestions(value);
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return "text-emerald-500";
    if (score >= 50) return "text-amber-500";
    return "text-red-500";
  };

  const getScoreBg = (score: number) => {
    if (score >= 70) return "bg-emerald-500";
    if (score >= 50) return "bg-amber-500";
    return "bg-red-500";
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "up":
        return <ArrowUp className="h-4 w-4 text-emerald-500" />;
      case "down":
        return <ArrowDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-400" />;
    }
  };

  const getCompetitionLabel = (score: number) => {
    if (score >= 70) return "High";
    if (score >= 40) return "Medium";
    return "Low";
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Keyword Research</h1>
          <p className="text-muted-foreground">
            Find high-opportunity keywords with demand analysis and opportunity scoring
          </p>
        </div>
        <Button onClick={fetchTrendingKeywords} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Search Section */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Enter a keyword or niche (e.g., 'minimalist home office')"
                value={searchQuery}
                onChange={(e) => handleInputChange(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="pl-10"
              />
              
              {/* Autocomplete suggestions */}
              {suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-900 border rounded-lg shadow-lg z-10">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      className="w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-800 text-sm"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <Button onClick={handleSearch} disabled={isSearching} className="gap-2">
              {isSearching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Analyze
            </Button>
          </div>

          {/* Trending Keywords as suggestions */}
          {!hasSearched && trendingKeywords.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-muted-foreground mb-2">Try these trending keywords:</p>
              <div className="flex flex-wrap gap-2">
                {trendingKeywords.slice(0, 8).map((kw) => (
                  <Badge
                    key={kw.keyword}
                    variant="outline"
                    className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors"
                    onClick={() => handleSuggestionClick(kw.keyword)}
                  >
                    {kw.keyword}
                    {kw.trend === "up" && <ArrowUp className="h-3 w-3 ml-1 text-emerald-500" />}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-950/20">
          <CardContent className="pt-6">
            <p className="text-red-600 dark:text-red-400">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      <AnimatePresence>
        {hasSearched && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">
                Results for "{searchQuery}"
              </h2>
              <Badge variant="secondary">{results.length} keywords</Badge>
            </div>

            <div className="grid gap-4">
              {results.map((result, index) => (
                <motion.div
                  key={result.keyword}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="hover:border-primary/50 transition-colors">
                    <CardContent className="pt-6">
                      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="font-semibold text-lg">{result.keyword}</h3>
                            {result.categories && result.categories.length > 0 && (
                              <Badge variant="outline">
                                {result.categories[0]?.name || "General"}
                              </Badge>
                            )}
                            {getTrendIcon(result.trend)}
                          </div>
                          
                          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <BarChart3 className="h-4 w-4" />
                              <span>Results: {formatNumber(result.nb_results)}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Users className="h-4 w-4" />
                              <span>Contributors: {result.unique_contributors}</span>
                            </div>
                            <div>
                              Competition: {getCompetitionLabel(result.competition_score)}
                            </div>
                            <Badge className={`${getScoreBg(result.demand_score)} text-white`}>
                              Demand: {result.demand_score.toFixed(0)}
                            </Badge>
                          </div>

                          {/* Related searches */}
                          {result.related_searches && result.related_searches.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-1">
                              <span className="text-xs text-muted-foreground mr-1">Related:</span>
                              {result.related_searches.slice(0, 5).map((related) => (
                                <Badge
                                  key={related}
                                  variant="secondary"
                                  className="text-xs cursor-pointer hover:bg-primary hover:text-primary-foreground"
                                  onClick={() => handleSuggestionClick(related)}
                                >
                                  {related}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-6">
                          <div className="text-center">
                            <div className="text-sm text-muted-foreground mb-1">
                              Opportunity Score
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="w-20">
                                <Progress value={result.opportunity_score} className="h-2" />
                              </div>
                              <span className={`text-2xl font-bold ${getScoreColor(result.opportunity_score)}`}>
                                {result.opportunity_score.toFixed(0)}
                              </span>
                            </div>
                            <Badge 
                              variant="outline" 
                              className={`mt-1 ${
                                result.urgency === "high" 
                                  ? "border-red-500 text-red-500" 
                                  : result.urgency === "medium"
                                    ? "border-amber-500 text-amber-500"
                                    : ""
                              }`}
                            >
                              {result.urgency} urgency
                            </Badge>
                          </div>

                          <div className="flex flex-col gap-2">
                            <Button variant="outline" size="sm" className="gap-1">
                              <Target className="h-4 w-4" />
                              Details
                            </Button>
                            <Button size="sm" className="gap-1">
                              <Lightbulb className="h-4 w-4" />
                              Brief
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Trending Keywords Section */}
      {!hasSearched && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-emerald-500" />
            <h2 className="text-xl font-semibold">Trending Keywords</h2>
          </div>

          {loadingTrending ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <Skeleton key={i} className="h-32 rounded-lg" />
              ))}
            </div>
          ) : trendingKeywords.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Hash className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Trending Data Yet</h3>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Scrape some assets with details enabled to see trending keywords and opportunity scores.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {trendingKeywords.map((kw, index) => (
                <motion.div
                  key={kw.keyword}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card 
                    className="cursor-pointer hover:border-primary/50 transition-all hover:shadow-md"
                    onClick={() => handleSuggestionClick(kw.keyword)}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-bold text-muted-foreground">
                            {index + 1}
                          </span>
                          {getTrendIcon(kw.trend)}
                        </div>
                        <div className={`text-2xl font-bold ${getScoreColor(kw.opportunity_score)}`}>
                          {kw.opportunity_score.toFixed(0)}
                        </div>
                      </div>
                      
                      <h3 className="font-semibold mb-2">{kw.keyword}</h3>
                      
                      <div className="flex items-center justify-between text-sm text-muted-foreground">
                        <span>{formatNumber(kw.nb_results)} results</span>
                        <span>{kw.asset_count} assets</span>
                      </div>
                      
                      <Progress value={kw.opportunity_score} className="h-1 mt-3" />
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!hasSearched && !loadingTrending && trendingKeywords.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <Search className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Start Your Research</h3>
          <p className="text-muted-foreground max-w-md">
            Enter a keyword or niche to discover opportunity scores, competition
            analysis, and trending data for Adobe Stock.
          </p>
        </div>
      )}
    </div>
  );
}
