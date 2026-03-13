"use client";

import { useMemo } from "react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DollarSign, FileType, Layers, Percent } from "lucide-react";

interface MarketAnalysis {
  premium_ratio: number;
  editorial_ratio: number;
  ai_generated_ratio: number;
  price_analysis: {
    min?: number;
    max?: number;
    avg?: number;
    median?: number;
    count?: number;
  };
  price_distribution?: Array<{
    range: string;
    count: number;
    percentage?: number;
  }>;
  format_distribution: Record<string, number>;
  dimension_analysis?: {
    avg_width?: number;
    avg_height?: number;
    orientations?: {
      horizontal?: number;
      vertical?: number;
      square?: number;
    };
  };
  contributor_concentration?: number;
  unique_contributors?: number;
  sample_size?: number;
}

interface MarketChartsProps {
  marketAnalysis: MarketAnalysis;
  className?: string;
}

const COLORS = {
  primary: ["#8884d8", "#82ca9d", "#ffc658", "#ff7c43", "#a05195"],
  premium: "#8b5cf6",
  editorial: "#06b6d4",
  aiGenerated: "#f59e0b",
  standard: "#6b7280",
};

export function MarketCharts({ marketAnalysis, className = "" }: MarketChartsProps) {
  const contentTypeData = useMemo(() => {
    const premium = marketAnalysis.premium_ratio || 0;
    const editorial = marketAnalysis.editorial_ratio || 0;
    const ai = marketAnalysis.ai_generated_ratio || 0;
    const standard = Math.max(0, 1 - premium - editorial - ai);

    return [
      { name: "Premium", value: premium * 100, color: COLORS.premium },
      { name: "Editorial", value: editorial * 100, color: COLORS.editorial },
      { name: "AI Generated", value: ai * 100, color: COLORS.aiGenerated },
      { name: "Standard", value: standard * 100, color: COLORS.standard },
    ].filter((d) => d.value > 0);
  }, [marketAnalysis]);

  const formatData = useMemo(() => {
    const formats = marketAnalysis.format_distribution || {};
    return Object.entries(formats)
      .map(([name, value], index) => ({
        name: name === "Unknown" ? "Other" : name,
        value,
        fill: COLORS.primary[index % COLORS.primary.length],
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 6);
  }, [marketAnalysis]);

  const orientationData = useMemo(() => {
    const orientations = marketAnalysis.dimension_analysis?.orientations || {};
    return [
      { name: "Horizontal", value: orientations.horizontal || 0, fill: "#8884d8" },
      { name: "Vertical", value: orientations.vertical || 0, fill: "#82ca9d" },
      { name: "Square", value: orientations.square || 0, fill: "#ffc658" },
    ].filter((d) => d.value > 0);
  }, [marketAnalysis]);

  const priceData = useMemo(() => {
    const price = marketAnalysis.price_analysis || {};
    if (!price.min && !price.max && !price.avg) return null;
    return [
      { name: "Min", value: price.min || 0 },
      { name: "Avg", value: price.avg || 0 },
      { name: "Max", value: price.max || 0 },
    ];
  }, [marketAnalysis]);

  const priceDistributionData = useMemo(() => {
    const dist = marketAnalysis.price_distribution || [];
    if (dist.length === 0) return null;
    return dist.map((d, index) => ({
      ...d,
      fill: COLORS.primary[index % COLORS.primary.length],
    }));
  }, [marketAnalysis]);

  const CustomPieTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-900 px-3 py-2 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium">{payload[0].name}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {payload[0].value.toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  const CustomBarTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-900 px-3 py-2 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium">{payload[0].payload.name}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {payload[0].value} assets
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 gap-4 ${className}`}>
      {/* Content Type Distribution */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Percent className="h-4 w-4" />
            Content Type Mix
          </CardTitle>
        </CardHeader>
        <CardContent>
          {contentTypeData.length > 0 ? (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={contentTypeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={70}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {contentTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomPieTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
              No content type data available
            </div>
          )}
          <div className="flex flex-wrap justify-center gap-3 mt-2">
            {contentTypeData.map((item, i) => (
              <div key={i} className="flex items-center gap-1.5 text-xs">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span>{item.name}</span>
                <span className="text-gray-500">{item.value.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Format Distribution */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <FileType className="h-4 w-4" />
            File Formats
          </CardTitle>
        </CardHeader>
        <CardContent>
          {formatData.length > 0 ? (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={formatData} layout="vertical" margin={{ left: 0, right: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis type="number" tick={{ fontSize: 10 }} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fontSize: 10 }}
                    width={50}
                  />
                  <Tooltip content={<CustomBarTooltip />} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {formatData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
              No format data available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Orientation Distribution */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Layers className="h-4 w-4" />
            Orientations
          </CardTitle>
        </CardHeader>
        <CardContent>
          {orientationData.length > 0 ? (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={orientationData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={70}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {orientationData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomPieTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
              No orientation data available
            </div>
          )}
          <div className="flex flex-wrap justify-center gap-3 mt-2">
            {orientationData.map((item, i) => (
              <div key={i} className="flex items-center gap-1.5 text-xs">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: item.fill }}
                />
                <span>{item.name}</span>
                <span className="text-gray-500">{item.value}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Price Analysis */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <DollarSign className="h-4 w-4" />
            Price Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          {priceDistributionData || priceData ? (
            <div className="space-y-4">
              {priceDistributionData ? (
                <div className="h-36">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={priceDistributionData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis dataKey="range" tick={{ fontSize: 9 }} />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip
                        formatter={(value: number, name: string, props: any) => [
                          `${value} assets${props.payload.percentage ? ` (${props.payload.percentage}%)` : ''}`,
                          "Count"
                        ]}
                        contentStyle={{
                          backgroundColor: "var(--background)",
                          border: "1px solid var(--border)",
                          borderRadius: "8px",
                        }}
                      />
                      <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                        {priceDistributionData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : priceData && (
                <div className="h-32">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={priceData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `$${v}`} />
                      <Tooltip
                        formatter={(value: number) => [`$${value.toFixed(2)}`, "Price"]}
                        contentStyle={{
                          backgroundColor: "var(--background)",
                          border: "1px solid var(--border)",
                          borderRadius: "8px",
                        }}
                      />
                      <Bar dataKey="value" fill="#8884d8" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
              <div className="grid grid-cols-4 gap-2">
                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
                  <p className="text-xs text-gray-500">Min</p>
                  <p className="font-semibold text-sm">${marketAnalysis.price_analysis?.min?.toFixed(0) || "N/A"}</p>
                </div>
                <div className="text-center p-2 bg-purple-50 dark:bg-purple-900/20 rounded">
                  <p className="text-xs text-gray-500">Avg</p>
                  <p className="font-semibold text-sm text-purple-600">${marketAnalysis.price_analysis?.avg?.toFixed(0) || "N/A"}</p>
                </div>
                <div className="text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
                  <p className="text-xs text-gray-500">Median</p>
                  <p className="font-semibold text-sm text-blue-600">${marketAnalysis.price_analysis?.median?.toFixed(0) || "N/A"}</p>
                </div>
                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
                  <p className="text-xs text-gray-500">Max</p>
                  <p className="font-semibold text-sm">${marketAnalysis.price_analysis?.max?.toFixed(0) || "N/A"}</p>
                </div>
              </div>
              {marketAnalysis.price_analysis?.count && (
                <p className="text-xs text-center text-gray-500">
                  Based on {marketAnalysis.price_analysis.count} prices collected
                </p>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-48 text-gray-500 text-sm">
              <DollarSign className="h-8 w-8 mb-2 text-gray-300" />
              <p>No price data available</p>
              <p className="text-xs mt-1">Run Deep analysis to collect pricing</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default MarketCharts;
