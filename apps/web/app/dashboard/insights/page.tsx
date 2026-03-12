"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { BarChart3, Hash, Users, Database, Link2 } from "lucide-react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

interface Summary {
  total_assets: number;
  total_searches: number;
  total_contributors: number;
  total_keywords: number;
  total_similar_links: number;
}

interface TopKeyword {
  term: string;
  asset_count: number;
}

interface TopContributor {
  adobe_id: string;
  name: string | null;
  asset_count: number;
}

export default function InsightsPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [topKeywords, setTopKeywords] = useState<TopKeyword[]>([]);
  const [topContributors, setTopContributors] = useState<TopContributor[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchInsights() {
      setLoading(true);
      try {
        const [sumRes, kwRes, contribRes] = await Promise.all([
          fetch(`${API_BASE}/insights/summary`),
          fetch(`${API_BASE}/insights/top-keywords?limit=20`),
          fetch(`${API_BASE}/insights/top-contributors?limit=20`),
        ]);
        if (sumRes.ok) setSummary(await sumRes.json());
        if (kwRes.ok) setTopKeywords(await kwRes.json());
        if (contribRes.ok) setTopContributors(await contribRes.json());
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    fetchInsights();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Insights</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Insights</h1>
        <p className="text-muted-foreground">
          Aggregated data from your scraped assets, keywords, and contributors
        </p>
      </div>

      {summary && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Assets</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.total_assets.toLocaleString()}</div>
              <Link href="/dashboard/assets" className="text-xs text-primary hover:underline">
                View assets
              </Link>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Searches</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.total_searches.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Contributors</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.total_contributors.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Keywords</CardTitle>
              <Hash className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.total_keywords.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Similar Links</CardTitle>
              <Link2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.total_similar_links.toLocaleString()}</div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Top Keywords</CardTitle>
            <CardDescription>Most used keywords across scraped assets</CardDescription>
          </CardHeader>
          <CardContent>
            {topKeywords.length === 0 ? (
              <p className="text-sm text-muted-foreground">No keyword data yet. Run a scrape with details and import to the API.</p>
            ) : (
              <div className="space-y-2">
                {topKeywords.slice(0, 20).map((kw, i) => (
                  <div key={kw.term} className="flex items-center justify-between">
                    <span className="text-sm font-medium truncate flex-1">{kw.term}</span>
                    <Badge variant="secondary" className="ml-2">{kw.asset_count}</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Top Contributors</CardTitle>
            <CardDescription>Contributors with most scraped assets</CardDescription>
          </CardHeader>
          <CardContent>
            {topContributors.length === 0 ? (
              <p className="text-sm text-muted-foreground">No contributor data yet.</p>
            ) : (
              <div className="space-y-2">
                {topContributors.slice(0, 20).map((c) => (
                  <div key={c.adobe_id} className="flex items-center justify-between">
                    <span className="text-sm font-medium truncate flex-1">{c.name || c.adobe_id}</span>
                    <Badge variant="secondary" className="ml-2">{c.asset_count}</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
