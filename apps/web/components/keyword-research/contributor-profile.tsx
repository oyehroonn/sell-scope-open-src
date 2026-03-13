"use client";

import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  User,
  Camera,
  Palette,
  Video,
  FileText,
  Box,
  Crown,
  TrendingUp,
  Calendar,
  ExternalLink,
} from "lucide-react";

interface ContributorProfileData {
  adobe_id: string;
  name?: string;
  profile_url?: string;
  total_assets: number;
  total_photos?: number;
  total_vectors?: number;
  total_videos?: number;
  total_templates?: number;
  total_3d?: number;
  premium_count?: number;
  premium_ratio: number;
  top_categories?: string[];
  top_keywords?: string[];
  niches?: string[];
  estimated_join_date?: string;
  upload_frequency_monthly?: number;
  competition_level?: string;
}

interface ContributorProfileCardProps {
  contributor: ContributorProfileData;
  rank?: number;
  className?: string;
  compact?: boolean;
}

export function ContributorProfileCard({
  contributor,
  rank,
  className = "",
  compact = false,
}: ContributorProfileCardProps) {
  const getCompetitionColor = (level?: string) => {
    switch (level?.toLowerCase()) {
      case "high":
        return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
      case "medium":
        return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400";
      case "low":
        return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400";
      default:
        return "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400";
    }
  };

  const formatNumber = (n: number) => {
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
    return n.toString();
  };

  const portfolioBreakdown = [
    { label: "Photos", value: contributor.total_photos || 0, icon: Camera, color: "text-blue-500" },
    { label: "Vectors", value: contributor.total_vectors || 0, icon: Palette, color: "text-purple-500" },
    { label: "Videos", value: contributor.total_videos || 0, icon: Video, color: "text-red-500" },
    { label: "Templates", value: contributor.total_templates || 0, icon: FileText, color: "text-green-500" },
    { label: "3D", value: contributor.total_3d || 0, icon: Box, color: "text-amber-500" },
  ].filter((item) => item.value > 0);

  if (compact) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 ${className}`}
      >
        {rank && (
          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 text-xs font-bold">
            {rank}
          </div>
        )}
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700">
          <User className="w-4 h-4 text-gray-500" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate">
            {contributor.name || `Contributor ${contributor.adobe_id}`}
          </p>
          <p className="text-xs text-gray-500">
            {formatNumber(contributor.total_assets)} assets
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-[10px]">
            {(contributor.premium_ratio * 100).toFixed(0)}% Premium
          </Badge>
          {contributor.profile_url && (
            <a
              href={contributor.profile_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              <ExternalLink className="w-3.5 h-3.5 text-gray-400" />
            </a>
          )}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <Card className={className}>
        <CardContent className="p-4">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              {rank && (
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white text-sm font-bold">
                  {rank}
                </div>
              )}
              <div className="flex items-center justify-center w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800">
                <User className="w-6 h-6 text-gray-500" />
              </div>
              <div>
                <h3 className="font-semibold">
                  {contributor.name || `Contributor ${contributor.adobe_id}`}
                </h3>
                <p className="text-sm text-gray-500">
                  ID: {contributor.adobe_id}
                </p>
              </div>
            </div>
            {contributor.profile_url && (
              <a
                href={contributor.profile_url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                <ExternalLink className="w-4 h-4 text-gray-400" />
              </a>
            )}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="p-2 rounded-lg bg-gray-50 dark:bg-gray-800/50 text-center">
              <p className="text-xs text-gray-500">Portfolio</p>
              <p className="font-bold text-lg">
                {formatNumber(contributor.total_assets)}
              </p>
            </div>
            <div className="p-2 rounded-lg bg-purple-50 dark:bg-purple-900/20 text-center">
              <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-0.5">
                <Crown className="w-3 h-3 text-purple-500" />
                Premium
              </div>
              <p className="font-bold text-lg text-purple-600">
                {(contributor.premium_ratio * 100).toFixed(0)}%
              </p>
            </div>
            <div className="p-2 rounded-lg bg-gray-50 dark:bg-gray-800/50 text-center">
              <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-0.5">
                <TrendingUp className="w-3 h-3" />
                Monthly
              </div>
              <p className="font-bold text-lg">
                {contributor.upload_frequency_monthly?.toFixed(1) || "N/A"}
              </p>
            </div>
          </div>

          {/* Portfolio Breakdown */}
          {portfolioBreakdown.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2">Portfolio Breakdown</p>
              <div className="space-y-2">
                {portfolioBreakdown.map((item, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <item.icon className={`w-3.5 h-3.5 ${item.color}`} />
                    <span className="text-xs flex-1">{item.label}</span>
                    <span className="text-xs text-gray-500">
                      {formatNumber(item.value)}
                    </span>
                    <div className="w-16">
                      <Progress
                        value={(item.value / contributor.total_assets) * 100}
                        className="h-1.5"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Niches */}
          {contributor.niches && contributor.niches.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2">Specializations</p>
              <div className="flex flex-wrap gap-1.5">
                {contributor.niches.slice(0, 5).map((niche, i) => (
                  <Badge key={i} variant="secondary" className="text-[10px]">
                    {niche}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Top Keywords */}
          {contributor.top_keywords && contributor.top_keywords.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2">Top Keywords</p>
              <div className="flex flex-wrap gap-1.5">
                {contributor.top_keywords.slice(0, 8).map((kw, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 text-[10px] bg-gray-100 dark:bg-gray-800 rounded"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
            {contributor.competition_level && (
              <Badge className={getCompetitionColor(contributor.competition_level)}>
                {contributor.competition_level} Competition
              </Badge>
            )}
            {contributor.estimated_join_date && (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Calendar className="w-3 h-3" />
                Since {contributor.estimated_join_date.slice(0, 4)}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default ContributorProfileCard;
