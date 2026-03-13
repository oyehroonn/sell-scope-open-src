"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  BarChart3,
  Hash,
  Users,
  Database,
  Link2,
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  Sparkles,
  ArrowRight,
  Library,
  PieChart,
  Zap,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Summary {
  total_assets: number;
  total_searches: number;
  total_contributors: number;
  total_keywords: number;
  total_similar_links: number;
  total_library_assets: number;
  avg_opportunity_score: number;
}

interface TopKeyword {
  term: string;
  asset_count: number;
  opportunity_score?: number;
  trend?: string;
}

interface TopContributor {
  adobe_id: string;
  name: string | null;
  asset_count: number;
}

interface CategoryDistribution {
  name: string;
  count: number;
  percentage: number;
}

interface TrendingKeyword {
  keyword: string;
  demand_score: number;
  opportunity_score: number;
  trend: string;
  asset_count: number;
}

interface OpportunityHighlight {
  keyword: string;
  opportunity_score: number;
  urgency: string;
  recommendation: string;
}

export default function InsightsPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [topKeywords, setTopKeywords] = useState<TopKeyword[]>([]);
  const [topContributors, setTopContributors] = useState<TopContributor[]>([]);
  const [categoryDistribution, setCategoryDistribution] = useState<CategoryDistribution[]>([]);
  const [trendingKeywords, setTrendingKeywords] = useState<TrendingKeyword[]>([]);
  const [opportunityHighlights, setOpportunityHighlights] = useState<OpportunityHighlight[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const [sumRes, kwRes, contribRes, catRes, trendRes, oppRes] = await Promise.all([
        fetch(`${API_BASE}/insights/summary`),
        fetch(`${API_BASE}/insights/top-keywords?limit=15`),
        fetch(`${API_BASE}/insights/top-contributors?limit=10`),
        fetch(`${API_BASE}/insights/category-distribution?limit=10`),
        fetch(`${API_BASE}/insights/trending?limit=8`),
        fetch(`${API_BASE}/insights/opportunity-highlights?limit=5`),
      ]);
      if (sumRes.ok) setSummary(await sumRes.json());
      if (kwRes.ok) setTopKeywords(await kwRes.json());
      if (contribRes.ok) setTopContributors(await contribRes.json());
      if (catRes.ok) setCategoryDistribution(await catRes.json());
      if (trendRes.ok) setTrendingKeywords(await trendRes.json());
      if (oppRes.ok) setOpportunityHighlights(await oppRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "up":
        return <TrendingUp className="h-4 w-4 text-emerald-500" />;
      case "down":
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-400" />;
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case "high":
        return "bg-red-500";
      case "medium":
        return "bg-amber-500";
      default:
        return "bg-gray-500";
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Insights</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-28 rounded-lg" />
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-80 rounded-lg" />
          <Skeleton className="h-80 rounded-lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Insights</h1>
          <p className="text-muted-foreground">
            Analytics and trends from your scraped data
          </p>
        </div>
        <Button onClick={fetchInsights} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0 }}
          >
            <Card className="relative overflow-hidden">
              <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-violet-500/20 to-violet-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Total Assets</CardTitle>
                <Database className="h-4 w-4 text-violet-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.total_assets.toLocaleString()}</div>
                <div className="flex items-center gap-2 mt-1">
                  <Library className="h-3 w-3 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">
                    {summary.total_library_assets} in library
                  </span>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="relative overflow-hidden">
              <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-blue-500/20 to-blue-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Keywords</CardTitle>
                <Hash className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.total_keywords.toLocaleString()}</div>
                <Link href="/dashboard/keywords" className="text-xs text-primary hover:underline">
                  Research keywords →
                </Link>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="relative overflow-hidden">
              <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Contributors</CardTitle>
                <Users className="h-4 w-4 text-emerald-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.total_contributors.toLocaleString()}</div>
                <span className="text-xs text-muted-foreground">Unique creators</span>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="relative overflow-hidden">
              <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-amber-500/20 to-amber-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Avg Opportunity</CardTitle>
                <Target className="h-4 w-4 text-amber-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.avg_opportunity_score.toFixed(1)}</div>
                <Progress value={summary.avg_opportunity_score} className="h-1 mt-2" />
              </CardContent>
            </Card>
          </motion.div>
        </div>
      )}

      {/* Opportunity Highlights */}
      {opportunityHighlights.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-amber-500" />
                Top Opportunities
              </CardTitle>
              <CardDescription>High-potential keywords to focus on</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {opportunityHighlights.map((opp, i) => (
                  <motion.div
                    key={opp.keyword}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 * i }}
                    className="p-4 rounded-lg border bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold">{opp.keyword}</span>
                      <Badge className={`${getUrgencyColor(opp.urgency)} text-white`}>
                        {opp.urgency}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl font-bold">{opp.opportunity_score.toFixed(0)}</span>
                      <span className="text-sm text-muted-foreground">score</span>
                    </div>
                    <p className="text-xs text-muted-foreground">{opp.recommendation}</p>
                  </motion.div>
                ))}
              </div>
              <div className="mt-4 text-center">
                <Link href="/dashboard/opportunities">
                  <Button variant="outline" className="gap-2">
                    View All Opportunities
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Trending Keywords & Category Distribution */}
      <div className="grid gap-6 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-emerald-500" />
                Trending Keywords
              </CardTitle>
              <CardDescription>Keywords with high demand and opportunity</CardDescription>
            </CardHeader>
            <CardContent>
              {trendingKeywords.length === 0 ? (
                <div className="text-center py-8">
                  <Sparkles className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-sm text-muted-foreground">
                    No trending data yet. Scrape more assets to see trends.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {trendingKeywords.map((kw, i) => (
                    <div
                      key={kw.keyword}
                      className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-900"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-lg font-bold text-muted-foreground w-6">
                          {i + 1}
                        </span>
                        <div>
                          <p className="font-medium">{kw.keyword}</p>
                          <p className="text-xs text-muted-foreground">
                            {kw.asset_count} assets
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <p className="font-semibold">{kw.opportunity_score.toFixed(0)}</p>
                          <p className="text-xs text-muted-foreground">score</p>
                        </div>
                        {getTrendIcon(kw.trend)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5 text-blue-500" />
                Category Distribution
              </CardTitle>
              <CardDescription>Asset distribution across categories</CardDescription>
            </CardHeader>
            <CardContent>
              {categoryDistribution.length === 0 ? (
                <div className="text-center py-8">
                  <PieChart className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-sm text-muted-foreground">
                    No category data yet. Scrape assets with details enabled.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {categoryDistribution.map((cat, i) => (
                    <div key={cat.name} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{cat.name}</span>
                        <span className="text-muted-foreground">
                          {cat.count} ({cat.percentage}%)
                        </span>
                      </div>
                      <Progress value={cat.percentage} className="h-2" />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Top Keywords & Contributors */}
      <div className="grid gap-6 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Hash className="h-5 w-5 text-violet-500" />
                Top Keywords
              </CardTitle>
              <CardDescription>Most used keywords across scraped assets</CardDescription>
            </CardHeader>
            <CardContent>
              {topKeywords.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No keyword data yet. Run a scrape with details enabled.
                </p>
              ) : (
                <div className="space-y-2">
                  {topKeywords.slice(0, 15).map((kw) => (
                    <div key={kw.term} className="flex items-center justify-between">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <span className="text-sm font-medium truncate">{kw.term}</span>
                        {kw.trend && getTrendIcon(kw.trend)}
                      </div>
                      <div className="flex items-center gap-2">
                        {kw.opportunity_score && (
                          <Badge variant="outline" className="text-xs">
                            {kw.opportunity_score.toFixed(0)}
                          </Badge>
                        )}
                        <Badge variant="secondary">{kw.asset_count}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-emerald-500" />
                Top Contributors
              </CardTitle>
              <CardDescription>Contributors with most scraped assets</CardDescription>
            </CardHeader>
            <CardContent>
              {topContributors.length === 0 ? (
                <p className="text-sm text-muted-foreground">No contributor data yet.</p>
              ) : (
                <div className="space-y-2">
                  {topContributors.slice(0, 10).map((c, i) => (
                    <div key={c.adobe_id} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-bold text-muted-foreground w-5">
                          {i + 1}
                        </span>
                        <span className="text-sm font-medium truncate">
                          {c.name || `Contributor ${c.adobe_id}`}
                        </span>
                      </div>
                      <Badge variant="secondary">{c.asset_count}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
