"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ArrowLeft,
  Camera,
  Video,
  Sparkles,
  Crown,
  User,
  Tag,
  Maximize2,
  Download,
  ExternalLink,
  Copy,
  Check,
  Layers,
  Palette,
  FileType,
  Calendar,
  Eye,
  TrendingUp,
  BarChart3,
  PieChart,
  Grid3X3,
  Share2,
  Heart,
  Bookmark,
  Info,
  Zap,
  Globe,
  Shield,
  Clock,
  Hash,
  Link2,
  ChevronRight,
  Library,
  Plus,
  Loader2,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AssetDetail {
  [key: string]: any;
}

export default function AssetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inLibrary, setInLibrary] = useState(false);
  const [addingToLibrary, setAddingToLibrary] = useState(false);

  useEffect(() => {
    const fetchAsset = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Try scraped endpoint first
        let response = await fetch(`${API_BASE}/assets/${params.id}/scraped`);
        
        if (!response.ok) {
          // Fallback to regular asset endpoint
          response = await fetch(`${API_BASE}/assets/${params.id}`);
        }
        
        if (response.ok) {
          const data = await response.json();
          
          // Parse string arrays if needed
          const parseArray = (val: any): any[] => {
            if (Array.isArray(val)) return val;
            if (typeof val === "string") {
              try {
                return JSON.parse(val.replace(/'/g, '"'));
              } catch {
                return val.split("|").filter(Boolean);
              }
            }
            return [];
          };
          
          setAsset({
            ...data,
            keywords_list: parseArray(data.keywords_list || data.keywords),
            similar_asset_ids: parseArray(data.similar_asset_ids),
            categories: parseArray(data.categories),
            color_palette: parseArray(data.color_palette),
          });
          
          // Check library status
          setInLibrary(data.in_library === true);
        } else {
          setError("Asset not found");
        }
      } catch (err) {
        console.error("Failed to fetch asset:", err);
        setError("Failed to load asset");
      } finally {
        setLoading(false);
      }
    };

    if (params.id) {
      fetchAsset();
    }
  }, [params.id]);
  
  const handleAddToLibrary = async () => {
    if (addingToLibrary || inLibrary) return;
    
    setAddingToLibrary(true);
    try {
      const response = await fetch(`${API_BASE}/assets/${params.id}/library`, {
        method: "POST",
      });
      
      if (response.ok) {
        setInLibrary(true);
      }
    } catch (err) {
      console.error("Failed to add to library:", err);
    } finally {
      setAddingToLibrary(false);
    }
  };
  
  const handleRemoveFromLibrary = async () => {
    if (addingToLibrary || !inLibrary) return;
    
    setAddingToLibrary(true);
    try {
      const response = await fetch(`${API_BASE}/assets/${params.id}/library`, {
        method: "DELETE",
      });
      
      if (response.ok) {
        setInLibrary(false);
      }
    } catch (err) {
      console.error("Failed to remove from library:", err);
    } finally {
      setAddingToLibrary(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "video": return <Video className="h-5 w-5" />;
      case "vector": return <Sparkles className="h-5 w-5" />;
      default: return <Camera className="h-5 w-5" />;
    }
  };

  const formatValue = (val: any): string => {
    if (val === null || val === undefined || val === "" || val === "None") return "—";
    if (typeof val === "boolean") return val ? "Yes" : "No";
    return String(val);
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded-full" />
          <Skeleton className="h-8 w-64" />
        </div>
        <div className="grid lg:grid-cols-5 gap-8">
          <div className="lg:col-span-3">
            <Skeleton className="aspect-[4/3] rounded-2xl" />
          </div>
          <div className="lg:col-span-2 space-y-4">
            <Skeleton className="h-40 rounded-xl" />
            <Skeleton className="h-60 rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !asset) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="text-center"
        >
          <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-red-500/20 to-orange-500/20 flex items-center justify-center">
            <Info className="h-12 w-12 text-red-500" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Asset Not Found</h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            This asset may not have been scraped yet. Try searching for it first to fetch the data.
          </p>
          <div className="flex gap-3 justify-center">
            <Button variant="outline" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
            <Button onClick={() => router.push("/dashboard/scraper")}>
              <Search className="h-4 w-4 mr-2" />
              Search Assets
            </Button>
          </div>
        </motion.div>
      </div>
    );
  }

  const keywords = asset.keywords_list || [];
  const similarIds = asset.similar_asset_ids || [];
  const assetId = asset.adobe_id || asset.asset_id || params.id;

  // Calculate quality score based on available data
  const qualityFactors = [
    keywords.length > 10,
    asset.width && asset.height,
    asset.contributor_name,
    asset.description,
    asset.file_format,
    similarIds.length > 0,
    asset.preview_url || asset.thumbnail_url,
  ];
  const qualityScore = Math.round((qualityFactors.filter(Boolean).length / qualityFactors.length) * 100);

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4"
      >
        <Button variant="ghost" size="icon" onClick={() => router.back()} className="shrink-0">
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Link href="/dashboard/scraper" className="hover:text-foreground transition-colors">
              Search
            </Link>
            <ChevronRight className="h-4 w-4" />
            <span className="truncate">Asset Details</span>
          </div>
          <h1 className="text-2xl font-bold truncate">Asset #{assetId}</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon">
            <Heart className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon">
            <Bookmark className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon">
            <Share2 className="h-4 w-4" />
          </Button>
          {asset.asset_url && (
            <Button variant="outline" asChild>
              <a href={asset.asset_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 mr-2" />
                View on Adobe
              </a>
            </Button>
          )}
        </div>
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-5 gap-8">
        {/* Left Column - Image & Description */}
        <div className="lg:col-span-3 space-y-6">
          {/* Image Preview */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative aspect-[4/3] rounded-2xl overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 shadow-2xl group"
          >
            {(asset.preview_url || asset.thumbnail_url) ? (
              <Image
                src={asset.preview_url || asset.thumbnail_url}
                alt={asset.title || "Asset preview"}
                fill
                className="object-contain transition-transform duration-500 group-hover:scale-105"
                priority
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Camera className="h-20 w-20 text-muted-foreground" />
              </div>
            )}
            
            {/* Floating badges */}
            <div className="absolute top-4 left-4 flex flex-wrap gap-2">
              <Badge className="bg-black/60 text-white border-0 backdrop-blur-sm">
                {getTypeIcon(asset.asset_type || "photo")}
                <span className="ml-1 capitalize">{asset.asset_type || "photo"}</span>
              </Badge>
              {(asset.is_premium === true || asset.is_premium === "True") && (
                <Badge className="bg-gradient-to-r from-amber-500 to-orange-500 text-white border-0">
                  <Crown className="h-3 w-3 mr-1" />
                  Premium
                </Badge>
              )}
              {(asset.is_ai_generated === true || asset.is_ai_generated === "True") && (
                <Badge className="bg-gradient-to-r from-violet-500 to-purple-500 text-white border-0">
                  <Sparkles className="h-3 w-3 mr-1" />
                  AI Generated
                </Badge>
              )}
              {(asset.is_editorial === true || asset.is_editorial === "True") && (
                <Badge className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white border-0">
                  <Globe className="h-3 w-3 mr-1" />
                  Editorial
                </Badge>
              )}
            </div>
            
            {asset.width && asset.height && (
              <div className="absolute top-4 right-4">
                <Badge className="bg-black/60 text-white border-0 backdrop-blur-sm font-mono">
                  {asset.width} × {asset.height}
                </Badge>
              </div>
            )}
            
            {/* Quality indicator */}
            <div className="absolute bottom-4 right-4">
              <div className="bg-black/60 backdrop-blur-sm rounded-full px-3 py-1.5 flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${qualityScore >= 80 ? 'bg-emerald-500' : qualityScore >= 50 ? 'bg-amber-500' : 'bg-red-500'}`} />
                <span className="text-white text-sm font-medium">{qualityScore}% Data</span>
              </div>
            </div>
          </motion.div>

          {/* Title & Description Card */}
          <Card>
            <CardContent className="pt-6">
              <h2 className="text-xl font-semibold mb-3 leading-relaxed">
                {asset.title || `Asset #${assetId}`}
              </h2>
              {asset.description && (
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {asset.description}
                </p>
              )}
              
              {/* Contributor */}
              {asset.contributor_name && (
                <div className="mt-6 pt-6 border-t flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center text-white font-bold text-lg shadow-lg">
                    {asset.contributor_name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold">{asset.contributor_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {asset.contributor_id ? `ID: ${asset.contributor_id}` : "Contributor"}
                    </p>
                  </div>
                  {asset.contributor_url && (
                    <Button variant="outline" size="sm" asChild>
                      <a href={asset.contributor_url} target="_blank" rel="noopener noreferrer">
                        <User className="h-4 w-4 mr-2" />
                        Profile
                      </a>
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Keywords Visualization */}
          {keywords.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Tag className="h-5 w-5 text-violet-500" />
                    Keywords Analysis
                  </span>
                  <Badge variant="secondary">{keywords.length} keywords</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Keyword Stats Visualization */}
                <div className="grid grid-cols-3 gap-4">
                  <motion.div 
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="relative p-4 rounded-xl bg-gradient-to-br from-violet-500/10 to-violet-500/5 border border-violet-500/20 overflow-hidden"
                  >
                    <div className="absolute top-0 right-0 w-16 h-16 bg-violet-500/10 rounded-full -translate-y-1/2 translate-x-1/2" />
                    <BarChart3 className="h-5 w-5 text-violet-500 mb-2" />
                    <div className="text-2xl font-bold">{keywords.length}</div>
                    <div className="text-xs text-muted-foreground">Total Keywords</div>
                  </motion.div>
                  
                  <motion.div 
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.2 }}
                    className="relative p-4 rounded-xl bg-gradient-to-br from-blue-500/10 to-blue-500/5 border border-blue-500/20 overflow-hidden"
                  >
                    <div className="absolute top-0 right-0 w-16 h-16 bg-blue-500/10 rounded-full -translate-y-1/2 translate-x-1/2" />
                    <TrendingUp className="h-5 w-5 text-blue-500 mb-2" />
                    <div className="text-2xl font-bold">
                      {keywords.length > 0 ? Math.round(keywords.reduce((a, k) => a + k.length, 0) / keywords.length) : 0}
                    </div>
                    <div className="text-xs text-muted-foreground">Avg Length</div>
                  </motion.div>
                  
                  <motion.div 
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="relative p-4 rounded-xl bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20 overflow-hidden"
                  >
                    <div className="absolute top-0 right-0 w-16 h-16 bg-emerald-500/10 rounded-full -translate-y-1/2 translate-x-1/2" />
                    <PieChart className="h-5 w-5 text-emerald-500 mb-2" />
                    <div className="text-2xl font-bold">{Math.min(Math.round(keywords.length / 30 * 100), 100)}%</div>
                    <div className="text-xs text-muted-foreground">SEO Coverage</div>
                  </motion.div>
                </div>

                {/* Keyword Length Distribution Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Keyword density</span>
                    <span className="font-medium">{keywords.length} / 50 optimal</span>
                  </div>
                  <div className="h-3 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(keywords.length / 50 * 100, 100)}%` }}
                      transition={{ duration: 1, ease: "easeOut" }}
                      className="h-full rounded-full"
                      style={{
                        background: keywords.length >= 30 
                          ? "linear-gradient(90deg, #10b981, #059669)" 
                          : keywords.length >= 15 
                            ? "linear-gradient(90deg, #f59e0b, #d97706)"
                            : "linear-gradient(90deg, #ef4444, #dc2626)"
                      }}
                    />
                  </div>
                </div>

                {/* Keyword Cloud */}
                <div className="flex flex-wrap gap-2">
                  {keywords.slice(0, 40).map((keyword, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0.8, y: 10 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      transition={{ delay: index * 0.02 }}
                    >
                      <Badge
                        variant="secondary"
                        className="cursor-pointer hover:bg-violet-100 dark:hover:bg-violet-900/30 transition-all hover:scale-105 hover:shadow-md"
                        style={{
                          fontSize: `${Math.max(0.75, 1 - index * 0.008)}rem`,
                          opacity: Math.max(0.6, 1 - index * 0.015),
                        }}
                      >
                        {keyword}
                      </Badge>
                    </motion.div>
                  ))}
                  {keywords.length > 40 && (
                    <Badge variant="outline" className="text-muted-foreground">
                      +{keywords.length - 40} more
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Similar Assets Network */}
          {similarIds.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Link2 className="h-5 w-5 text-blue-500" />
                    Related Assets Network
                  </span>
                  <Badge variant="secondary">{similarIds.length} connected</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {/* Network Visualization */}
                <div className="relative h-48 mb-6 rounded-xl bg-gradient-to-br from-blue-500/5 to-violet-500/5 border border-blue-500/10 overflow-hidden">
                  {/* Center node */}
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                    <motion.div
                      animate={{ scale: [1, 1.1, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="w-16 h-16 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center text-white font-bold shadow-lg shadow-violet-500/30"
                    >
                      <Hash className="h-6 w-6" />
                    </motion.div>
                  </div>
                  
                  {/* Connected nodes */}
                  {similarIds.slice(0, 8).map((id, index) => {
                    const angle = (index / 8) * 2 * Math.PI - Math.PI / 2;
                    const radius = 70;
                    const x = Math.cos(angle) * radius;
                    const y = Math.sin(angle) * radius;
                    
                    return (
                      <motion.div
                        key={id}
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.1 }}
                        className="absolute top-1/2 left-1/2"
                        style={{ transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))` }}
                      >
                        {/* Connection line */}
                        <svg className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none" width="200" height="200" style={{ transform: `translate(${-x/2}px, ${-y/2}px)` }}>
                          <line
                            x1="100"
                            y1="100"
                            x2={100 - x}
                            y2={100 - y}
                            stroke="url(#gradient)"
                            strokeWidth="1"
                            strokeDasharray="4 2"
                            opacity="0.3"
                          />
                          <defs>
                            <linearGradient id="gradient">
                              <stop offset="0%" stopColor="#8b5cf6" />
                              <stop offset="100%" stopColor="#3b82f6" />
                            </linearGradient>
                          </defs>
                        </svg>
                        
                        <Link href={`/dashboard/assets/${id}`}>
                          <motion.div
                            whileHover={{ scale: 1.2 }}
                            className="w-10 h-10 rounded-full bg-white dark:bg-gray-800 border-2 border-blue-500/30 flex items-center justify-center text-xs font-mono shadow-md cursor-pointer hover:border-blue-500 transition-colors"
                          >
                            {id.slice(-4)}
                          </motion.div>
                        </Link>
                      </motion.div>
                    );
                  })}
                </div>
                
                {/* ID List */}
                <div className="flex flex-wrap gap-2">
                  {similarIds.slice(0, 15).map((id, index) => (
                    <Link key={id} href={`/dashboard/assets/${id}`}>
                      <Badge
                        variant="outline"
                        className="cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors font-mono text-xs"
                      >
                        #{id}
                      </Badge>
                    </Link>
                  ))}
                  {similarIds.length > 15 && (
                    <Badge variant="secondary">+{similarIds.length - 15} more</Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Stats & Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Quick Stats Ring */}
          <Card className="bg-gradient-to-br from-violet-500/5 via-blue-500/5 to-emerald-500/5 border-violet-500/20">
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: "Keywords", value: keywords.length, icon: Tag, color: "violet" },
                  { label: "Megapixels", value: asset.megapixels || "—", icon: Maximize2, color: "blue" },
                  { label: "Similar", value: similarIds.length, icon: Layers, color: "emerald" },
                  { label: "Position", value: asset.position || "—", icon: TrendingUp, color: "amber" },
                ].map((stat, index) => (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="text-center p-4 rounded-xl bg-white/50 dark:bg-black/20 backdrop-blur-sm"
                  >
                    <stat.icon className={`h-5 w-5 mx-auto mb-2 text-${stat.color}-500`} />
                    <div className={`text-2xl font-bold bg-gradient-to-r from-${stat.color}-600 to-${stat.color}-400 bg-clip-text text-transparent`}>
                      {stat.value}
                    </div>
                    <div className="text-xs text-muted-foreground">{stat.label}</div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Technical Specifications */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Grid3X3 className="h-5 w-5 text-blue-500" />
                Technical Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              {[
                { icon: FileType, label: "Format", value: asset.file_format },
                { icon: Maximize2, label: "Dimensions", value: asset.width && asset.height ? `${asset.width} × ${asset.height} px` : null },
                { icon: Layers, label: "Aspect Ratio", value: asset.aspect_ratio ? `${asset.aspect_ratio}:1` : null },
                { icon: Eye, label: "Orientation", value: asset.orientation },
                { icon: Zap, label: "Megapixels", value: asset.megapixels ? `${asset.megapixels} MP` : null },
                { icon: Download, label: "File Size", value: asset.file_size },
                { icon: Eye, label: "DPI", value: asset.dpi },
              ].filter(item => item.value && item.value !== "—").map((item, index) => (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center justify-between py-3 border-b border-gray-100 dark:border-gray-800 last:border-0"
                >
                  <span className="flex items-center gap-2 text-muted-foreground">
                    <item.icon className="h-4 w-4" />
                    {item.label}
                  </span>
                  <span className="font-medium">{formatValue(item.value)}</span>
                </motion.div>
              ))}
            </CardContent>
          </Card>

          {/* Licensing & Rights */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="h-5 w-5 text-emerald-500" />
                Licensing & Rights
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {asset.license_type && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">License Type</span>
                  <Badge variant={asset.license_type === "Premium" ? "default" : "secondary"}>
                    {asset.license_type}
                  </Badge>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-3 pt-2">
                {[
                  { label: "Premium", value: asset.is_premium, color: "amber" },
                  { label: "Editorial", value: asset.is_editorial, color: "blue" },
                  { label: "AI Generated", value: asset.is_ai_generated, color: "violet" },
                  { label: "Model Release", value: asset.has_model_release, color: "emerald" },
                ].map((item) => (
                  <div
                    key={item.label}
                    className={`p-3 rounded-lg border ${
                      item.value === true || item.value === "True"
                        ? `bg-${item.color}-500/10 border-${item.color}-500/30`
                        : "bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800"
                    }`}
                  >
                    <div className="text-xs text-muted-foreground mb-1">{item.label}</div>
                    <div className="font-medium">
                      {item.value === true || item.value === "True" ? "Yes" : "No"}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Asset ID & Actions */}
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-900">
                <div>
                  <p className="text-xs text-muted-foreground">Asset ID</p>
                  <p className="font-mono font-bold text-lg">{assetId}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(assetId)}
                >
                  {copied ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
              
              {/* Add to Library Button */}
              <Button 
                className={`w-full ${
                  inLibrary 
                    ? "bg-emerald-600 hover:bg-emerald-700" 
                    : "bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-700 hover:to-blue-700"
                }`}
                onClick={inLibrary ? handleRemoveFromLibrary : handleAddToLibrary}
                disabled={addingToLibrary}
              >
                {addingToLibrary ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : inLibrary ? (
                  <Check className="h-4 w-4 mr-2" />
                ) : (
                  <Plus className="h-4 w-4 mr-2" />
                )}
                {addingToLibrary 
                  ? "Processing..." 
                  : inLibrary 
                    ? "In Library" 
                    : "Add to Library"
                }
              </Button>
              
              {asset.asset_url && (
                <Button className="w-full" variant="outline" asChild>
                  <a href={asset.asset_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View on Adobe Stock
                  </a>
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Metadata */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Clock className="h-5 w-5 text-gray-500" />
                Metadata
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { label: "Search Query", value: asset.search_query },
                { label: "Search Position", value: asset.position ? `#${asset.position}` : null },
                { label: "Category", value: asset.category },
                { label: "Scraped At", value: asset.scraped_at ? new Date(asset.scraped_at).toLocaleString() : null },
              ].filter(item => item.value).map((item) => (
                <div key={item.label} className="p-3 rounded-lg bg-gray-50 dark:bg-gray-900">
                  <p className="text-xs text-muted-foreground mb-1">{item.label}</p>
                  <p className="font-medium text-sm">{item.value}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Search(props: any) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}
