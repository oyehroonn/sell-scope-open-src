"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ArrowRight,
  ArrowUp,
  Clock,
  Filter,
  Flame,
  Lightbulb,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";

const opportunities = [
  {
    keyword: "remote work lifestyle",
    score: 87,
    urgency: "high",
    demand: 85,
    competition: 35,
    freshness: 72,
    seasonal: 45,
    styleGap: 68,
    production: 30,
    risk: 15,
    recommendation: "HIGH PRIORITY: Create content immediately. High buyer demand detected. Low competition - easy to rank.",
    category: "Business",
  },
  {
    keyword: "ai technology future",
    score: 82,
    urgency: "high",
    demand: 90,
    competition: 55,
    freshness: 65,
    seasonal: 30,
    styleGap: 75,
    production: 40,
    risk: 20,
    recommendation: "HIGH PRIORITY: Create content immediately. High buyer demand detected. Visual gaps detected - opportunity for unique styles.",
    category: "Technology",
  },
  {
    keyword: "sustainable eco friendly",
    score: 79,
    urgency: "medium",
    demand: 75,
    competition: 40,
    freshness: 80,
    seasonal: 35,
    styleGap: 60,
    production: 35,
    risk: 10,
    recommendation: "GOOD OPPORTUNITY: Add to production queue. Low competition - easy to rank.",
    category: "Lifestyle",
  },
  {
    keyword: "wellness meditation",
    score: 74,
    urgency: "medium",
    demand: 80,
    competition: 50,
    freshness: 55,
    seasonal: 40,
    styleGap: 55,
    production: 25,
    risk: 15,
    recommendation: "GOOD OPPORTUNITY: Add to production queue. High buyer demand detected.",
    category: "Health",
  },
  {
    keyword: "home office minimalist",
    score: 71,
    urgency: "medium",
    demand: 70,
    competition: 45,
    freshness: 60,
    seasonal: 50,
    styleGap: 65,
    production: 30,
    risk: 10,
    recommendation: "GOOD OPPORTUNITY: Add to production queue. Visual gaps detected.",
    category: "Interior",
  },
];

const heatmapData = [
  { name: "Business", score: 78, assets: 125000, competition: 0.65 },
  { name: "Technology", score: 82, assets: 98000, competition: 0.72 },
  { name: "Lifestyle", score: 71, assets: 156000, competition: 0.58 },
  { name: "Health", score: 75, assets: 89000, competition: 0.55 },
  { name: "Food", score: 68, assets: 134000, competition: 0.62 },
  { name: "Nature", score: 64, assets: 178000, competition: 0.48 },
  { name: "Travel", score: 72, assets: 112000, competition: 0.68 },
  { name: "Education", score: 77, assets: 67000, competition: 0.45 },
];

export default function OpportunitiesPage() {
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
          <Button variant="outline" className="gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </Button>
          <Button className="gap-2">
            <Zap className="h-4 w-4" />
            Refresh Scores
          </Button>
        </div>
      </div>

      <Tabs defaultValue="list" className="space-y-6">
        <TabsList>
          <TabsTrigger value="list" className="gap-2">
            <Target className="h-4 w-4" />
            Top Opportunities
          </TabsTrigger>
          <TabsTrigger value="heatmap" className="gap-2">
            <Flame className="h-4 w-4" />
            Category Heatmap
          </TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="space-y-4">
          {opportunities.map((opp, index) => (
            <Card key={opp.keyword}>
              <CardContent className="pt-6">
                <div className="flex flex-col xl:flex-row gap-6">
                  {/* Main Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">{opp.keyword}</h3>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{opp.category}</Badge>
                          <Badge
                            variant={
                              opp.urgency === "high"
                                ? "default"
                                : opp.urgency === "medium"
                                  ? "secondary"
                                  : "outline"
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

                    {/* Score Breakdown */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                      <div>
                        <div className="text-xs text-muted-foreground mb-1">Demand</div>
                        <div className="flex items-center gap-2">
                          <Progress value={opp.demand} className="h-1.5 flex-1" />
                          <span className="text-xs font-medium">{opp.demand}</span>
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground mb-1">Competition</div>
                        <div className="flex items-center gap-2">
                          <Progress value={opp.competition} className="h-1.5 flex-1" />
                          <span className="text-xs font-medium">{opp.competition}</span>
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground mb-1">Style Gap</div>
                        <div className="flex items-center gap-2">
                          <Progress value={opp.styleGap} className="h-1.5 flex-1" />
                          <span className="text-xs font-medium">{opp.styleGap}</span>
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground mb-1">Seasonal</div>
                        <div className="flex items-center gap-2">
                          <Progress value={opp.seasonal} className="h-1.5 flex-1" />
                          <span className="text-xs font-medium">{opp.seasonal}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Score & Actions */}
                  <div className="flex flex-row xl:flex-col items-center justify-between xl:justify-center gap-4 xl:w-48">
                    <div className="text-center">
                      <div className="text-sm text-muted-foreground mb-1">
                        Opportunity Score
                      </div>
                      <div
                        className={`text-4xl font-bold ${
                          opp.score >= 80
                            ? "text-emerald-500"
                            : opp.score >= 60
                              ? "text-amber-500"
                              : "text-red-500"
                        }`}
                      >
                        {opp.score}
                      </div>
                    </div>
                    <div className="flex xl:flex-col gap-2">
                      <Button variant="outline" size="sm" className="gap-1">
                        <TrendingUp className="h-4 w-4" />
                        Analyze
                      </Button>
                      <Button size="sm" className="gap-1">
                        <Lightbulb className="h-4 w-4" />
                        Generate Brief
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
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
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {heatmapData.map((cat) => (
                  <div
                    key={cat.name}
                    className={`p-4 rounded-lg border-2 transition-colors cursor-pointer hover:border-primary ${
                      cat.score >= 75
                        ? "bg-emerald-500/10 border-emerald-500/30"
                        : cat.score >= 65
                          ? "bg-amber-500/10 border-amber-500/30"
                          : "bg-red-500/10 border-red-500/30"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">{cat.name}</h4>
                      <span
                        className={`text-lg font-bold ${
                          cat.score >= 75
                            ? "text-emerald-500"
                            : cat.score >= 65
                              ? "text-amber-500"
                              : "text-red-500"
                        }`}
                      >
                        {cat.score}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground space-y-1">
                      <div className="flex justify-between">
                        <span>Assets</span>
                        <span>{(cat.assets / 1000).toFixed(0)}K</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Competition</span>
                        <span>{(cat.competition * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
