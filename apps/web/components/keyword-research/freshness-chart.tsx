"use client";

import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface AssetDate {
  upload_date?: string;
  scraped_at?: string;
}

interface FreshnessChartProps {
  assets?: AssetDate[];
  freshnessScore?: number;
  trend?: "up" | "down" | "stable";
  className?: string;
}

export function FreshnessChart({
  assets = [],
  freshnessScore = 50,
  trend = "stable",
  className = "",
}: FreshnessChartProps) {
  const chartData = useMemo(() => {
    const now = new Date();
    const months: { [key: string]: number } = {};

    for (let i = 11; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const key = date.toISOString().slice(0, 7);
      const label = date.toLocaleDateString("en-US", { month: "short" });
      months[key] = 0;
    }

    assets.forEach((asset) => {
      const dateStr = asset.upload_date || asset.scraped_at;
      if (!dateStr) return;

      try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return;

        const key = date.toISOString().slice(0, 7);
        if (key in months) {
          months[key]++;
        }
      } catch {
        // Skip invalid dates
      }
    });

    return Object.entries(months).map(([month, count]) => {
      const date = new Date(month + "-01");
      return {
        month: date.toLocaleDateString("en-US", { month: "short" }),
        fullMonth: date.toLocaleDateString("en-US", { month: "long", year: "numeric" }),
        uploads: count,
      };
    });
  }, [assets]);

  const stats = useMemo(() => {
    const total = chartData.reduce((sum, d) => sum + d.uploads, 0);
    const recentMonths = chartData.slice(-3);
    const recentTotal = recentMonths.reduce((sum, d) => sum + d.uploads, 0);
    const oldMonths = chartData.slice(0, 3);
    const oldTotal = oldMonths.reduce((sum, d) => sum + d.uploads, 0);
    
    const avgMonthly = total / chartData.length;
    const peakMonth = chartData.reduce(
      (max, d) => (d.uploads > max.uploads ? d : max),
      chartData[0] || { month: "N/A", uploads: 0 }
    );

    return {
      total,
      recentTotal,
      oldTotal,
      avgMonthly: avgMonthly.toFixed(1),
      peakMonth,
      recentTrend: recentTotal > oldTotal ? "up" : recentTotal < oldTotal ? "down" : "stable",
    };
  }, [chartData]);

  const getTrendIcon = (t: string) => {
    switch (t) {
      case "up":
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case "down":
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTrendColor = (t: string) => {
    switch (t) {
      case "up":
        return "text-green-500";
      case "down":
        return "text-red-500";
      default:
        return "text-gray-500";
    }
  };

  const getFreshnessLabel = (score: number) => {
    if (score >= 70) return { label: "Very Fresh", color: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" };
    if (score >= 50) return { label: "Moderately Fresh", color: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" };
    if (score >= 30) return { label: "Aging Content", color: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400" };
    return { label: "Stale Market", color: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" };
  };

  const freshnessInfo = getFreshnessLabel(freshnessScore);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-900 px-3 py-2 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium">{payload[0].payload.fullMonth}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {payload[0].value} uploads
          </p>
        </div>
      );
    }
    return null;
  };

  const hasData = stats.total > 0 || assets.length > 0;

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <Clock className="h-4 w-4" />
            Market Freshness
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge className={freshnessInfo.color}>
              {freshnessInfo.label}
            </Badge>
            <div className="flex items-center gap-1">
              {getTrendIcon(trend)}
              <span className={`text-sm font-medium ${getTrendColor(trend)}`}>
                {trend === "up" ? "Growing" : trend === "down" ? "Declining" : "Stable"}
              </span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Freshness Score */}
        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-500">Freshness Score</span>
            <span className="text-2xl font-bold">{freshnessScore.toFixed(0)}</span>
          </div>
          <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${freshnessScore}%`,
                background: `linear-gradient(90deg, 
                  ${freshnessScore >= 70 ? "#22c55e" : freshnessScore >= 50 ? "#eab308" : freshnessScore >= 30 ? "#f97316" : "#ef4444"} 0%, 
                  ${freshnessScore >= 70 ? "#16a34a" : freshnessScore >= 50 ? "#ca8a04" : freshnessScore >= 30 ? "#ea580c" : "#dc2626"} 100%)`,
              }}
            />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg text-center">
            <p className="text-xs text-gray-500 mb-1">Avg Monthly</p>
            <p className="font-semibold">{stats.avgMonthly}</p>
          </div>
          <div className="p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg text-center">
            <p className="text-xs text-gray-500 mb-1">Last 3 Months</p>
            <p className="font-semibold">{stats.recentTotal}</p>
          </div>
          <div className="p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg text-center">
            <p className="text-xs text-gray-500 mb-1">Peak</p>
            <p className="font-semibold">{stats.peakMonth.month}</p>
          </div>
        </div>

        {/* Area Chart */}
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="uploadGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 10 }}
                axisLine={{ stroke: "#e5e7eb" }}
              />
              <YAxis
                tick={{ fontSize: 10 }}
                axisLine={{ stroke: "#e5e7eb" }}
                allowDecimals={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine
                y={parseFloat(stats.avgMonthly)}
                stroke="#94a3b8"
                strokeDasharray="3 3"
                label={{
                  value: "Avg",
                  position: "right",
                  style: { fontSize: 10, fill: "#94a3b8" },
                }}
              />
              <Area
                type="monotone"
                dataKey="uploads"
                stroke="#8b5cf6"
                strokeWidth={2}
                fill="url(#uploadGradient)"
                animationDuration={1000}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Insight */}
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500">
            {!hasData ? (
              <>
                <span className="font-medium text-gray-500">No upload date data available.</span>{" "}
                Run a deep analysis to collect upload dates from asset details.
              </>
            ) : stats.recentTrend === "up" ? (
              <>
                <span className="font-medium text-green-600">Active market.</span>{" "}
                Recent uploads ({stats.recentTotal}) exceed historical average.
                This indicates growing interest in this niche.
              </>
            ) : stats.recentTrend === "down" ? (
              <>
                <span className="font-medium text-orange-600">Declining activity.</span>{" "}
                Recent uploads ({stats.recentTotal}) are below average.
                Consider this an opportunity or a sign of market saturation.
              </>
            ) : (
              <>
                <span className="font-medium text-gray-600">Stable market.</span>{" "}
                Upload activity is consistent. Established niche with steady demand.
              </>
            )}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

export default FreshnessChart;
