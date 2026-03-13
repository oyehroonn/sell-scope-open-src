"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ChevronLeft,
  ChevronRight,
  Crown,
  ExternalLink,
  Filter,
  Image as ImageIcon,
  RefreshCw,
  Search,
  Video,
  Users,
  Clock,
  Database,
  TrendingUp,
  Eye,
  Sparkles,
  LayoutGrid,
  List,
  Camera,
} from "lucide-react";

interface Asset {
  id: number;
  adobe_id: string;
  title: string;
  asset_type: string;
  contributor_id: string;
  contributor_name: string;
  thumbnail_url: string;
  preview_url: string;
  keywords: string[];
  category: string;
  width: number;
  height: number;
  orientation: string;
  is_premium: boolean;
  is_ai_generated?: boolean;
  is_editorial?: boolean;
  similar_count: number;
  scraped_at: string;
}

interface AssetStats {
  total_assets: number;
  by_type: Record<string, number>;
  by_premium: { premium: number; standard: number };
  by_contributor: number;
  latest_scrape: string | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [stats, setStats] = useState<AssetStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [assetType, setAssetType] = useState<string>("all");
  const [isPremium, setIsPremium] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const pageSize = 24;

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        in_library: "true",
      });
      
      if (search) params.append("search", search);
      if (assetType && assetType !== "all") params.append("asset_type", assetType);
      if (isPremium && isPremium !== "all") {
        params.append("is_premium", isPremium === "premium" ? "true" : "false");
      }

      const response = await fetch(`${API_BASE}/assets/?${params}`);
      if (response.ok) {
        const data = await response.json();
        setAssets(data.assets || []);
        setTotal(data.total || 0);
      }
    } catch (error) {
      console.error("Failed to fetch assets:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/assets/stats?in_library=true`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  useEffect(() => {
    fetchAssets();
    fetchStats();
  }, [page]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (page === 1) {
        fetchAssets();
      } else {
        setPage(1);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [search, assetType, isPremium]);

  const totalPages = Math.ceil(total / pageSize);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "video":
        return <Video className="h-4 w-4" />;
      case "vector":
        return <Sparkles className="h-4 w-4" />;
      default:
        return <Camera className="h-4 w-4" />;
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return "Never";
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
    });
  };

  const formatFullDate = (dateStr: string) => {
    if (!dateStr) return "Never";
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Asset Library</h1>
          <p className="text-muted-foreground">
            Your saved assets from Adobe Stock searches
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => { fetchAssets(); fetchStats(); }} variant="outline" className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Link href="/dashboard/scraper">
            <Button className="gap-2 bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-700 hover:to-blue-700">
              <Search className="h-4 w-4" />
              Search & Scrape
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0 }}
        >
          <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-violet-500/20 to-violet-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Database className="h-4 w-4 text-violet-500" />
                Total Assets
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {loading ? <Skeleton className="h-9 w-16" /> : (stats?.total_assets || 0).toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                In your library
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-blue-500/20 to-blue-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Users className="h-4 w-4 text-blue-500" />
                Contributors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {loading ? <Skeleton className="h-9 w-16" /> : (stats?.by_contributor || 0).toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Unique creators
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-amber-500/20 to-amber-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Crown className="h-4 w-4 text-amber-500" />
                Premium Assets
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {loading ? <Skeleton className="h-9 w-16" /> : (stats?.by_premium?.premium || 0).toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {stats && stats.total_assets > 0 
                  ? `${Math.round((stats.by_premium?.premium || 0) / stats.total_assets * 100)}% of total`
                  : "0% of total"
                }
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Clock className="h-4 w-4 text-emerald-500" />
                Last Added
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold">
                {loading ? <Skeleton className="h-7 w-24" /> : formatDate(stats?.latest_scrape || "")}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {stats?.latest_scrape ? formatFullDate(stats.latest_scrape) : "No assets added yet"}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by title or contributor..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={assetType} onValueChange={setAssetType}>
              <SelectTrigger className="w-[160px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="photo">Photo</SelectItem>
                <SelectItem value="vector">Vector</SelectItem>
                <SelectItem value="illustration">Illustration</SelectItem>
                <SelectItem value="video">Video</SelectItem>
              </SelectContent>
            </Select>
            <Select value={isPremium} onValueChange={setIsPremium}>
              <SelectTrigger className="w-[160px]">
                <Crown className="h-4 w-4 mr-2" />
                <SelectValue placeholder="License" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Licenses</SelectItem>
                <SelectItem value="premium">Premium</SelectItem>
                <SelectItem value="standard">Standard</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex items-center gap-1 border rounded-lg p-1">
              <Button
                variant={viewMode === "grid" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("grid")}
              >
                <LayoutGrid className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === "list" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("list")}
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Assets Display */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Assets ({total.toLocaleString()})</CardTitle>
              <CardDescription>
                Page {page} of {totalPages || 1}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className={viewMode === "grid" ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4" : "space-y-4"}>
              {Array.from({ length: 12 }).map((_, i) => (
                <div key={i} className={viewMode === "grid" ? "" : "flex items-center gap-4"}>
                  <Skeleton className={viewMode === "grid" ? "aspect-[4/3] rounded-lg" : "h-16 w-24 rounded"} />
                  {viewMode === "list" && (
                    <div className="space-y-2 flex-1">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : assets.length === 0 ? (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center py-16"
            >
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-violet-500/20 to-blue-500/20 flex items-center justify-center">
                <ImageIcon className="h-10 w-10 text-muted-foreground" />
              </div>
              <h3 className="text-xl font-semibold mb-2">No assets in your library</h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                Search and scrape assets from Adobe Stock to build your library. 
                Click "Add to Library" on any search result to save it here.
              </p>
              <Link href="/dashboard/scraper">
                <Button className="gap-2 bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-700 hover:to-blue-700">
                  <Search className="h-4 w-4" />
                  Start Searching
                </Button>
              </Link>
            </motion.div>
          ) : viewMode === "grid" ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
              <AnimatePresence>
                {assets.map((asset, index) => (
                  <motion.div
                    key={asset.adobe_id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.03 }}
                  >
                    <Link href={`/dashboard/assets/${asset.adobe_id}`}>
                      <div className="group relative aspect-[4/3] rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 cursor-pointer">
                        {asset.thumbnail_url ? (
                          <img
                            src={asset.thumbnail_url}
                            alt={asset.title || "Asset"}
                            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <ImageIcon className="h-8 w-8 text-muted-foreground" />
                          </div>
                        )}
                        
                        {/* Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        
                        {/* Badges */}
                        <div className="absolute top-2 left-2 flex gap-1">
                          {asset.is_premium && (
                            <Badge className="bg-amber-500/90 text-white border-0 text-xs px-1.5 py-0.5">
                              <Crown className="h-2.5 w-2.5" />
                            </Badge>
                          )}
                          {asset.is_ai_generated && (
                            <Badge className="bg-violet-500/90 text-white border-0 text-xs px-1.5 py-0.5">
                              <Sparkles className="h-2.5 w-2.5" />
                            </Badge>
                          )}
                        </div>
                        
                        {/* Info on hover */}
                        <div className="absolute bottom-0 left-0 right-0 p-2 translate-y-full group-hover:translate-y-0 transition-transform duration-300">
                          <p className="text-white text-xs font-medium line-clamp-2">
                            {asset.title || `Asset #${asset.adobe_id}`}
                          </p>
                          {asset.contributor_name && (
                            <p className="text-white/70 text-xs mt-0.5">
                              by {asset.contributor_name}
                            </p>
                          )}
                        </div>
                        
                        {/* View icon */}
                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <div className="bg-white/90 rounded-full p-1.5">
                            <Eye className="h-3 w-3 text-gray-700" />
                          </div>
                        </div>
                      </div>
                    </Link>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          ) : (
            <div className="space-y-2">
              {assets.map((asset, index) => (
                <motion.div
                  key={asset.adobe_id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.02 }}
                >
                  <Link href={`/dashboard/assets/${asset.adobe_id}`}>
                    <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors cursor-pointer group">
                      <div className="relative h-14 w-20 rounded overflow-hidden bg-gray-100 dark:bg-gray-800 shrink-0">
                        {asset.thumbnail_url ? (
                          <img
                            src={asset.thumbnail_url}
                            alt={asset.title || "Asset"}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <ImageIcon className="h-6 w-6 text-muted-foreground" />
                          </div>
                        )}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate group-hover:text-violet-600 transition-colors">
                          {asset.title || `Asset #${asset.adobe_id}`}
                        </p>
                        <div className="flex items-center gap-3 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            {getTypeIcon(asset.asset_type)}
                            {asset.asset_type}
                          </span>
                          {asset.contributor_name && (
                            <span>by {asset.contributor_name}</span>
                          )}
                          {asset.width && asset.height && (
                            <span>{asset.width}×{asset.height}</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {asset.is_premium && (
                          <Badge className="bg-amber-500 hover:bg-amber-600">
                            <Crown className="h-3 w-3 mr-1" />
                            Premium
                          </Badge>
                        )}
                        <span className="text-xs text-muted-foreground">
                          {formatDate(asset.scraped_at)}
                        </span>
                        <Eye className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-6 border-t">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of{" "}
                {total.toLocaleString()} assets
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page >= totalPages}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
