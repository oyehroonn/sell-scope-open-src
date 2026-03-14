"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Save, BookmarkCheck, Star, BarChart3, Users, TrendingUp, Sparkles, Target, Zap, Network } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CompetitorChart } from "./competitor-chart";
import { MarketCharts } from "./market-charts";
import { ContributorProfileCard } from "./contributor-profile";
import { KeywordNetwork } from "./keyword-network";
import { FreshnessChart } from "./freshness-chart";

interface KeywordResult {
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
  scraped_at?: string;
  source?: string;
}

interface DeepAnalysisResult {
  keyword: string;
  depth: string;
  search_results: any;
  assets: any[];
  asset_details: any[];
  contributor_profiles: any[];
  market_analysis: any;
  scoring: any;
  visualizations: any;
  scraped_at?: string;
  source?: string;
  errors?: string[];
}

interface EnhancedDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  keyword: KeywordResult | null;
  deepAnalysis?: DeepAnalysisResult | null;
  isSaved: boolean;
  isOpportunity: boolean;
  onSave: () => void;
  onToggleOpportunity: () => void;
}

type TabType = "overview" | "competitors" | "market" | "trends" | "opportunities";

export function EnhancedDetailsModal({
  isOpen,
  onClose,
  keyword,
  deepAnalysis: initialDeepAnalysis = null,
  isSaved,
  isOpportunity,
  onSave,
  onToggleOpportunity,
}: EnhancedDetailsModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [deepAnalysis, setDeepAnalysis] = useState<DeepAnalysisResult | null>(initialDeepAnalysis);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen && initialDeepAnalysis) {
      setDeepAnalysis(initialDeepAnalysis);
    }
  }, [isOpen, initialDeepAnalysis]);

  const getScoreColor = (score: number) => {
    if (score >= 70) return "text-emerald-500";
    if (score >= 50) return "text-amber-500";
    return "text-red-500";
  };

  const getScoreBg = (score: number) => {
    if (score >= 70) return "bg-emerald-500";
    if (score >= 50) return "bg-amber-500";
    return "bg-red-500";
  };

  if (!isOpen || !keyword) return null;

  const scoring = deepAnalysis?.scoring || {
    demand_score: keyword.demand_score,
    competition_score: keyword.competition_score,
    gap_score: keyword.gap_score,
    freshness_score: keyword.freshness_score,
    opportunity_score: keyword.opportunity_score,
    quality_gap_score: 50,
  };

  const tabs: { id: TabType; label: string; icon: React.ReactNode }[] = [
    { id: "overview", label: "Overview", icon: <Target className="h-4 w-4" /> },
    { id: "competitors", label: "Competitors", icon: <Users className="h-4 w-4" /> },
    { id: "market", label: "Market", icon: <BarChart3 className="h-4 w-4" /> },
    { id: "trends", label: "Trends", icon: <TrendingUp className="h-4 w-4" /> },
    { id: "opportunities", label: "Opportunities", icon: <Sparkles className="h-4 w-4" /> },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative z-50 w-full max-w-5xl max-h-[90vh] overflow-hidden bg-white dark:bg-gray-900 rounded-xl shadow-2xl m-4 flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-white dark:bg-gray-900">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold">{keyword.keyword}</h2>
            {isOpportunity && (
              <Badge className="bg-amber-500 text-white">
                <Star className="h-3 w-3 mr-1 fill-current" />
                Opportunity
              </Badge>
            )}
            {deepAnalysis && (
              <Badge variant="secondary" className="text-purple-600">
                <Zap className="h-3 w-3 mr-1" />
                Deep Analysis
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant={isSaved ? "secondary" : "outline"}
              size="sm"
              onClick={onSave}
            >
              {isSaved ? (
                <>
                  <BookmarkCheck className="h-4 w-4 mr-1 text-emerald-500" />
                  Saved
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-1" />
                  Save
                </>
              )}
            </Button>
            {isSaved && (
              <Button
                variant={isOpportunity ? "default" : "outline"}
                size="sm"
                className={isOpportunity ? "bg-amber-500 hover:bg-amber-600" : ""}
                onClick={onToggleOpportunity}
              >
                <Star className={`h-4 w-4 ${isOpportunity ? "fill-current" : ""}`} />
              </Button>
            )}
            <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 px-4 pt-3 border-b bg-gray-50 dark:bg-gray-800/50 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-t-lg transition-colors
                ${activeTab === tab.id
                  ? "bg-white dark:bg-gray-900 text-primary border-t border-l border-r"
                  : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                }
              `}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {/* Overview Tab */}
              {activeTab === "overview" && (
                <div className="space-y-6">
                  {/* Score Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    <div className="text-center p-4 rounded-lg bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-900/30">
                      <div className={`text-3xl font-bold ${getScoreColor(scoring.opportunity_score)}`}>
                        {scoring.opportunity_score?.toFixed(0) || 0}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Opportunity</div>
                    </div>
                    <div className="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
                      <div className={`text-3xl font-bold ${getScoreColor(scoring.demand_score)}`}>
                        {scoring.demand_score?.toFixed(0) || 0}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Demand</div>
                    </div>
                    <div className="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
                      <div className={`text-3xl font-bold ${getScoreColor(100 - scoring.competition_score)}`}>
                        {scoring.competition_score?.toFixed(0) || 0}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Competition</div>
                    </div>
                    <div className="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
                      <div className="text-3xl font-bold text-blue-500">
                        {scoring.gap_score?.toFixed(0) || 0}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Gap</div>
                    </div>
                    <div className="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
                      <div className="text-3xl font-bold text-cyan-500">
                        {scoring.freshness_score?.toFixed(0) || 0}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Freshness</div>
                    </div>
                  </div>

                  {/* Market Stats */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg border">
                      <div className="flex items-center gap-2 mb-2 text-gray-500">
                        <BarChart3 className="h-4 w-4" />
                        <span className="text-sm">Total Results</span>
                      </div>
                      <div className="text-2xl font-bold">{keyword.nb_results.toLocaleString()}</div>
                    </div>
                    <div className="p-4 rounded-lg border">
                      <div className="flex items-center gap-2 mb-2 text-gray-500">
                        <Users className="h-4 w-4" />
                        <span className="text-sm">Contributors</span>
                      </div>
                      <div className="text-2xl font-bold">{keyword.unique_contributors}</div>
                    </div>
                  </div>

                  {/* Analysis Info */}
                  {deepAnalysis && (
                    <div className="border rounded-lg p-4 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="secondary" className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
                          <Sparkles className="h-3 w-3 mr-1" />
                          Deep Analysis Complete
                        </Badge>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Assets Analyzed</span>
                          <div className="font-semibold">{deepAnalysis.asset_details?.length || deepAnalysis.assets?.length || 0}</div>
                        </div>
                        <div>
                          <span className="text-gray-500">Contributors Profiled</span>
                          <div className="font-semibold">{deepAnalysis.contributor_profiles?.length || 0}</div>
                        </div>
                        <div>
                          <span className="text-gray-500">Analysis Depth</span>
                          <div className="font-semibold capitalize">{deepAnalysis.depth || "medium"}</div>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Market Analysis Summary */}
                  {deepAnalysis?.market_analysis && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="p-3 rounded-lg border bg-gray-50 dark:bg-gray-800">
                        <div className="text-xs text-gray-500 mb-1">Premium Ratio</div>
                        <div className="text-lg font-bold">{((deepAnalysis.market_analysis.premium_ratio || 0) * 100).toFixed(0)}%</div>
                      </div>
                      <div className="p-3 rounded-lg border bg-gray-50 dark:bg-gray-800">
                        <div className="text-xs text-gray-500 mb-1">AI Generated</div>
                        <div className="text-lg font-bold">{((deepAnalysis.market_analysis.ai_generated_ratio || 0) * 100).toFixed(0)}%</div>
                      </div>
                      <div className="p-3 rounded-lg border bg-gray-50 dark:bg-gray-800">
                        <div className="text-xs text-gray-500 mb-1">Editorial</div>
                        <div className="text-lg font-bold">{((deepAnalysis.market_analysis.editorial_ratio || 0) * 100).toFixed(0)}%</div>
                      </div>
                      <div className="p-3 rounded-lg border bg-gray-50 dark:bg-gray-800">
                        <div className="text-xs text-gray-500 mb-1">Top 5 Concentration</div>
                        <div className="text-lg font-bold">{((deepAnalysis.market_analysis.contributor_concentration || 0) * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                  )}

                  {/* Related Keywords */}
                  {keyword.related_searches?.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2">Related Keywords</h4>
                      <div className="flex flex-wrap gap-2">
                        {keyword.related_searches.map((kw) => (
                          <Badge key={kw} variant="secondary">{kw}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Competitors Tab */}
              {activeTab === "competitors" && (
                <div className="space-y-6">
                  {deepAnalysis?.contributor_profiles?.length > 0 ? (
                    <>
                      <CompetitorChart
                        contributors={deepAnalysis.contributor_profiles}
                        keyword={keyword.keyword}
                      />
                      <div className="space-y-3">
                        <h3 className="font-semibold">Top Contributors</h3>
                        <div className="space-y-2">
                          {deepAnalysis.contributor_profiles.slice(0, 5).map((c: any, i: number) => (
                            <ContributorProfileCard
                              key={c.adobe_id}
                              contributor={c}
                              rank={i + 1}
                              compact
                            />
                          ))}
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-12">
                      <Users className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                      <h3 className="font-semibold mb-2">No Competitor Data</h3>
                      <p className="text-gray-500 mb-4">
                        Select "Medium" or "Deep" research depth before analyzing to get contributor profiling data.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Market Tab */}
              {activeTab === "market" && (
                <div className="space-y-6">
                  {deepAnalysis?.market_analysis ? (
                    <MarketCharts 
                      marketAnalysis={deepAnalysis.market_analysis} 
                      visualizations={deepAnalysis.visualizations}
                    />
                  ) : (
                    <div className="text-center py-12">
                      <BarChart3 className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                      <h3 className="font-semibold mb-2">No Market Data</h3>
                      <p className="text-gray-500 mb-4">
                        Select "Medium" or "Deep" research depth before analyzing to get market distribution charts.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Trends Tab */}
              {activeTab === "trends" && (
                <div className="space-y-6">
                  <FreshnessChart
                    assets={deepAnalysis?.asset_details || []}
                    freshnessScore={scoring.freshness_score || 50}
                    trend={keyword.trend as "up" | "down" | "stable"}
                  />
                  {deepAnalysis?.visualizations?.keyword_cloud?.length > 0 ? (
                    <KeywordNetwork
                      keywords={deepAnalysis.visualizations.keyword_cloud}
                      centralKeyword={keyword.keyword}
                    />
                  ) : deepAnalysis?.market_analysis?.keyword_frequency && Object.keys(deepAnalysis.market_analysis.keyword_frequency).length > 0 ? (
                    <KeywordNetwork
                      keywords={Object.entries(deepAnalysis.market_analysis.keyword_frequency).map(([text, value]) => ({
                        text,
                        value: value as number,
                      }))}
                      centralKeyword={keyword.keyword}
                    />
                  ) : (
                    <div className="p-6 border rounded-lg text-center">
                      <Network className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                      <h3 className="font-semibold mb-2">No Keyword Network Data</h3>
                      <p className="text-sm text-gray-500">
                        Select "Medium" or "Deep" research depth to analyze keyword relationships and frequency.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Opportunities Tab */}
              {activeTab === "opportunities" && (
                <div className="space-y-6">
                  <div className="p-4 rounded-lg bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20">
                    <div className="flex items-center gap-4">
                      <div className={`text-5xl font-bold ${getScoreColor(scoring.opportunity_score)}`}>
                        {scoring.opportunity_score?.toFixed(0) || 0}
                      </div>
                      <div>
                        <div className="font-semibold text-lg">Opportunity Score</div>
                        <Badge className={`${getScoreBg(scoring.opportunity_score)} text-white`}>
                          {keyword.urgency?.toUpperCase()} PRIORITY
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg border">
                      <h4 className="font-medium mb-3">Score Factors</h4>
                      <div className="space-y-2">
                        {[
                          { label: "Demand", value: scoring.demand_score || 0, weight: "35%" },
                          { label: "Low Competition", value: 100 - (scoring.competition_score || 0), weight: "25%" },
                          { label: "Market Gap", value: scoring.gap_score || 0, weight: "20%" },
                          { label: "Freshness", value: scoring.freshness_score || 0, weight: "10%" },
                          { label: "Quality Gap", value: scoring.quality_gap_score || 50, weight: "10%" },
                        ].map((item) => (
                          <div key={item.label} className="flex items-center justify-between text-sm">
                            <span>{item.label} ({item.weight})</span>
                            <div className="flex items-center gap-2">
                              <Progress value={item.value} className="w-16 h-1.5" />
                              <span className="w-8 text-right">{item.value.toFixed(0)}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="p-4 rounded-lg border">
                      <h4 className="font-medium mb-3">Recommendation</h4>
                      <div className={`p-3 rounded-lg ${
                        scoring.opportunity_score >= 70 
                          ? "bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500"
                          : scoring.opportunity_score >= 50
                            ? "bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500"
                            : "bg-gray-50 dark:bg-gray-800 border-l-4 border-gray-400"
                      }`}>
                        <p className="text-sm">
                          {scoring.opportunity_score >= 70 ? (
                            "HIGH PRIORITY - Create content immediately!"
                          ) : scoring.opportunity_score >= 50 ? (
                            "GOOD OPPORTUNITY - Add to your production queue."
                          ) : (
                            "LIMITED OPPORTUNITY - Consider alternatives."
                          )}
                        </p>
                      </div>
                    </div>
                  </div>

                  {deepAnalysis?.market_analysis && (
                    <div className="p-4 rounded-lg border">
                      <h4 className="font-medium mb-3">Market Gaps Found</h4>
                      <ul className="space-y-2 text-sm">
                        {deepAnalysis.market_analysis.premium_ratio < 0.3 && (
                          <li className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-green-500" />
                            <span>Low premium content - opportunity for quality submissions</span>
                          </li>
                        )}
                        {deepAnalysis.market_analysis.contributor_concentration > 0.5 && (
                          <li className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-green-500" />
                            <span>Market dominated by few contributors - fresh perspectives welcome</span>
                          </li>
                        )}
                        {deepAnalysis.market_analysis.unique_contributors < 10 && (
                          <li className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-green-500" />
                            <span>Low contributor diversity - room for new entrants</span>
                          </li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="p-3 border-t bg-gray-50 dark:bg-gray-800/50 text-xs text-gray-500 text-center">
          {keyword.scraped_at && (
            <span>Last analyzed: {new Date(keyword.scraped_at).toLocaleString()}</span>
          )}
          {deepAnalysis && (
            <span className="ml-2">• Deep analysis: {deepAnalysis.source || "live"}</span>
          )}
        </div>
      </motion.div>
    </div>
  );
}

export default EnhancedDetailsModal;
