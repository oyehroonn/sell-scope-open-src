"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X, Clock, Zap, Sparkles, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface DepthFeatures {
  name: string;
  estimated_time: string;
  max_assets: number;
  features: string[];
  not_included: string[];
}

interface DepthSelectorProps {
  selectedDepth: "simple" | "medium" | "deep";
  onDepthChange: (depth: "simple" | "medium" | "deep") => void;
  onStartAnalysis: () => void;
  isAnalyzing?: boolean;
  className?: string;
}

const depthConfig: Record<string, DepthFeatures> = {
  simple: {
    name: "Simple Research",
    estimated_time: "30-60 seconds",
    max_assets: 20,
    features: [
      "Search results analysis",
      "Basic demand & competition scores",
      "Related keywords",
      "Category detection",
    ],
    not_included: [
      "Asset detail pages",
      "Contributor profiling",
      "Similar asset analysis",
      "Price analysis",
      "Upload date analysis",
      "Advanced visualizations",
    ],
  },
  medium: {
    name: "Deep Research",
    estimated_time: "3-5 minutes",
    max_assets: 50,
    features: [
      "Everything in Simple Research",
      "Top 50 asset detail pages",
      "Top 10 contributor profiles",
      "Similar asset network",
      "Price distribution analysis",
      "Upload date freshness",
      "Premium/editorial ratio",
      "Format distribution",
      "Competitor landscape chart",
      "Market distribution charts",
    ],
    not_included: [
      "Full contributor portfolios",
      "Extended similar network",
    ],
  },
  deep: {
    name: "Comprehensive Research",
    estimated_time: "10-15 minutes",
    max_assets: 100,
    features: [
      "Everything in Deep Research",
      "Top 100 asset detail pages",
      "Top 20 contributor profiles",
      "Extended similar asset network",
      "Full contributor portfolio analysis",
      "Historical trend estimation",
      "Keyword network graph",
      "Quality gap analysis",
    ],
    not_included: [],
  },
};

export function DepthSelector({
  selectedDepth,
  onDepthChange,
  onStartAnalysis,
  isAnalyzing = false,
  className = "",
}: DepthSelectorProps) {
  const [showComparison, setShowComparison] = useState(false);

  const getDepthIcon = (depth: string) => {
    switch (depth) {
      case "simple":
        return <Zap className="h-4 w-4" />;
      case "medium":
        return <Sparkles className="h-4 w-4" />;
      case "deep":
        return <Sparkles className="h-5 w-5" />;
      default:
        return <Zap className="h-4 w-4" />;
    }
  };

  const getDepthColor = (depth: string) => {
    switch (depth) {
      case "simple":
        return "bg-blue-500/10 border-blue-500/30 text-blue-500";
      case "medium":
        return "bg-purple-500/10 border-purple-500/30 text-purple-500";
      case "deep":
        return "bg-amber-500/10 border-amber-500/30 text-amber-500";
      default:
        return "bg-gray-500/10 border-gray-500/30 text-gray-500";
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Depth Selection Buttons */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
          Analysis Depth:
        </span>
        <div className="flex items-center gap-2">
          {(["simple", "medium", "deep"] as const).map((depth) => (
            <TooltipProvider key={depth}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => onDepthChange(depth)}
                    disabled={isAnalyzing}
                    className={`
                      flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium
                      transition-all duration-200
                      ${
                        selectedDepth === depth
                          ? getDepthColor(depth)
                          : "bg-gray-100 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
                      }
                      ${isAnalyzing ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
                    `}
                  >
                    {getDepthIcon(depth)}
                    <span className="capitalize">{depth}</span>
                    {depth === "medium" && (
                      <Badge variant="secondary" className="ml-1 text-[10px] py-0">
                        Recommended
                      </Badge>
                    )}
                  </button>
                </TooltipTrigger>
                <TooltipContent>
                  <div className="text-sm">
                    <p className="font-semibold">{depthConfig[depth].name}</p>
                    <p className="text-gray-500">
                      ~{depthConfig[depth].estimated_time}
                    </p>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ))}
        </div>
        <button
          onClick={() => setShowComparison(!showComparison)}
          className="ml-2 p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500"
        >
          <Info className="h-4 w-4" />
        </button>
      </div>

      {/* Comparison Panel */}
      <AnimatePresence>
        {showComparison && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700">
              {(["simple", "medium", "deep"] as const).map((depth) => (
                <div
                  key={depth}
                  className={`
                    relative p-4 rounded-lg border-2 transition-all
                    ${
                      selectedDepth === depth
                        ? `${getDepthColor(depth)} shadow-lg`
                        : "bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700"
                    }
                  `}
                >
                  {depth === "medium" && (
                    <div className="absolute -top-2 left-1/2 -translate-x-1/2">
                      <Badge className="bg-purple-500 text-white text-[10px]">
                        RECOMMENDED
                      </Badge>
                    </div>
                  )}

                  <div className="flex items-center gap-2 mb-3">
                    {getDepthIcon(depth)}
                    <h4 className="font-semibold">{depthConfig[depth].name}</h4>
                  </div>

                  <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-3">
                    <Clock className="h-3.5 w-3.5" />
                    <span>{depthConfig[depth].estimated_time}</span>
                  </div>

                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    <span className="font-medium">Up to {depthConfig[depth].max_assets} assets</span>
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Includes:
                    </p>
                    <ul className="space-y-1">
                      {depthConfig[depth].features.slice(0, 6).map((feature, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs">
                          <Check className="h-3.5 w-3.5 text-green-500 flex-shrink-0 mt-0.5" />
                          <span>{feature}</span>
                        </li>
                      ))}
                      {depthConfig[depth].features.length > 6 && (
                        <li className="text-xs text-gray-500 pl-5">
                          +{depthConfig[depth].features.length - 6} more features
                        </li>
                      )}
                    </ul>
                  </div>

                  {depthConfig[depth].not_included.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 space-y-2">
                      <p className="text-xs font-medium text-gray-400 uppercase">
                        Not included:
                      </p>
                      <ul className="space-y-1">
                        {depthConfig[depth].not_included.slice(0, 3).map((feature, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs text-gray-400">
                            <X className="h-3.5 w-3.5 text-gray-300 flex-shrink-0 mt-0.5" />
                            <span>{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <Button
                    variant={selectedDepth === depth ? "default" : "outline"}
                    size="sm"
                    className="w-full mt-4"
                    onClick={() => onDepthChange(depth)}
                    disabled={isAnalyzing}
                  >
                    {selectedDepth === depth ? "Selected" : "Select"}
                  </Button>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Selected Depth Summary */}
      {!showComparison && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${getDepthColor(selectedDepth)}`}>
              {getDepthIcon(selectedDepth)}
            </div>
            <div>
              <p className="font-medium text-sm">
                {depthConfig[selectedDepth].name}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {depthConfig[selectedDepth].estimated_time} • Up to{" "}
                {depthConfig[selectedDepth].max_assets} assets
              </p>
            </div>
          </div>
          <Button
            onClick={onStartAnalysis}
            disabled={isAnalyzing}
            className="gap-2"
          >
            {isAnalyzing ? (
              <>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                >
                  <Sparkles className="h-4 w-4" />
                </motion.div>
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Start Analysis
              </>
            )}
          </Button>
        </motion.div>
      )}
    </div>
  );
}

export default DepthSelector;
