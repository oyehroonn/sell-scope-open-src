"use client";

import { useMemo } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, TrendingUp, Crown } from "lucide-react";

interface ContributorData {
  name: string;
  adobe_id?: string;
  total_assets: number;
  premium_ratio: number;
  niches?: string[];
  competition_level?: string;
}

interface CompetitorChartProps {
  contributors: ContributorData[];
  keyword?: string;
  className?: string;
}

const COLORS = [
  "#8884d8",
  "#82ca9d",
  "#ffc658",
  "#ff7c43",
  "#a05195",
  "#d45087",
  "#f95d6a",
  "#ff7c43",
  "#2f4b7c",
  "#665191",
];

export function CompetitorChart({
  contributors,
  keyword,
  className = "",
}: CompetitorChartProps) {
  const chartData = useMemo(() => {
    if (!contributors || contributors.length === 0) return [];

    const maxAssets = Math.max(...contributors.map((c) => c.total_assets || 0));
    
    return contributors.map((c, index) => ({
      name: c.name || `Contributor ${index + 1}`,
      adobe_id: c.adobe_id,
      portfolioSize: c.total_assets || 0,
      premiumRatio: (c.premium_ratio || 0) * 100,
      marketShare: maxAssets > 0 ? ((c.total_assets || 0) / maxAssets) * 100 : 0,
      niches: c.niches || [],
      competitionLevel: c.competition_level,
      color: COLORS[index % COLORS.length],
    }));
  }, [contributors]);

  const totalAssets = useMemo(
    () => contributors.reduce((sum, c) => sum + (c.total_assets || 0), 0),
    [contributors]
  );

  const avgPremiumRatio = useMemo(() => {
    if (contributors.length === 0) return 0;
    return (
      contributors.reduce((sum, c) => sum + (c.premium_ratio || 0), 0) /
      contributors.length
    );
  }, [contributors]);

  const topContributor = useMemo(() => {
    if (contributors.length === 0) return null;
    return contributors.reduce((max, c) =>
      (c.total_assets || 0) > (max.total_assets || 0) ? c : max
    );
  }, [contributors]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-900 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="font-semibold text-sm mb-1">{data.name}</p>
          <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
            <p>Portfolio: {data.portfolioSize.toLocaleString()} assets</p>
            <p>Premium: {data.premiumRatio.toFixed(1)}%</p>
            <p>Market Share: {data.marketShare.toFixed(1)}%</p>
            {data.niches.length > 0 && (
              <p>Niches: {data.niches.slice(0, 3).join(", ")}</p>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  if (!contributors || contributors.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4" />
            Competitor Landscape
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-gray-500">
            No competitor data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4" />
            Competitor Landscape
            {keyword && (
              <Badge variant="secondary" className="ml-2">
                {keyword}
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>{contributors.length} contributors</span>
            <span>{totalAssets.toLocaleString()} total assets</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Stats Summary */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
              <Crown className="h-3 w-3" />
              Top Contributor
            </div>
            <p className="font-semibold text-sm truncate">
              {topContributor?.name || "N/A"}
            </p>
            <p className="text-xs text-gray-500">
              {topContributor?.total_assets?.toLocaleString() || 0} assets
            </p>
          </div>
          <div className="p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
              <TrendingUp className="h-3 w-3" />
              Avg Premium
            </div>
            <p className="font-semibold text-sm">
              {(avgPremiumRatio * 100).toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500">across all</p>
          </div>
          <div className="p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
              <Users className="h-3 w-3" />
              Competition
            </div>
            <p className="font-semibold text-sm">
              {contributors.length < 5
                ? "Low"
                : contributors.length < 15
                  ? "Medium"
                  : "High"}
            </p>
            <p className="text-xs text-gray-500">{contributors.length} active</p>
          </div>
        </div>

        {/* Bubble Chart */}
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart
              margin={{ top: 10, right: 10, bottom: 20, left: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis
                type="number"
                dataKey="portfolioSize"
                name="Portfolio Size"
                tick={{ fontSize: 10 }}
                tickFormatter={(value) =>
                  value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value
                }
                label={{
                  value: "Portfolio Size",
                  position: "bottom",
                  offset: 0,
                  style: { fontSize: 10, fill: "#6b7280" },
                }}
              />
              <YAxis
                type="number"
                dataKey="premiumRatio"
                name="Premium %"
                tick={{ fontSize: 10 }}
                tickFormatter={(value) => `${value.toFixed(0)}%`}
                label={{
                  value: "Premium %",
                  angle: -90,
                  position: "insideLeft",
                  style: { fontSize: 10, fill: "#6b7280" },
                }}
                domain={[0, 100]}
              />
              <ZAxis
                type="number"
                dataKey="marketShare"
                range={[50, 400]}
                name="Market Share"
              />
              <Tooltip content={<CustomTooltip />} />
              <Scatter name="Contributors" data={chartData}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.color}
                    fillOpacity={0.7}
                    stroke={entry.color}
                    strokeWidth={2}
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 mb-2">Top Contributors</p>
          <div className="flex flex-wrap gap-2">
            {chartData.slice(0, 5).map((c, i) => (
              <div
                key={i}
                className="flex items-center gap-1.5 text-xs px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded"
              >
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: c.color }}
                />
                <span className="truncate max-w-[100px]">{c.name}</span>
              </div>
            ))}
            {chartData.length > 5 && (
              <span className="text-xs text-gray-500 px-2 py-1">
                +{chartData.length - 5} more
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default CompetitorChart;
