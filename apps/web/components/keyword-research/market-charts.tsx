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
  Treemap,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DollarSign, FileType, Layers, Percent, Grid3X3, Target, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface CategoryHeatmapItem {
  name: string;
  slug: string;
  count: number;
  percentage: number;
  demand_score: number;
  competition_score: number;
  opportunity_score: number;
  competition_level: string;
  unique_contributors?: number;
  premium_ratio?: number;
  top_keywords?: string[];
  keyword_count?: number;
  estimated_results?: number;
}

interface NicheAnalysisItem {
  name: string;
  score: number;
  demand_score: number;
  competition_score: number;
  opportunity_score: number;
  keywords: string[];
  keyword_count: number;
  asset_count?: number;
  unique_contributors?: number;
  premium_ratio?: number;
  avg_price?: number;
  category: string;
  description: string;
}

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
  top_categories?: CategoryHeatmapItem[];
  detected_niches?: NicheAnalysisItem[];
}

interface Visualizations {
  category_heatmap?: CategoryHeatmapItem[];
  niche_analysis?: NicheAnalysisItem[];
}

interface MarketChartsProps {
  marketAnalysis: MarketAnalysis;
  visualizations?: Visualizations;
  className?: string;
}

const COLORS = {
  primary: ["#8884d8", "#82ca9d", "#ffc658", "#ff7c43", "#a05195"],
  premium: "#8b5cf6",
  editorial: "#06b6d4",
  aiGenerated: "#f59e0b",
  standard: "#6b7280",
};

export function MarketCharts({ marketAnalysis, visualizations, className = "" }: MarketChartsProps) {
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

      {/* Category Heatmap */}
      <CategoryHeatmap 
        categories={visualizations?.category_heatmap || marketAnalysis.top_categories || []} 
      />

      {/* Niche Analysis */}
      <NicheAnalysis 
        niches={visualizations?.niche_analysis || marketAnalysis.detected_niches || []} 
      />
    </div>
  );
}

function getOpportunityColor(score: number): string {
  if (score >= 70) return "bg-emerald-500";
  if (score >= 50) return "bg-amber-500";
  return "bg-red-500";
}

function getOpportunityTextColor(score: number): string {
  if (score >= 70) return "text-emerald-500";
  if (score >= 50) return "text-amber-500";
  return "text-red-500";
}

function getTrendIcon(trend: string) {
  if (trend === "up") return <TrendingUp className="h-3 w-3 text-emerald-500" />;
  if (trend === "down") return <TrendingDown className="h-3 w-3 text-red-500" />;
  return <Minus className="h-3 w-3 text-gray-400" />;
}

function CategoryHeatmap({ categories }: { categories: CategoryHeatmapItem[] }) {
  if (!categories || categories.length === 0) {
    return (
      <Card className="md:col-span-2">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Grid3X3 className="h-4 w-4" />
            Category Heatmap
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-48 text-gray-500 text-sm">
            <Grid3X3 className="h-8 w-8 mb-2 text-gray-300" />
            <p>No category data available</p>
            <p className="text-xs mt-1">Run Deep analysis to analyze categories</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="md:col-span-2">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Grid3X3 className="h-4 w-4" />
          Category Heatmap
          <Badge variant="secondary" className="ml-auto text-xs">
            {categories.length} categories
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {categories.slice(0, 12).map((cat, index) => (
            <div
              key={cat.slug || index}
              className="p-3 rounded-lg border bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-medium text-sm truncate flex-1" title={cat.name}>
                  {cat.name}
                </h4>
                <Badge 
                  variant="outline" 
                  className={`text-xs ml-1 ${getOpportunityTextColor(cat.opportunity_score)}`}
                >
                  {cat.opportunity_score?.toFixed(0) || 0}
                </Badge>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">Demand</span>
                  <span className={getOpportunityTextColor(cat.demand_score)}>
                    {cat.demand_score?.toFixed(0) || 0}
                  </span>
                </div>
                <Progress 
                  value={cat.demand_score || 0} 
                  className="h-1.5"
                />
                
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">Competition</span>
                  <span className={cat.competition_score > 60 ? "text-red-500" : cat.competition_score > 30 ? "text-amber-500" : "text-emerald-500"}>
                    {cat.competition_score?.toFixed(0) || 0}
                  </span>
                </div>
                <Progress 
                  value={cat.competition_score || 0} 
                  className="h-1.5"
                />
              </div>
              
              <div className="mt-2 pt-2 border-t flex items-center justify-between text-xs text-gray-500">
                <span>{cat.count || 0} assets</span>
                <span>{cat.keyword_count || 0} keywords</span>
              </div>
              
              {cat.top_keywords && cat.top_keywords.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {cat.top_keywords.slice(0, 3).map((kw, i) => (
                    <Badge key={i} variant="secondary" className="text-[10px] px-1.5 py-0">
                      {kw}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function NicheAnalysis({ niches }: { niches: NicheAnalysisItem[] }) {
  if (!niches || niches.length === 0) {
    return (
      <Card className="md:col-span-2">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Target className="h-4 w-4" />
            Niche Opportunities
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-48 text-gray-500 text-sm">
            <Target className="h-8 w-8 mb-2 text-gray-300" />
            <p>No niche data available</p>
            <p className="text-xs mt-1">Run Deep analysis to detect niches</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="md:col-span-2">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Target className="h-4 w-4" />
          Niche Opportunities
          <Badge variant="secondary" className="ml-auto text-xs">
            {niches.length} niches detected
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {niches.slice(0, 8).map((niche, index) => (
            <div
              key={niche.name || index}
              className="p-3 rounded-lg border hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-sm">{niche.name}</h4>
                    {niche.category && (
                      <Badge variant="outline" className="text-[10px]">
                        {niche.category}
                      </Badge>
                    )}
                  </div>
                  {niche.description && (
                    <p className="text-xs text-gray-500 mt-0.5">{niche.description}</p>
                  )}
                </div>
                <div className={`text-2xl font-bold ${getOpportunityTextColor(niche.opportunity_score)}`}>
                  {niche.opportunity_score?.toFixed(0) || 0}
                </div>
              </div>
              
              <div className="grid grid-cols-4 gap-3 mb-2">
                <div className="text-center">
                  <p className="text-xs text-gray-500">Demand</p>
                  <p className={`font-semibold text-sm ${getOpportunityTextColor(niche.demand_score)}`}>
                    {niche.demand_score?.toFixed(0) || 0}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-500">Competition</p>
                  <p className={`font-semibold text-sm ${niche.competition_score > 60 ? "text-red-500" : niche.competition_score > 30 ? "text-amber-500" : "text-emerald-500"}`}>
                    {niche.competition_score?.toFixed(0) || 0}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-500">Assets</p>
                  <p className="font-semibold text-sm">{niche.asset_count || 0}</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-500">Keywords</p>
                  <p className="font-semibold text-sm">{niche.keyword_count || 0}</p>
                </div>
              </div>
              
              {niche.keywords && niche.keywords.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t">
                  <span className="text-xs text-gray-500 mr-1">Top keywords:</span>
                  {niche.keywords.slice(0, 5).map((kw, i) => (
                    <Badge key={i} variant="secondary" className="text-[10px] px-1.5 py-0">
                      {kw}
                    </Badge>
                  ))}
                </div>
              )}
              
              {niche.avg_price && (
                <div className="mt-2 text-xs text-gray-500">
                  Avg. price: <span className="font-medium">${niche.avg_price.toFixed(2)}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default MarketCharts;
