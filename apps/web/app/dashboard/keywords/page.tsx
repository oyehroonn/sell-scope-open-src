"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ArrowUp,
  ArrowDown,
  Minus,
  Lightbulb,
  Loader2,
  Search,
  Sparkles,
  Target,
  RefreshCw,
  BarChart3,
  Users,
  Hash,
  X,
  CheckCircle,
  AlertTriangle,
  Clock,
  Zap,
  Camera,
  FileText,
  Copy,
  Check,
  Save,
  Star,
  Bookmark,
  BookmarkCheck,
  Trash2,
  Info,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { EnhancedDetailsModal, ProgressIndicator } from "@/components/keyword-research";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SAVED_RESEARCHES_KEY = "sellscope_saved_researches";
const OPPORTUNITY_KEYWORDS_KEY = "sellscope_opportunity_keywords";

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
  scraped_at?: string;
  source?: string;
}

interface DeepAnalysisData {
  keyword: string;
  depth: string;
  search_results: any;
  assets: any[];
  asset_details: any[];
  contributor_profiles: any[];
  market_analysis: any;
  scoring: any;
  visualizations: any;
  scraped_at?: string;
  source?: string;
  errors?: string[];
}

interface SavedResearch extends KeywordResult {
  saved_at: string;
  is_opportunity: boolean;
  deep_analysis?: DeepAnalysisData;  // Store the full deep analysis
}

function Modal({ 
  isOpen, 
  onClose, 
  title, 
  children 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  title: string;
  children: React.ReactNode;
}) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative z-50 w-full max-w-2xl max-h-[85vh] overflow-y-auto bg-white dark:bg-gray-900 rounded-lg shadow-xl m-4">
        <div className="sticky top-0 flex items-center justify-between p-4 border-b bg-white dark:bg-gray-900">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-4">
          {children}
        </div>
      </div>
    </div>
  );
}

export default function KeywordsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<KeywordResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [useLiveScraping, setUseLiveScraping] = useState(true);
  const [researchDepth, setResearchDepth] = useState<"simple" | "medium" | "deep">("simple");
  const [showDepthComparison, setShowDepthComparison] = useState(false);
  
  const [savedResearches, setSavedResearches] = useState<SavedResearch[]>([]);
  const [activeTab, setActiveTab] = useState<"researched" | "saved">("researched");
  
  const [selectedKeyword, setSelectedKeyword] = useState<KeywordResult | null>(null);
  const [deepAnalysisData, setDeepAnalysisData] = useState<any | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showBriefModal, setShowBriefModal] = useState(false);
  const [copiedBrief, setCopiedBrief] = useState(false);

  useEffect(() => {
    loadSavedResearches();
  }, []);

  const loadSavedResearches = async () => {
    try {
      // First try to load from API (backend persistence)
      const response = await fetch(`${API_BASE}/keywords/saved-researches`);
      if (response.ok) {
        const data = await response.json();
        setSavedResearches(data);
        // Also sync to localStorage as backup
        localStorage.setItem(SAVED_RESEARCHES_KEY, JSON.stringify(data));
        return;
      }
    } catch (e) {
      console.error("Failed to load from API:", e);
    }
    
    // Fallback to localStorage
    try {
      const saved = localStorage.getItem(SAVED_RESEARCHES_KEY);
      if (saved) {
        setSavedResearches(JSON.parse(saved));
      }
    } catch (e) {
      console.error("Failed to load saved researches:", e);
    }
  };

  const saveResearch = async (result: KeywordResult, deepData?: DeepAnalysisData | null) => {
    const requestData = {
      ...result,
      deep_analysis: deepData || undefined,
      is_opportunity: isMarkedAsOpportunity(result.keyword),
    };
    
    try {
      // Save to backend
      const response = await fetch(`${API_BASE}/keywords/saved-researches`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData),
      });
      
      if (response.ok) {
        const savedData = await response.json();
        // Reload all saved researches to stay in sync
        await loadSavedResearches();
        return;
      }
    } catch (e) {
      console.error("Failed to save to API:", e);
    }
    
    // Fallback to localStorage
    const existing = savedResearches.find(r => r.keyword.toLowerCase() === result.keyword.toLowerCase());
    if (existing) {
      const updated = savedResearches.map(r => 
        r.keyword.toLowerCase() === result.keyword.toLowerCase()
          ? { 
              ...result, 
              saved_at: new Date().toISOString(), 
              is_opportunity: r.is_opportunity,
              deep_analysis: deepData || r.deep_analysis,
            }
          : r
      );
      localStorage.setItem(SAVED_RESEARCHES_KEY, JSON.stringify(updated));
      setSavedResearches(updated);
    } else {
      const newResearch: SavedResearch = {
        ...result,
        saved_at: new Date().toISOString(),
        is_opportunity: false,
        deep_analysis: deepData || undefined,
      };
      const updated = [newResearch, ...savedResearches];
      localStorage.setItem(SAVED_RESEARCHES_KEY, JSON.stringify(updated));
      setSavedResearches(updated);
    }
  };

  const removeResearch = async (keyword: string) => {
    try {
      // Delete from backend
      const response = await fetch(`${API_BASE}/keywords/saved-researches/${encodeURIComponent(keyword)}`, {
        method: "DELETE",
      });
      
      if (response.ok) {
        await loadSavedResearches();
        return;
      }
    } catch (e) {
      console.error("Failed to delete from API:", e);
    }
    
    // Fallback to localStorage
    const updated = savedResearches.filter(r => r.keyword.toLowerCase() !== keyword.toLowerCase());
    localStorage.setItem(SAVED_RESEARCHES_KEY, JSON.stringify(updated));
    setSavedResearches(updated);
  };

  const toggleOpportunity = async (keyword: string) => {
    const current = savedResearches.find(r => r.keyword.toLowerCase() === keyword.toLowerCase());
    const newValue = !current?.is_opportunity;
    
    try {
      // Update in backend
      const response = await fetch(
        `${API_BASE}/keywords/saved-researches/${encodeURIComponent(keyword)}/opportunity?is_opportunity=${newValue}`,
        { method: "PATCH" }
      );
      
      if (response.ok) {
        await loadSavedResearches();
        return;
      }
    } catch (e) {
      console.error("Failed to update opportunity status:", e);
    }
    
    // Fallback to localStorage
    const updated = savedResearches.map(r => 
      r.keyword.toLowerCase() === keyword.toLowerCase()
        ? { ...r, is_opportunity: newValue }
        : r
    );
    localStorage.setItem(SAVED_RESEARCHES_KEY, JSON.stringify(updated));
    setSavedResearches(updated);
    
    const opportunities = updated.filter(r => r.is_opportunity);
    localStorage.setItem(OPPORTUNITY_KEYWORDS_KEY, JSON.stringify(opportunities));
  };

  const isResearchSaved = (keyword: string) => {
    return savedResearches.some(r => r.keyword.toLowerCase() === keyword.toLowerCase());
  };

  const isMarkedAsOpportunity = (keyword: string) => {
    const saved = savedResearches.find(r => r.keyword.toLowerCase() === keyword.toLowerCase());
    return saved?.is_opportunity || false;
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
    setSuggestions([]);
    setDeepAnalysisData(null); // Reset deep analysis data for new search
    
    try {
      // Use different endpoint based on research depth
      if (researchDepth === "simple") {
        // Simple analysis - use regular endpoint
        const liveParam = useLiveScraping ? "live=true" : "";
        const response = await fetch(
          `${API_BASE}/keywords/analyze/${encodeURIComponent(searchQuery.trim())}?${liveParam}`
        );
        
        if (response.ok) {
          const data = await response.json();
          setResults([data]);
          
          // Also fetch related keywords
          const searchResponse = await fetch(
            `${API_BASE}/keywords/search?q=${encodeURIComponent(searchQuery.trim())}&page_size=10`
          );
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
          const errorData = await response.json().catch(() => ({}));
          setError(errorData.detail || "Failed to analyze keyword. Try again.");
        }
      } else {
        // Deep analysis - use deep endpoint
        const response = await fetch(
          `${API_BASE}/keywords/analyze/${encodeURIComponent(searchQuery.trim())}/deep?depth=${researchDepth}`
        );
        
        if (response.ok) {
          const data = await response.json();
          // Store the full deep analysis data for the modal
          setDeepAnalysisData(data);
          
          // Convert deep analysis to KeywordResult format for the list view
          const keywordResult: KeywordResult = {
            keyword: data.keyword,
            nb_results: data.search_results?.nb_results || 0,
            unique_contributors: data.market_analysis?.unique_contributors || 0,
            demand_score: data.scoring?.demand_score || 0,
            competition_score: data.scoring?.competition_score || 0,
            gap_score: data.scoring?.gap_score || 50,
            freshness_score: data.scoring?.freshness_score || 50,
            opportunity_score: data.scoring?.opportunity_score || 0,
            trend: data.scoring?.trend || "stable",
            urgency: data.scoring?.urgency || "medium",
            related_searches: data.search_results?.related_searches || [],
            categories: data.search_results?.categories || [],
            scraped_at: data.scraped_at,
            source: `deep-${researchDepth}`,
          };
          setResults([keywordResult]);
        } else {
          const errorData = await response.json().catch(() => ({}));
          setError(errorData.detail || "Failed to run deep analysis. Try again.");
        }
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

  const openDetailsModal = useCallback((result: KeywordResult) => {
    setSelectedKeyword(result);
    
    // Check if this is a saved research with deep analysis data
    const savedResearch = savedResearches.find(
      r => r.keyword.toLowerCase() === result.keyword.toLowerCase()
    );
    
    if (savedResearch?.deep_analysis) {
      // Use the saved deep analysis data
      setDeepAnalysisData(savedResearch.deep_analysis);
    }
    // If the current deepAnalysisData matches this keyword, keep it
    // Otherwise it will be null (for simple searches)
    
    setShowDetailsModal(true);
  }, [savedResearches]);

  const openBriefModal = useCallback((result: KeywordResult) => {
    setSelectedKeyword(result);
    setShowBriefModal(true);
  }, []);

  const closeDetailsModal = useCallback(() => {
    setShowDetailsModal(false);
  }, []);

  const closeBriefModal = useCallback(() => {
    setShowBriefModal(false);
  }, []);

  const generateBrief = (kw: KeywordResult): string => {
    const competitionLevel = kw.competition_score >= 70 ? "high" : kw.competition_score >= 40 ? "medium" : "low";
    const demandLevel = kw.demand_score >= 70 ? "high" : kw.demand_score >= 40 ? "medium" : "low";
    
    let recommendation = "";
    if (kw.opportunity_score >= 70) {
      recommendation = "This is a HIGH PRIORITY keyword. Create content immediately to capitalize on the opportunity.";
    } else if (kw.opportunity_score >= 50) {
      recommendation = "This is a GOOD OPPORTUNITY. Add to your production queue and create quality content.";
    } else {
      recommendation = "This keyword has LIMITED OPPORTUNITY. Consider focusing on higher-scoring alternatives.";
    }

    const contentIdeas = [
      `Professional ${kw.keyword} photography with clean backgrounds`,
      `${kw.keyword} in modern, minimalist settings`,
      `Diverse people interacting with ${kw.keyword}`,
      `${kw.keyword} lifestyle and workspace shots`,
      `Abstract or conceptual ${kw.keyword} imagery`,
    ];

    return `KEYWORD BRIEF: ${kw.keyword.toUpperCase()}
${"=".repeat(50)}

OPPORTUNITY ANALYSIS
Opportunity Score: ${kw.opportunity_score.toFixed(0)}/100
Demand Score: ${kw.demand_score.toFixed(0)}/100 (${demandLevel})
Competition Score: ${kw.competition_score.toFixed(0)}/100 (${competitionLevel})
Urgency: ${kw.urgency.toUpperCase()}
Trend: ${kw.trend.toUpperCase()}

MARKET DATA
Total Results on Adobe Stock: ${kw.nb_results.toLocaleString()}
Unique Contributors: ${kw.unique_contributors}

RECOMMENDATION
${recommendation}

CONTENT IDEAS
${contentIdeas.map((idea, i) => `${i + 1}. ${idea}`).join("\n")}

RELATED KEYWORDS
${kw.related_searches?.slice(0, 8).join(", ") || "No related keywords found"}

Generated: ${new Date().toLocaleString()}`;
  };

  const copyBrief = async () => {
    if (!selectedKeyword) return;
    const brief = generateBrief(selectedKeyword);
    await navigator.clipboard.writeText(brief);
    setCopiedBrief(true);
    setTimeout(() => setCopiedBrief(false), 2000);
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

  const renderKeywordCard = (result: KeywordResult, showSaveActions: boolean = true, isSavedView: boolean = false) => {
    const isSaved = isResearchSaved(result.keyword);
    const isOpportunity = isMarkedAsOpportunity(result.keyword);

    return (
      <Card key={result.keyword} className="hover:border-primary/50 transition-colors">
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
                {isOpportunity && (
                  <Badge className="bg-amber-500 text-white">
                    <Star className="h-3 w-3 mr-1 fill-current" />
                    Opportunity
                  </Badge>
                )}
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

            <div className="flex items-center gap-4">
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
                {showSaveActions && (
                  <div className="flex gap-1">
                    <Button
                      variant={isSaved ? "secondary" : "outline"}
                      size="sm"
                      className="gap-1"
                      onClick={() => isSaved ? removeResearch(result.keyword) : saveResearch(result, deepAnalysisData)}
                      title={isSaved ? "Remove from saved" : "Save research"}
                    >
                      {isSaved ? (
                        <BookmarkCheck className="h-4 w-4 text-emerald-500" />
                      ) : (
                        <Save className="h-4 w-4" />
                      )}
                      {isSaved ? "Saved" : "Save"}
                    </Button>
                    {isSaved && (
                      <Button
                        variant={isOpportunity ? "default" : "outline"}
                        size="sm"
                        className={`gap-1 ${isOpportunity ? "bg-amber-500 hover:bg-amber-600" : ""}`}
                        onClick={() => toggleOpportunity(result.keyword)}
                        title={isOpportunity ? "Unmark as opportunity" : "Mark as opportunity"}
                      >
                        <Star className={`h-4 w-4 ${isOpportunity ? "fill-current" : ""}`} />
                      </Button>
                    )}
                  </div>
                )}
                {isSavedView && (
                  <div className="flex gap-1">
                    <Button
                      variant={isOpportunity ? "default" : "outline"}
                      size="sm"
                      className={`gap-1 ${isOpportunity ? "bg-amber-500 hover:bg-amber-600" : ""}`}
                      onClick={() => toggleOpportunity(result.keyword)}
                      title={isOpportunity ? "Unmark as opportunity" : "Mark as opportunity"}
                    >
                      <Star className={`h-4 w-4 ${isOpportunity ? "fill-current" : ""}`} />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1 text-red-500 hover:text-red-600 hover:bg-red-50"
                      onClick={() => removeResearch(result.keyword)}
                      title="Remove from saved"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                )}
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="gap-1"
                  onClick={() => openDetailsModal(result)}
                >
                  <Target className="h-4 w-4" />
                  Details
                </Button>
                <Button 
                  size="sm" 
                  className="gap-1"
                  onClick={() => openBriefModal(result)}
                >
                  <Lightbulb className="h-4 w-4" />
                  Brief
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
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
      </div>

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
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Analyze
                </>
              )}
            </Button>
          </div>

          {/* Research Depth Selector */}
          <div className="mt-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Research Depth:</span>
                <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                  {(["simple", "medium", "deep"] as const).map((depth) => {
                    const isSelected = researchDepth === depth;
                    const colors = {
                      simple: {
                        bg: "bg-blue-500",
                        text: "text-blue-500",
                        border: "border-blue-500",
                        glow: "shadow-[0_0_15px_rgba(59,130,246,0.5)]",
                        badge: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
                      },
                      medium: {
                        bg: "bg-purple-500",
                        text: "text-purple-500",
                        border: "border-purple-500",
                        glow: "shadow-[0_0_15px_rgba(168,85,247,0.5)]",
                        badge: "bg-purple-500/10 text-purple-600 dark:text-purple-400",
                      },
                      deep: {
                        bg: "bg-amber-500",
                        text: "text-amber-500",
                        border: "border-amber-500",
                        glow: "shadow-[0_0_15px_rgba(245,158,11,0.5)]",
                        badge: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
                      },
                    }[depth];
                    
                    return (
                      <button
                        key={depth}
                        onClick={() => setResearchDepth(depth)}
                        disabled={isSearching}
                        className={`
                          flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium
                          transition-all duration-200
                          ${isSelected
                            ? `bg-gray-900 dark:bg-gray-100 ${colors.text} ${colors.glow}`
                            : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-200/50 dark:hover:bg-gray-700/50"
                          }
                          ${isSearching ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
                        `}
                      >
                        {depth === "simple" && <Zap className={`h-3.5 w-3.5 ${isSelected ? colors.text : ""}`} />}
                        {depth === "medium" && <Sparkles className={`h-3.5 w-3.5 ${isSelected ? colors.text : ""}`} />}
                        {depth === "deep" && <Target className={`h-3.5 w-3.5 ${isSelected ? colors.text : ""}`} />}
                        <span className={isSelected ? "text-white dark:text-gray-900" : ""}>{depth.charAt(0).toUpperCase() + depth.slice(1)}</span>
                        {depth === "medium" && !isSelected && (
                          <span className="ml-1 px-1.5 py-0.5 text-[9px] font-medium uppercase bg-purple-500/10 text-purple-600 dark:text-purple-400 rounded">
                            Best
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
                <button
                  onClick={() => setShowDepthComparison(!showDepthComparison)}
                  className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                >
                  {showDepthComparison ? <ChevronUp className="h-4 w-4" /> : <Info className="h-4 w-4" />}
                </button>
              </div>
              <div className={`
                flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border
                ${researchDepth === "simple" 
                  ? "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30" 
                  : researchDepth === "medium" 
                    ? "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30" 
                    : "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30"
                }
              `}>
                <Clock className="h-3 w-3" />
                {researchDepth === "simple" ? "~30-60 sec" : researchDepth === "medium" ? "~3-5 min" : "~10-15 min"}
              </div>
            </div>

            {/* Depth Comparison Panel */}
            {showDepthComparison && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-4 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700">
                {(["simple", "medium", "deep"] as const).map((depth) => {
                  const isSelected = researchDepth === depth;
                  const config = {
                    simple: {
                      name: "Simple",
                      subtitle: "Quick Analysis",
                      time: "30-60 sec",
                      assets: 20,
                      features: ["Search results analysis", "Basic scores", "Related keywords", "Categories"],
                      color: "blue",
                      borderColor: "border-blue-500",
                      glowColor: "shadow-[0_0_20px_rgba(59,130,246,0.4)]",
                      iconBg: "bg-blue-500",
                      textColor: "text-blue-500",
                      badgeBg: "bg-blue-500",
                    },
                    medium: {
                      name: "Deep",
                      subtitle: "Recommended",
                      time: "3-5 min",
                      assets: 50,
                      features: ["All Simple features", "50 asset details", "10 contributor profiles", "Price analysis", "Market charts"],
                      color: "purple",
                      borderColor: "border-purple-500",
                      glowColor: "shadow-[0_0_20px_rgba(168,85,247,0.4)]",
                      iconBg: "bg-purple-500",
                      textColor: "text-purple-500",
                      badgeBg: "bg-purple-500",
                    },
                    deep: {
                      name: "Comprehensive",
                      subtitle: "Full Analysis",
                      time: "10-15 min",
                      assets: 100,
                      features: ["All Deep features", "100 asset details", "20 contributor profiles", "Keyword network", "Full portfolio analysis"],
                      color: "amber",
                      borderColor: "border-amber-500",
                      glowColor: "shadow-[0_0_20px_rgba(245,158,11,0.4)]",
                      iconBg: "bg-amber-500",
                      textColor: "text-amber-500",
                      badgeBg: "bg-amber-500",
                    },
                  }[depth];
                  
                  return (
                    <div
                      key={depth}
                      onClick={() => setResearchDepth(depth)}
                      className={`
                        relative p-4 rounded-lg cursor-pointer transition-all duration-200
                        bg-white dark:bg-gray-800
                        ${isSelected
                          ? `border-2 ${config.borderColor} ${config.glowColor}`
                          : "border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                        }
                      `}
                    >
                      {/* Recommended Badge */}
                      {depth === "medium" && (
                        <div className="absolute -top-2.5 left-1/2 -translate-x-1/2">
                          <span className="px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide bg-purple-500 text-white rounded">
                            Recommended
                          </span>
                        </div>
                      )}
                      
                      {/* Header */}
                      <div className="flex items-start justify-between mb-3 mt-1">
                        <div className="flex items-center gap-2">
                          <div className={`p-1.5 rounded-md ${isSelected ? config.iconBg : "bg-gray-100 dark:bg-gray-700"}`}>
                            {depth === "simple" && <Zap className={`h-4 w-4 ${isSelected ? "text-white" : "text-gray-500 dark:text-gray-400"}`} />}
                            {depth === "medium" && <Sparkles className={`h-4 w-4 ${isSelected ? "text-white" : "text-gray-500 dark:text-gray-400"}`} />}
                            {depth === "deep" && <Target className={`h-4 w-4 ${isSelected ? "text-white" : "text-gray-500 dark:text-gray-400"}`} />}
                          </div>
                          <div>
                            <h4 className={`font-semibold text-sm ${isSelected ? config.textColor : "text-gray-900 dark:text-white"}`}>
                              {config.name}
                            </h4>
                            <p className="text-[10px] text-gray-500 dark:text-gray-400">
                              {config.subtitle}
                            </p>
                          </div>
                        </div>
                        {isSelected && (
                          <div className={`p-1 rounded-full ${config.iconBg}`}>
                            <Check className="h-3 w-3 text-white" />
                          </div>
                        )}
                      </div>
                      
                      {/* Stats */}
                      <div className="flex items-center gap-3 mb-3 pb-3 border-b border-gray-100 dark:border-gray-700">
                        <div className={`flex items-center gap-1 text-xs ${isSelected ? config.textColor : "text-gray-500 dark:text-gray-400"}`}>
                          <Clock className="h-3 w-3" />
                          <span>{config.time}</span>
                        </div>
                        <div className="w-px h-3 bg-gray-200 dark:bg-gray-700" />
                        <div className={`flex items-center gap-1 text-xs ${isSelected ? config.textColor : "text-gray-500 dark:text-gray-400"}`}>
                          <FileText className="h-3 w-3" />
                          <span>{config.assets} assets</span>
                        </div>
                      </div>
                      
                      {/* Features */}
                      <ul className="space-y-1.5">
                        {config.features.map((feature, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-400">
                            <Check className={`h-3 w-3 mt-0.5 flex-shrink-0 ${isSelected ? config.textColor : "text-gray-400 dark:text-gray-500"}`} />
                            <span>{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {savedResearches.length > 0 && !hasSearched && (
            <div className="mt-4">
              <p className="text-sm text-muted-foreground mb-2">Quick access to saved keywords:</p>
              <div className="flex flex-wrap gap-2">
                {savedResearches.slice(0, 8).map((kw) => (
                  <Badge
                    key={kw.keyword}
                    variant="outline"
                    className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors"
                    onClick={() => handleSuggestionClick(kw.keyword)}
                  >
                    {kw.is_opportunity && <Star className="h-3 w-3 mr-1 fill-amber-500 text-amber-500" />}
                    {kw.keyword}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {isSearching && (
        <Card className={`
          ${researchDepth === "simple" 
            ? "border-blue-200 bg-blue-50 dark:bg-blue-950/20" 
            : researchDepth === "medium"
              ? "border-purple-200 bg-purple-50 dark:bg-purple-950/20"
              : "border-amber-200 bg-amber-50 dark:bg-amber-950/20"
          }
        `}>
          <CardContent className="py-8">
            <div className="flex flex-col items-center text-center">
              <div className="relative">
                <Loader2 className={`h-12 w-12 animate-spin ${
                  researchDepth === "simple" ? "text-blue-500" 
                    : researchDepth === "medium" ? "text-purple-500" 
                    : "text-amber-500"
                }`} />
                {researchDepth === "simple" && <Zap className="h-5 w-5 text-blue-400 absolute -top-1 -right-1 animate-pulse" />}
                {researchDepth === "medium" && <Sparkles className="h-5 w-5 text-purple-400 absolute -top-1 -right-1 animate-pulse" />}
                {researchDepth === "deep" && <Target className="h-5 w-5 text-amber-400 absolute -top-1 -right-1 animate-pulse" />}
              </div>
              <h3 className="mt-4 font-semibold text-lg">
                {researchDepth === "simple" && "Quick Analysis"}
                {researchDepth === "medium" && "Deep Research"}
                {researchDepth === "deep" && "Comprehensive Analysis"}
                {" "}&quot;{searchQuery}&quot;
              </h3>
              <p className="text-muted-foreground mt-2 max-w-md">
                {researchDepth === "simple" 
                  ? "Analyzing search results and calculating scores. This takes about 30-60 seconds..."
                  : researchDepth === "medium"
                    ? "Scraping 50 asset pages, analyzing 10 contributors, building market insights. This may take 3-5 minutes..."
                    : "Full comprehensive analysis: 100 assets, 20 contributors, keyword networks, portfolio analysis. This may take 10-15 minutes..."
                }
              </p>
              {researchDepth !== "simple" && (
                <div className="mt-4 w-full max-w-md">
                  <ProgressIndicator 
                    isActive={true}
                    depth={researchDepth}
                    keyword={searchQuery}
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-950/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <p className="text-red-600 dark:text-red-400">{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {hasSearched && !isSearching && results.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              Results for &quot;{searchQuery}&quot;
            </h2>
            <div className="flex items-center gap-2">
              {results[0]?.source === "live" && (
                <Badge variant="outline" className="text-emerald-600 border-emerald-600">
                  <Zap className="h-3 w-3 mr-1" />
                  Live Data
                </Badge>
              )}
              {results[0]?.source?.startsWith("deep-") && (
                <Badge variant="outline" className={
                  results[0]?.source === "deep-medium" 
                    ? "text-purple-600 border-purple-600" 
                    : "text-amber-600 border-amber-600"
                }>
                  {results[0]?.source === "deep-medium" ? (
                    <><Sparkles className="h-3 w-3 mr-1" /> Deep Research</>
                  ) : (
                    <><Target className="h-3 w-3 mr-1" /> Comprehensive</>
                  )}
                </Badge>
              )}
              <Badge variant="secondary">{results.length} keywords</Badge>
            </div>
          </div>

          <div className="grid gap-4">
            {results.map((result) => renderKeywordCard(result, true, false))}
          </div>
        </div>
      )}

      {!hasSearched && !isSearching && (
        <div className="space-y-4">
          <div className="flex items-center gap-4 border-b">
            <button
              className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === "researched"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setActiveTab("researched")}
            >
              <div className="flex items-center gap-2">
                <Search className="h-4 w-4" />
                Researched Keywords
              </div>
            </button>
            <button
              className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === "saved"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setActiveTab("saved")}
            >
              <div className="flex items-center gap-2">
                <Bookmark className="h-4 w-4" />
                Saved Researches
                {savedResearches.length > 0 && (
                  <Badge variant="secondary" className="ml-1">
                    {savedResearches.length}
                  </Badge>
                )}
              </div>
            </button>
          </div>

          {activeTab === "researched" && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Hash className="h-5 w-5 text-blue-500" />
                <h2 className="text-xl font-semibold">Researched Keywords</h2>
              </div>

              {results.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Search className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Research Yet</h3>
                    <p className="text-muted-foreground max-w-md mx-auto">
                      Search for keywords above to analyze them. Your research results will appear here.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4">
                  {results.map((result) => renderKeywordCard(result, true, false))}
                </div>
              )}
            </div>
          )}

          {activeTab === "saved" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bookmark className="h-5 w-5 text-emerald-500" />
                  <h2 className="text-xl font-semibold">Saved Researches</h2>
                </div>
                {savedResearches.filter(r => r.is_opportunity).length > 0 && (
                  <Badge className="bg-amber-500 text-white">
                    <Star className="h-3 w-3 mr-1 fill-current" />
                    {savedResearches.filter(r => r.is_opportunity).length} Opportunities
                  </Badge>
                )}
              </div>

              {savedResearches.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Bookmark className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Saved Researches</h3>
                    <p className="text-muted-foreground max-w-md mx-auto">
                      When you research a keyword, click the &quot;Save&quot; button to save it here for future reference.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4">
                  {savedResearches.map((result) => renderKeywordCard(result, false, true))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {!hasSearched && savedResearches.length === 0 && results.length === 0 && (
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

      <EnhancedDetailsModal
        isOpen={showDetailsModal}
        onClose={closeDetailsModal}
        keyword={selectedKeyword}
        deepAnalysis={deepAnalysisData}
        isSaved={selectedKeyword ? isResearchSaved(selectedKeyword.keyword) : false}
        isOpportunity={selectedKeyword ? isMarkedAsOpportunity(selectedKeyword.keyword) : false}
        onSave={() => {
          if (selectedKeyword) {
            isResearchSaved(selectedKeyword.keyword)
              ? removeResearch(selectedKeyword.keyword)
              : saveResearch(selectedKeyword, deepAnalysisData);
          }
        }}
        onToggleOpportunity={() => {
          if (selectedKeyword) {
            toggleOpportunity(selectedKeyword.keyword);
          }
        }}
      />

      <Modal
        isOpen={showBriefModal}
        onClose={closeBriefModal}
        title={`Content Brief: ${selectedKeyword?.keyword || ""}`}
      >
        {selectedKeyword && (
          <div className="space-y-6">
            <div className="flex items-center gap-4 p-4 rounded-lg bg-gradient-to-r from-violet-50 to-purple-50 dark:from-violet-950/20 dark:to-purple-950/20">
              <div className={`text-4xl font-bold ${getScoreColor(selectedKeyword.opportunity_score)}`}>
                {selectedKeyword.opportunity_score.toFixed(0)}
              </div>
              <div>
                <div className="font-semibold">Opportunity Score</div>
                <Badge className={getScoreBg(selectedKeyword.opportunity_score) + " text-white"}>
                  {selectedKeyword.urgency.toUpperCase()} URGENCY
                </Badge>
              </div>
            </div>

            <div className="p-4 rounded-lg border-l-4 border-l-blue-500 bg-blue-50 dark:bg-blue-950/20">
              <h4 className="font-semibold flex items-center gap-2 mb-2">
                <CheckCircle className="h-4 w-4 text-blue-500" />
                Recommendation
              </h4>
              <p className="text-sm">
                {selectedKeyword.opportunity_score >= 70 
                  ? "This is a HIGH PRIORITY keyword. Create content immediately to capitalize on the opportunity."
                  : selectedKeyword.opportunity_score >= 50
                    ? "This is a GOOD OPPORTUNITY. Add to your production queue and create quality content."
                    : "This keyword has LIMITED OPPORTUNITY. Consider focusing on higher-scoring alternatives."
                }
              </p>
            </div>

            <div>
              <h4 className="font-semibold flex items-center gap-2 mb-3">
                <Camera className="h-4 w-4" />
                Content Ideas
              </h4>
              <ul className="space-y-2">
                {[
                  `Professional ${selectedKeyword.keyword} photography with clean backgrounds`,
                  `${selectedKeyword.keyword} in modern, minimalist settings`,
                  `Diverse people interacting with ${selectedKeyword.keyword}`,
                  `${selectedKeyword.keyword} lifestyle and workspace shots`,
                  `Abstract or conceptual ${selectedKeyword.keyword} imagery`,
                ].map((idea, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="text-primary font-medium">{i + 1}.</span>
                    <span>{idea}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="font-semibold flex items-center gap-2 mb-3">
                <FileText className="h-4 w-4" />
                Production Tips
              </h4>
              <ul className="space-y-2 text-sm">
                {[
                  "Focus on unique angles and perspectives not commonly seen",
                  "Use authentic, diverse models when applicable",
                  "Ensure high technical quality (lighting, composition, focus)",
                  "Include both horizontal and vertical orientations",
                  "Consider seasonal variations if applicable",
                ].map((tip, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircle className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>

            {selectedKeyword.related_searches && selectedKeyword.related_searches.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Related Keywords to Include</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedKeyword.related_searches.slice(0, 8).map((kw) => (
                    <Badge key={kw} variant="outline">{kw}</Badge>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-4 border-t flex gap-2">
              <Button onClick={copyBrief} className="flex-1 gap-2">
                {copiedBrief ? (
                  <>
                    <Check className="h-4 w-4" />
                    Copied to Clipboard!
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    Copy Full Brief
                  </>
                )}
              </Button>
              <Button
                variant={isResearchSaved(selectedKeyword.keyword) ? "secondary" : "outline"}
                onClick={() => isResearchSaved(selectedKeyword.keyword) 
                  ? removeResearch(selectedKeyword.keyword) 
                  : saveResearch(selectedKeyword, deepAnalysisData)
                }
              >
                {isResearchSaved(selectedKeyword.keyword) ? (
                  <BookmarkCheck className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
