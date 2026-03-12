"use client";

import { useState, useEffect } from "react";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
} from "lucide-react";
import Image from "next/image";

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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [stats, setStats] = useState<AssetStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [assetType, setAssetType] = useState<string>("all");
  const [isPremium, setIsPremium] = useState<string>("all");
  const pageSize = 50;

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
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
      const response = await fetch(`${API_BASE}/assets/stats`);
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
      default:
        return <ImageIcon className="h-4 w-4" />;
    }
  };

  const formatDate = (dateStr: string) => {
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
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Scraped Assets</h1>
          <p className="text-muted-foreground">
            Browse and analyze assets scraped from Adobe Stock
          </p>
        </div>
        <Button onClick={() => fetchAssets()} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Assets</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_assets.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Contributors</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_contributor.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Premium Assets</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_premium.premium.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Last Scrape</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm font-medium">
                {stats.latest_scrape ? formatDate(stats.latest_scrape) : "Never"}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

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
          </div>
        </CardContent>
      </Card>

      {/* Assets Table */}
      <Card>
        <CardHeader>
          <CardTitle>Assets ({total.toLocaleString()})</CardTitle>
          <CardDescription>
            Page {page} of {totalPages || 1}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-16 w-24 rounded" />
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : assets.length === 0 ? (
            <div className="text-center py-12">
              <ImageIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold">No assets found</h3>
              <p className="text-muted-foreground">
                Run the scraper to import assets from Adobe Stock
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[80px]">Preview</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Contributor</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>License</TableHead>
                  <TableHead>Scraped</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {assets.map((asset) => (
                  <TableRow key={asset.id}>
                    <TableCell>
                      {asset.thumbnail_url ? (
                        <img
                          src={asset.thumbnail_url}
                          alt={asset.title}
                          className="h-12 w-16 object-cover rounded"
                        />
                      ) : (
                        <div className="h-12 w-16 bg-muted rounded flex items-center justify-center">
                          <ImageIcon className="h-6 w-6 text-muted-foreground" />
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="max-w-[300px]">
                        <p className="font-medium truncate">{asset.title || "Untitled"}</p>
                        <p className="text-xs text-muted-foreground">ID: {asset.adobe_id}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="gap-1">
                        {getTypeIcon(asset.asset_type)}
                        {asset.asset_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{asset.contributor_name || "-"}</span>
                    </TableCell>
                    <TableCell>
                      {asset.width && asset.height ? (
                        <span className="text-sm text-muted-foreground">
                          {asset.width} × {asset.height}
                        </span>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                    <TableCell>
                      {asset.is_premium ? (
                        <Badge className="bg-amber-500 hover:bg-amber-600">
                          <Crown className="h-3 w-3 mr-1" />
                          Premium
                        </Badge>
                      ) : (
                        <Badge variant="secondary">Standard</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {formatDate(asset.scraped_at)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <a
                        href={asset.preview_url || `https://stock.adobe.com/images/${asset.adobe_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Button variant="ghost" size="icon">
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      </a>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
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
