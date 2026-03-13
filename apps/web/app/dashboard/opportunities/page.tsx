"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ArrowRight,
  ArrowUp,
  ArrowDown,
  Minus,
  Clock,
  Filter,
  Flame,
  Lightbulb,
  Target,
  TrendingUp,
  Zap,
  RefreshCw,
  Search,
  BarChart3,
  Users,
  Star,
  Trash2,
} from "lucide-react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const SAVED_RESEARCHES_KEY = "sellscope_saved_researches";

interface MarkedOpportunity {
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
  saved_at: string;
  is_opportunity: boolean;
}

interface OpportunityScore {
  keyword: string;
  overall_score: number;
  demand_score: number;
  competition_score: number;
  gap_score: number;
  freshness_score: number;
  trend: string;
  urgency: string;
  recommendation: string;
  nb_results: number;
  unique_contributors: number;
  related_searches: string[];
  categories: { name: string }[];
}

interface NicheScore {
  name: string;
  slug: string;
  total_assets: number;
  total_keywords: number;
  avg_opportunity_score: number;
  avg_demand_score: number;
  avg_competition_score: number;
  top_keywords: string[];
  trend: string;
}

interface HeatmapItem {
  name: string;
  slug: string;
  score: number;
  assets: number;
  competition: number;
}

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<OpportunityScore[]>([]);
  const [niches, setNiches] = useState<NicheScore[]>([]);
  const [heatmapData, setHeatmapData] = useState<HeatmapItem[]>([]);
  const [markedOpportunities, setMarkedOpportunities] = useState<MarkedOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadMarkedOpportunities = () => {
    try {
      const saved = localStorage.getItem(SAVED_RESEARCHES_KEY);
      if (saved) {
        const allSaved = JSON.parse(saved) as MarkedOpportunity[];
        const marked = allSaved.filter(r => r.is_opportunity);
        setMarkedOpportunities(marked);
      }
    } catch (e) {
      console.error("Failed to load marked opportunities:", e);
    }
  };

  const removeFromOpportunities = (keyword: string) => {
    try {
      const saved = localStorage.getItem(SAVED_RESEARCHES_KEY);
      if (saved) {
        const allSaved = JSON.parse(saved) as MarkedOpportunity[];
        const updated = allSaved.map(r => 
          r.keyword.toLowerCase() === keyword.toLowerCase()
            ? { ...r, is_opportunity: false }
            : r
        );
        localStorage.setItem(SAVED_RESEARCHES_KEY, JSON.stringify(updated));
        setMarkedOpportunities(updated.filter(r => r.is_opportunity));
      }
    } catch (e) {
      console.error("Failed to remove from opportunities:", e);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [oppRes, nicheRes, heatmapRes] = await Promise.all([
        fetch(`${API_BASE}/opportunities/top?limit=20`),
        fetch(`${API_BASE}/opportunities/niches?limit=20`),
        fetch(`${API_BASE}/opportunities/heatmap`),
      ]);

      if (oppRes.ok) {
        const data = await oppRes.json();
        setOpportunities(data);
      }
      if (nicheRes.ok) {
        const data = await nicheRes.json();
        setNiches(data);
      }
      if (heatmapRes.ok) {
        const data = await heatmapRes.json();
        setHeatmapData(data.heatmap || []);
      }
    } catch (e) {
      console.error("Failed to fetch opportunities:", e);
    } finally {
      setLoading(false);
    }
  };

  const refreshScores = async () => {
    setRefreshing(true);
    await fetchData();
    loadMarkedOpportunities();
    setRefreshing(false);
  };

  useEffect(() => {
    fetchData();
    loadMarkedOpportunities();
    
    const handleStorageChange = () => {
      loadMarkedOpportunities();
    };
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

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

  const getScoreColor = (score: number) => {
    if (score >= 70) return "text-emerald-500";
    if (score >= 50) return "text-amber-500";
    return "text-red-500";
  };

  const getScoreBg = (score: number) => {
    if (score >= 70) return "bg-emerald-500/10 border-emerald-500/30";
    if (score >= 50) return "bg-amber-500/10 border-amber-500/30";
    return "bg-red-500/10 border-red-500/30";
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Opportunities</h1>
            <p className="text-muted-foreground">Loading opportunity data...</p>
          </div>
        </div>
        <div className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-40 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Opportunities</h1>
          <p className="text-muted-foreground">
            Top-scoring niches and keywords ranked by opportunity potential
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/keywords">
            <Button variant="outline" className="gap-2">
              <Search className="h-4 w-4" />
              Research Keywords
            </Button>
          </Link>
          <Button onClick={refreshScores} disabled={refreshing} className="gap-2">
            {refreshing ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4" />
            )}
            Refresh Scores
          </Button>
        </div>
      </div>

      <Tabs defaultValue="marked" className="space-y-6">
        <TabsList>
          <TabsTrigger value="marked" className="gap-2">
            <Star className="h-4 w-4" />
            Marked Opportunities
            {markedOpportunities.length > 0 && (
              <Badge variant="secondary" className="ml-1">
                {markedOpportunities.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="list" className="gap-2">
            <Target className="h-4 w-4" />
            Top Opportunities
          </TabsTrigger>
          <TabsTrigger value="heatmap" className="gap-2">
            <Flame className="h-4 w-4" />
            Category Heatmap
          </TabsTrigger>
          <TabsTrigger value="niches" className="gap-2">
            <BarChart3 className="h-4 w-4" />
            Niches
          </TabsTrigger>
        </TabsList>

        <TabsContent value="marked" className="space-y-4">
          {markedOpportunities.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Star className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Marked Opportunities</h3>
                <p className="text-muted-foreground max-w-md mx-auto mb-4">
                  When you research keywords, click the star icon to mark them as opportunities. 
                  They will appear here for quick access.
                </p>
                <Link href="/dashboard/keywords">
                  <Button className="gap-2">
                    <Search className="h-4 w-4" />
                    Start Keyword Research
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <AnimatePresence>
              {markedOpportunities.map((opp, index) => (
                <motion.div
                  key={opp.keyword}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="hover:border-primary/50 transition-colors border-amber-500/30 bg-amber-500/5">
                    <CardContent className="pt-6">
                      <div className="flex flex-col xl:flex-row gap-6">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-500/20 text-amber-500">
                              <Star className="h-5 w-5 fill-current" />
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="font-semibold text-lg">{opp.keyword}</h3>
                                {getTrendIcon(opp.trend)}
                              </div>
                              <div className="flex items-center gap-2 mt-1">
                                {opp.categories && opp.categories.length > 0 && (
                                  <Badge variant="outline">
                                    {opp.categories[0]?.name || "General"}
                                  </Badge>
                                )}
                                <Badge
                                  variant={
                                    opp.urgency === "high"
                                      ? "default"
                                      : opp.urgency === "medium"
                                        ? "secondary"
                                        : "outline"
                                  }
                                  className={
                                    opp.urgency === "high"
                                      ? "bg-red-500"
                                      : opp.urgency === "medium"
                                        ? "bg-amber-500"
                                        : ""
                                  }
                                >
                                  <Clock className="h-3 w-3 mr-1" />
                                  {opp.urgency} urgency
                                </Badge>
                                <span className="text-xs text-muted-foreground">
                                  Saved {new Date(opp.saved_at).toLocaleDateString()}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-4">
                            <div className="flex items-center gap-1">
                              <BarChart3 className="h-4 w-4" />
                              <span>{formatNumber(opp.nb_results)} results</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Users className="h-4 w-4" />
                              <span>{opp.unique_contributors} contributors</span>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Demand</div>
                              <div className="flex items-center gap-2">
                                <Progress value={opp.demand_score} className="h-1.5 flex-1" />
                                <span className="text-xs font-medium">{opp.demand_score.toFixed(0)}</span>
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Competition</div>
                              <div className="flex items-center gap-2">
                                <Progress value={opp.competition_score} className="h-1.5 flex-1" />
                                <span className="text-xs font-medium">{opp.competition_score.toFixed(0)}</span>
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Gap</div>
                              <div className="flex items-center gap-2">
                                <Progress value={opp.gap_score} className="h-1.5 flex-1" />
                                <span className="text-xs font-medium">{opp.gap_score.toFixed(0)}</span>
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Freshness</div>
                              <div className="flex items-center gap-2">
                                <Progress value={opp.freshness_score} className="h-1.5 flex-1" />
                                <span className="text-xs font-medium">{opp.freshness_score.toFixed(0)}</span>
                              </div>
                            </div>
                          </div>

                          {opp.related_searches && opp.related_searches.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-1">
                              <span className="text-xs text-muted-foreground mr-1">Related:</span>
                              {opp.related_searches.slice(0, 4).map((related) => (
                                <Badge key={related} variant="secondary" className="text-xs">
                                  {related}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>

                        <div className="flex flex-row xl:flex-col items-center justify-between xl:justify-center gap-4 xl:w-48">
                          <div className="text-center">
                            <div className="text-sm text-muted-foreground mb-1">
                              Opportunity Score
                            </div>
                            <div className={`text-4xl font-bold ${getScoreColor(opp.opportunity_score)}`}>
                              {opp.opportunity_score.toFixed(0)}
                            </div>
                          </div>
                          <div className="flex xl:flex-col gap-2">
                            <Link href={`/dashboard/keywords?q=${encodeURIComponent(opp.keyword)}`}>
                              <Button variant="outline" size="sm" className="gap-1">
                                <TrendingUp className="h-4 w-4" />
                                Analyze
                              </Button>
                            </Link>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="gap-1 text-red-500 hover:text-red-600 hover:bg-red-50"
                              onClick={() => removeFromOpportunities(opp.keyword)}
                            >
                              <Trash2 className="h-4 w-4" />
                              Remove
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </TabsContent>

        <TabsContent value="list" className="space-y-4">
          {opportunities.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Target className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Opportunities Yet</h3>
                <p className="text-muted-foreground max-w-md mx-auto mb-4">
                  Scrape assets and analyze keywords to discover high-opportunity niches.
                </p>
                <Link href="/dashboard/keywords">
                  <Button className="gap-2">
                    <Search className="h-4 w-4" />
                    Start Keyword Research
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <AnimatePresence>
              {opportunities.map((opp, index) => (
                <motion.div
                  key={opp.keyword}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="hover:border-primary/50 transition-colors">
                    <CardContent className="pt-6">
                      <div className="flex flex-col xl:flex-row gap-6">
                        {/* Main Info */}
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary font-bold">
                              {index + 1}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="font-semibold text-lg">{opp.keyword}</h3>
                                {getTrendIcon(opp.trend)}
                              </div>
                              <div className="flex items-center gap-2 mt-1">
                                {opp.categories && opp.categories.length > 0 && (
                                  <Badge variant="outline">
                                    {opp.categories[0]?.name || "General"}
                                  </Badge>
                                )}
                                <Badge
                                  variant={
                                    opp.urgency === "high"
                                      ? "default"
                                      : opp.urgency === "medium"
                                        ? "secondary"
                                        : "outline"
                                  }
                                  className={
                                    opp.urgency === "high"
                                      ? "bg-red-500"
                                      : opp.urgency === "medium"
                                        ? "bg-amber-500"
                                        : ""
                                  }
                                >
                                  <Clock className="h-3 w-3 mr-1" />
                                  {opp.urgency} urgency
                                </Badge>
                              </div>
                            </div>
                          </div>

                          <p className="text-sm text-muted-foreground mb-4">
                            {opp.recommendation}
                          </p>

                          {/* Stats */}
                          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-4">
                            <div className="flex items-center gap-1">
                              <BarChart3 className="h-4 w-4" />
                              <span>{formatNumber(opp.nb_results)} results</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Users className="h-4 w-4" />
                              <span>{opp.unique_contributors} contributors</span>
                            </div>
                          </div>

                          {/* Score Breakdown */}
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Demand</div>
                              <div className="flex items-center gap-2">
                                <Progress value={opp.demand_score} className="h-1.5 flex-1" />
                                <span className="text-xs font-medium">{opp.demand_score.toFixed(0)}</span>
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Competition</div>
                              <div className="flex items-center gap-2">
                                <Progress value={opp.competition_score} className="h-1.5 flex-1" />
                                <span className="text-xs font-medium">{opp.competition_score.toFixed(0)}</span>
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Gap</div>
                              <div className="flex items-center gap-2">
                                <Progress value={opp.gap_score} className="h-1.5 flex-1" />
                                <span className="text-xs font-medium">{opp.gap_score.toFixed(0)}</span>
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Freshness</div>
                              <div className="flex items-center gap-2">
                                <Progress value={opp.freshness_score} className="h-1.5 flex-1" />
                                <span className="text-xs font-medium">{opp.freshness_score.toFixed(0)}</span>
                              </div>
                            </div>
                          </div>

                          {/* Related searches */}
                          {opp.related_searches && opp.related_searches.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-1">
                              <span className="text-xs text-muted-foreground mr-1">Related:</span>
                              {opp.related_searches.slice(0, 4).map((related) => (
                                <Badge key={related} variant="secondary" className="text-xs">
                                  {related}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Score & Actions */}
                        <div className="flex flex-row xl:flex-col items-center justify-between xl:justify-center gap-4 xl:w-48">
                          <div className="text-center">
                            <div className="text-sm text-muted-foreground mb-1">
                              Opportunity Score
                            </div>
                            <div className={`text-4xl font-bold ${getScoreColor(opp.overall_score)}`}>
                              {opp.overall_score.toFixed(0)}
                            </div>
                          </div>
                          <div className="flex xl:flex-col gap-2">
                            <Link href={`/dashboard/keywords?q=${encodeURIComponent(opp.keyword)}`}>
                              <Button variant="outline" size="sm" className="gap-1">
                                <TrendingUp className="h-4 w-4" />
                                Analyze
                              </Button>
                            </Link>
                            <Button size="sm" className="gap-1">
                              <Lightbulb className="h-4 w-4" />
                              Generate Brief
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </TabsContent>

        <TabsContent value="heatmap">
          <Card>
            <CardHeader>
              <CardTitle>Category Opportunity Heatmap</CardTitle>
              <CardDescription>
                Visual overview of opportunities across all categories
              </CardDescription>
            </CardHeader>
            <CardContent>
              {heatmapData.length === 0 ? (
                <div className="text-center py-12">
                  <Flame className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    No category data yet. Scrape assets with details to see the heatmap.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {heatmapData.map((cat, index) => (
                    <motion.div
                      key={cat.slug}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.05 }}
                      className={`p-4 rounded-lg border-2 transition-colors cursor-pointer hover:border-primary ${getScoreBg(cat.score)}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold">{cat.name}</h4>
                        <span className={`text-lg font-bold ${getScoreColor(cat.score)}`}>
                          {cat.score.toFixed(0)}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground space-y-1">
                        <div className="flex justify-between">
                          <span>Assets</span>
                          <span>{formatNumber(cat.assets)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Competition</span>
                          <span>{cat.competition.toFixed(0)}%</span>
                        </div>
                      </div>
                      <Progress value={cat.score} className="h-1 mt-2" />
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="niches">
          <div className="space-y-4">
            {niches.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Niche Data Yet</h3>
                  <p className="text-muted-foreground">
                    Analyze keywords to discover trending niches.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {niches.map((niche, index) => (
                  <motion.div
                    key={niche.slug}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card className="h-full hover:border-primary/50 transition-colors">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">{niche.name}</CardTitle>
                          <div className="flex items-center gap-1">
                            {getTrendIcon(niche.trend)}
                            <span className={`text-xl font-bold ${getScoreColor(niche.avg_opportunity_score)}`}>
                              {niche.avg_opportunity_score.toFixed(0)}
                            </span>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Assets</span>
                            <span className="font-medium">{formatNumber(niche.total_assets)}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Keywords</span>
                            <span className="font-medium">{niche.total_keywords}</span>
                          </div>
                          <div className="space-y-1">
                            <div className="flex justify-between text-xs">
                              <span className="text-muted-foreground">Demand</span>
                              <span>{niche.avg_demand_score.toFixed(0)}</span>
                            </div>
                            <Progress value={niche.avg_demand_score} className="h-1" />
                          </div>
                          <div className="space-y-1">
                            <div className="flex justify-between text-xs">
                              <span className="text-muted-foreground">Competition</span>
                              <span>{niche.avg_competition_score.toFixed(0)}</span>
                            </div>
                            <Progress value={niche.avg_competition_score} className="h-1" />
                          </div>
                          
                          {niche.top_keywords && niche.top_keywords.length > 0 && (
                            <div className="pt-2">
                              <p className="text-xs text-muted-foreground mb-1">Top keywords:</p>
                              <div className="flex flex-wrap gap-1">
                                {niche.top_keywords.slice(0, 3).map((kw) => (
                                  <Badge key={kw} variant="secondary" className="text-xs">
                                    {kw}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
