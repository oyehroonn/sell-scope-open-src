"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ArrowRight,
  ArrowUp,
  ArrowDown,
  BarChart3,
  Clock,
  Eye,
  Lightbulb,
  Search,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";
import Link from "next/link";

const topOpportunities = [
  { keyword: "remote work lifestyle", score: 87, trend: "up", change: 12 },
  { keyword: "ai technology business", score: 82, trend: "up", change: 8 },
  { keyword: "sustainable living", score: 79, trend: "up", change: 15 },
  { keyword: "home office setup", score: 76, trend: "down", change: -3 },
  { keyword: "wellness meditation", score: 74, trend: "up", change: 5 },
];

const recentAlerts = [
  { type: "opportunity", message: "New high-demand niche detected: 'AI productivity'", time: "5m ago" },
  { type: "ranking", message: "Your asset 'Modern Office' moved to position #3", time: "1h ago" },
  { type: "seasonal", message: "Valentine's Day content deadline in 14 days", time: "2h ago" },
  { type: "competitor", message: "Tracked portfolio uploaded 12 new assets", time: "4h ago" },
];

const quickStats = [
  { label: "Keywords Tracked", value: "2,847", change: "+124 this week", icon: Search },
  { label: "Opportunity Score Avg", value: "68", change: "+5 points", icon: Target },
  { label: "Portfolios Monitored", value: "23", change: "+3 new", icon: Eye },
  { label: "Briefs Generated", value: "156", change: "12 today", icon: Lightbulb },
];

const seasonalCountdown = [
  { event: "Valentine's Day", daysUntil: 45, uploadDeadline: 14, urgency: "medium" },
  { event: "Easter", daysUntil: 82, uploadDeadline: 30, urgency: "low" },
  { event: "Summer Season", daysUntil: 120, uploadDeadline: 60, urgency: "low" },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Your stock contributor intelligence at a glance
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/keywords">
            <Button variant="outline" className="gap-2">
              <Search className="h-4 w-4" />
              Research
            </Button>
          </Link>
          <Link href="/dashboard/briefs">
            <Button className="gap-2">
              <Zap className="h-4 w-4" />
              Generate Brief
            </Button>
          </Link>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {quickStats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.label}</CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">{stat.change}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Top Opportunities */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-primary" />
                  Top Opportunities
                </CardTitle>
                <CardDescription>
                  Highest-scoring keywords right now
                </CardDescription>
              </div>
              <Link href="/dashboard/opportunities">
                <Button variant="ghost" size="sm" className="gap-1">
                  View All
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topOpportunities.map((opp, index) => (
                <div
                  key={opp.keyword}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-sm font-medium">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium">{opp.keyword}</p>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        {opp.trend === "up" ? (
                          <ArrowUp className="h-3 w-3 text-emerald-500" />
                        ) : (
                          <ArrowDown className="h-3 w-3 text-red-500" />
                        )}
                        <span
                          className={
                            opp.trend === "up"
                              ? "text-emerald-500"
                              : "text-red-500"
                          }
                        >
                          {opp.change > 0 ? "+" : ""}
                          {opp.change}%
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-24">
                      <Progress value={opp.score} className="h-2" />
                    </div>
                    <Badge
                      variant={
                        opp.score >= 80
                          ? "default"
                          : opp.score >= 60
                            ? "secondary"
                            : "outline"
                      }
                    >
                      {opp.score}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-primary" />
                  Live Alerts
                </CardTitle>
                <CardDescription>
                  Real-time market intelligence
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" className="gap-1">
                Configure
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentAlerts.map((alert, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div
                    className={`h-2 w-2 mt-2 rounded-full ${
                      alert.type === "opportunity"
                        ? "bg-emerald-500"
                        : alert.type === "ranking"
                          ? "bg-blue-500"
                          : alert.type === "seasonal"
                            ? "bg-amber-500"
                            : "bg-purple-500"
                    }`}
                  />
                  <div className="flex-1">
                    <p className="text-sm">{alert.message}</p>
                    <p className="text-xs text-muted-foreground">{alert.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Seasonal Countdown */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            Seasonal Content Calendar
          </CardTitle>
          <CardDescription>
            Upcoming events and recommended upload deadlines
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {seasonalCountdown.map((event) => (
              <div
                key={event.event}
                className="p-4 rounded-lg border bg-card"
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold">{event.event}</h4>
                  <Badge
                    variant={
                      event.urgency === "high"
                        ? "destructive"
                        : event.urgency === "medium"
                          ? "default"
                          : "secondary"
                    }
                  >
                    {event.urgency}
                  </Badge>
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Event in</span>
                    <span className="font-medium">{event.daysUntil} days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Upload by</span>
                    <span className="font-medium text-primary">
                      {event.uploadDeadline} days
                    </span>
                  </div>
                </div>
                <Progress
                  value={100 - (event.uploadDeadline / event.daysUntil) * 100}
                  className="mt-3 h-1"
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="hover:border-primary/50 transition-colors cursor-pointer">
          <Link href="/dashboard/keywords">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Search className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">Research Keywords</h3>
                  <p className="text-sm text-muted-foreground">
                    Find high-opportunity niches
                  </p>
                </div>
              </div>
            </CardContent>
          </Link>
        </Card>

        <Card className="hover:border-primary/50 transition-colors cursor-pointer">
          <Link href="/dashboard/briefs">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Lightbulb className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">Generate AI Brief</h3>
                  <p className="text-sm text-muted-foreground">
                    Get shot ideas & keywords
                  </p>
                </div>
              </div>
            </CardContent>
          </Link>
        </Card>

        <Card className="hover:border-primary/50 transition-colors cursor-pointer">
          <Link href="/dashboard/portfolio">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <BarChart3 className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">Portfolio Coach</h3>
                  <p className="text-sm text-muted-foreground">
                    Optimize your portfolio
                  </p>
                </div>
              </div>
            </CardContent>
          </Link>
        </Card>
      </div>
    </div>
  );
}
