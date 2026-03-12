"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ArrowRight,
  ArrowUp,
  ArrowDown,
  Filter,
  Lightbulb,
  Loader2,
  Search,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

interface KeywordResult {
  term: string;
  opportunityScore: number;
  searchVolume: string;
  competition: string;
  trend: "up" | "down" | "stable";
  change: number;
  category: string;
}

const mockResults: KeywordResult[] = [
  {
    term: "remote work lifestyle",
    opportunityScore: 87,
    searchVolume: "45K",
    competition: "Medium",
    trend: "up",
    change: 12,
    category: "Business",
  },
  {
    term: "ai technology business",
    opportunityScore: 82,
    searchVolume: "38K",
    competition: "High",
    trend: "up",
    change: 8,
    category: "Technology",
  },
  {
    term: "sustainable living eco friendly",
    opportunityScore: 79,
    searchVolume: "52K",
    competition: "Low",
    trend: "up",
    change: 15,
    category: "Lifestyle",
  },
  {
    term: "home office modern design",
    opportunityScore: 76,
    searchVolume: "29K",
    competition: "Medium",
    trend: "down",
    change: -3,
    category: "Interior",
  },
  {
    term: "wellness meditation mindfulness",
    opportunityScore: 74,
    searchVolume: "67K",
    competition: "High",
    trend: "up",
    change: 5,
    category: "Health",
  },
  {
    term: "digital nomad travel",
    opportunityScore: 71,
    searchVolume: "23K",
    competition: "Low",
    trend: "up",
    change: 18,
    category: "Travel",
  },
  {
    term: "plant based food healthy",
    opportunityScore: 68,
    searchVolume: "41K",
    competition: "Medium",
    trend: "stable",
    change: 0,
    category: "Food",
  },
  {
    term: "diverse team collaboration",
    opportunityScore: 65,
    searchVolume: "18K",
    competition: "Low",
    trend: "up",
    change: 22,
    category: "Business",
  },
];

const suggestedKeywords = [
  "remote work",
  "ai technology",
  "sustainable",
  "wellness",
  "home office",
  "digital nomad",
  "plant based",
  "diversity",
];

export default function KeywordsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<KeywordResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setResults(mockResults);
    setHasSearched(true);
    setIsSearching(false);
  };

  const handleSuggestionClick = (keyword: string) => {
    setSearchQuery(keyword);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-500";
    if (score >= 60) return "text-amber-500";
    return "text-red-500";
  };

  const getScoreBadge = (score: number) => {
    if (score >= 80) return "default";
    if (score >= 60) return "secondary";
    return "outline";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Keyword Research</h1>
        <p className="text-muted-foreground">
          Find high-opportunity keywords with demand analysis and opportunity scoring
        </p>
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
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="pl-10"
              />
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

          {/* Suggested Keywords */}
          <div className="mt-4">
            <p className="text-sm text-muted-foreground mb-2">Try these trending keywords:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedKeywords.map((keyword) => (
                <Badge
                  key={keyword}
                  variant="outline"
                  className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors"
                  onClick={() => handleSuggestionClick(keyword)}
                >
                  {keyword}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {hasSearched && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              Results for "{searchQuery}"
            </h2>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="gap-2">
                <Filter className="h-4 w-4" />
                Filters
              </Button>
              <Button variant="outline" size="sm">
                Export
              </Button>
            </div>
          </div>

          <div className="grid gap-4">
            {results.map((result) => (
              <Card key={result.term} className="hover:border-primary/50 transition-colors">
                <CardContent className="pt-6">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-lg">{result.term}</h3>
                        <Badge variant="outline">{result.category}</Badge>
                      </div>
                      <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <TrendingUp className="h-4 w-4" />
                          <span>Volume: {result.searchVolume}</span>
                        </div>
                        <div>Competition: {result.competition}</div>
                        <div className="flex items-center gap-1">
                          {result.trend === "up" ? (
                            <ArrowUp className="h-4 w-4 text-emerald-500" />
                          ) : result.trend === "down" ? (
                            <ArrowDown className="h-4 w-4 text-red-500" />
                          ) : null}
                          <span
                            className={
                              result.trend === "up"
                                ? "text-emerald-500"
                                : result.trend === "down"
                                  ? "text-red-500"
                                  : ""
                            }
                          >
                            {result.change > 0 ? "+" : ""}
                            {result.change}% this month
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-6">
                      <div className="text-center">
                        <div className="text-sm text-muted-foreground mb-1">
                          Opportunity Score
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-20">
                            <Progress value={result.opportunityScore} className="h-2" />
                          </div>
                          <span
                            className={`text-2xl font-bold ${getScoreColor(
                              result.opportunityScore
                            )}`}
                          >
                            {result.opportunityScore}
                          </span>
                        </div>
                      </div>

                      <div className="flex gap-2">
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
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!hasSearched && (
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
