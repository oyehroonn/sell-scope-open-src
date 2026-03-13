"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Camera,
  Video,
  Sparkles,
  Crown,
  User,
  Eye,
  Tag,
  Plus,
  Check,
  Loader2,
  Library,
} from "lucide-react";

export interface AssetData {
  adobe_id: string;
  title: string;
  thumbnail_url: string;
  preview_url?: string;
  asset_type: string;
  contributor_name?: string;
  contributor_id?: string;
  is_premium?: boolean;
  is_ai_generated?: boolean;
  is_editorial?: boolean;
  width?: number;
  height?: number;
  orientation?: string;
  keyword_count?: number;
  keywords?: string[];
}

interface AssetCardProps {
  asset: AssetData;
  index: number;
  showAddToLibrary?: boolean;
  inLibrary?: boolean;
  onAddToLibrary?: (asset: AssetData) => Promise<void>;
}

export function AssetCard({ asset, index, showAddToLibrary = true, inLibrary = false, onAddToLibrary }: AssetCardProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [isAdded, setIsAdded] = useState(inLibrary);

  const getTypeIcon = () => {
    switch (asset.asset_type) {
      case "video":
        return <Video className="h-3 w-3" />;
      case "vector":
        return <Sparkles className="h-3 w-3" />;
      default:
        return <Camera className="h-3 w-3" />;
    }
  };

  const handleAddToLibrary = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (isAdded || isAdding) return;
    
    setIsAdding(true);
    try {
      if (onAddToLibrary) {
        await onAddToLibrary(asset);
      }
      setIsAdded(true);
    } catch (error) {
      console.error("Failed to add to library:", error);
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="group"
    >
      <Link href={`/dashboard/assets/${asset.adobe_id}`}>
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 shadow-lg hover:shadow-2xl transition-all duration-300">
          {/* Image container */}
          <div className="relative aspect-[4/3] overflow-hidden">
            {asset.thumbnail_url ? (
              <Image
                src={asset.thumbnail_url}
                alt={asset.title || "Asset"}
                fill
                className="object-cover transition-transform duration-500 group-hover:scale-110"
                sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-violet-500/20 to-blue-500/20">
                <Camera className="h-12 w-12 text-muted-foreground" />
              </div>
            )}
            
            {/* Overlay gradient */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            
            {/* Top badges */}
            <div className="absolute top-2 left-2 flex flex-wrap gap-1">
              <Badge variant="secondary" className="bg-black/50 text-white border-0 text-xs backdrop-blur-sm">
                {getTypeIcon()}
                <span className="ml-1 capitalize">{asset.asset_type}</span>
              </Badge>
              
              {asset.is_premium && (
                <Badge className="bg-gradient-to-r from-amber-500 to-orange-500 text-white border-0 text-xs">
                  <Crown className="h-3 w-3 mr-1" />
                  Premium
                </Badge>
              )}
              
              {asset.is_ai_generated && (
                <Badge className="bg-gradient-to-r from-violet-500 to-purple-500 text-white border-0 text-xs">
                  <Sparkles className="h-3 w-3 mr-1" />
                  AI
                </Badge>
              )}
              {isAdded && (
                <Badge className="bg-gradient-to-r from-emerald-500 to-green-500 text-white border-0 text-xs">
                  <Library className="h-3 w-3 mr-1" />
                  In Library
                </Badge>
              )}
            </div>
            
            {/* Dimensions badge */}
            {asset.width && asset.height && (
              <div className="absolute top-2 right-2">
                <Badge variant="secondary" className="bg-black/50 text-white border-0 text-xs backdrop-blur-sm">
                  {asset.width} × {asset.height}
                </Badge>
              </div>
            )}
            
            {/* Add to Library button - appears on hover */}
            {showAddToLibrary && (
              <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <Button
                  size="sm"
                  onClick={handleAddToLibrary}
                  disabled={isAdding || isAdded}
                  className={`h-8 text-xs shadow-lg ${
                    isAdded 
                      ? "bg-emerald-500 hover:bg-emerald-600" 
                      : "bg-violet-600 hover:bg-violet-700"
                  }`}
                >
                  {isAdding ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : isAdded ? (
                    <>
                      <Check className="h-3 w-3 mr-1" />
                      Added
                    </>
                  ) : (
                    <>
                      <Plus className="h-3 w-3 mr-1" />
                      Add to Library
                    </>
                  )}
                </Button>
              </div>
            )}
            
            {/* Bottom info - appears on hover */}
            <div className="absolute bottom-0 left-0 right-2/3 p-3 translate-y-full group-hover:translate-y-0 transition-transform duration-300">
              <div className="flex items-center gap-2 text-white text-sm">
                {asset.contributor_name && (
                  <span className="flex items-center gap-1 text-xs">
                    <User className="h-3 w-3" />
                    {asset.contributor_name}
                  </span>
                )}
              </div>
            </div>
          </div>
          
          {/* Card content */}
          <div className="p-3">
            <h3 className="font-medium text-sm line-clamp-2 group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
              {asset.title || `Asset #${asset.adobe_id}`}
            </h3>
            
            {/* Quick stats */}
            <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Eye className="h-3 w-3" />
                View details
              </span>
              {asset.keyword_count && asset.keyword_count > 0 && (
                <span className="flex items-center gap-1">
                  <Tag className="h-3 w-3" />
                  {asset.keyword_count}
                </span>
              )}
            </div>
          </div>
          
          {/* Hover glow effect */}
          <div className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
            style={{
              background: "linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(59, 130, 246, 0.1))",
              boxShadow: "inset 0 0 30px rgba(139, 92, 246, 0.1)",
            }}
          />
        </div>
      </Link>
    </motion.div>
  );
}

export function AssetCardSkeleton() {
  return (
    <div className="rounded-xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 shadow-lg overflow-hidden animate-pulse">
      <div className="aspect-[4/3] bg-gray-300 dark:bg-gray-700" />
      <div className="p-3 space-y-2">
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-3/4" />
        <div className="h-3 bg-gray-300 dark:bg-gray-700 rounded w-1/2" />
      </div>
    </div>
  );
}
