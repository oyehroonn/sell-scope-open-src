"use client";

import { useMemo, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Network, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface KeywordNode {
  text: string;
  value: number;
}

interface KeywordNetworkProps {
  keywords: KeywordNode[];
  centralKeyword?: string;
  className?: string;
}

export function KeywordNetwork({
  keywords,
  centralKeyword,
  className = "",
}: KeywordNetworkProps) {
  const [zoom, setZoom] = useState(1);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const nodes = useMemo(() => {
    if (!keywords || keywords.length === 0) return [];

    const maxValue = Math.max(...keywords.map((k) => k.value));
    const sortedKeywords = [...keywords].sort((a, b) => b.value - a.value);
    const topKeywords = sortedKeywords.slice(0, expanded ? 30 : 15);

    const centerX = 200;
    const centerY = 150;
    const maxRadius = expanded ? 130 : 100;
    const minRadius = 40;

    return topKeywords.map((keyword, index) => {
      const normalizedValue = keyword.value / maxValue;
      const size = 16 + normalizedValue * 24;
      
      if (index === 0 && !centralKeyword) {
        return {
          ...keyword,
          x: centerX,
          y: centerY,
          size,
          isCenter: true,
        };
      }

      const angle = ((index - 1) / (topKeywords.length - 1)) * 2 * Math.PI;
      const radiusVariation = 0.7 + (1 - normalizedValue) * 0.3;
      const radius = minRadius + (maxRadius - minRadius) * radiusVariation;

      return {
        ...keyword,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
        size,
        isCenter: false,
      };
    });
  }, [keywords, expanded, centralKeyword]);

  const edges = useMemo(() => {
    if (nodes.length < 2) return [];

    const centerNode = nodes.find((n) => n.isCenter) || nodes[0];
    const edgeList: Array<{
      from: typeof centerNode;
      to: typeof centerNode;
      strength: number;
    }> = [];

    nodes.forEach((node, i) => {
      if (node === centerNode) return;
      const strength = node.value / Math.max(...nodes.map((n) => n.value));
      edgeList.push({
        from: centerNode,
        to: node,
        strength,
      });
    });

    return edgeList;
  }, [nodes]);

  const getNodeColor = (node: { text: string; value: number; isCenter?: boolean }) => {
    if (node.isCenter) return "#8b5cf6";
    const intensity = Math.min(1, node.value / Math.max(...nodes.map((n) => n.value)));
    const hue = 270 - intensity * 50;
    return `hsl(${hue}, 70%, 60%)`;
  };

  if (!keywords || keywords.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Network className="h-4 w-4" />
            Related Keywords Network
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-gray-500">
            No keyword data available
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
            <Network className="h-4 w-4" />
            Related Keywords Network
            {centralKeyword && (
              <Badge variant="secondary" className="ml-2">
                {centralKeyword}
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => setZoom((z) => Math.max(0.5, z - 0.2))}
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => setZoom((z) => Math.min(2, z + 0.2))}
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => setExpanded(!expanded)}
            >
              <Maximize2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div
          className={`relative overflow-hidden rounded-lg bg-gray-50 dark:bg-gray-800/50 ${
            expanded ? "h-96" : "h-64"
          }`}
        >
          <svg
            width="100%"
            height="100%"
            viewBox={`0 0 400 ${expanded ? 350 : 300}`}
            style={{ transform: `scale(${zoom})` }}
            className="transition-transform duration-200"
          >
            <defs>
              <filter id="glow">
                <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Edges */}
            {edges.map((edge, i) => (
              <motion.line
                key={`edge-${i}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.3 + edge.strength * 0.5 }}
                x1={edge.from.x}
                y1={edge.from.y}
                x2={edge.to.x}
                y2={edge.to.y}
                stroke={hoveredNode === edge.to.text ? "#8b5cf6" : "#94a3b8"}
                strokeWidth={1 + edge.strength * 2}
                strokeDasharray={hoveredNode === edge.to.text ? "none" : "4 2"}
              />
            ))}

            {/* Nodes */}
            {nodes.map((node, i) => (
              <motion.g
                key={`node-${i}`}
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.02 }}
                onMouseEnter={() => setHoveredNode(node.text)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ cursor: "pointer" }}
              >
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={hoveredNode === node.text ? node.size * 1.2 : node.size}
                  fill={getNodeColor(node)}
                  opacity={hoveredNode === node.text || hoveredNode === null ? 0.9 : 0.5}
                  filter={node.isCenter || hoveredNode === node.text ? "url(#glow)" : undefined}
                  className="transition-all duration-200"
                />
                <text
                  x={node.x}
                  y={node.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="white"
                  fontSize={node.isCenter ? 10 : 8}
                  fontWeight={node.isCenter ? "bold" : "normal"}
                  className="pointer-events-none"
                >
                  {node.text.length > 10 ? node.text.slice(0, 8) + "..." : node.text}
                </text>
              </motion.g>
            ))}
          </svg>

          {/* Hover tooltip */}
          <AnimatePresence>
            {hoveredNode && (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 5 }}
                className="absolute bottom-3 left-3 bg-white dark:bg-gray-900 px-3 py-2 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700"
              >
                <p className="font-medium text-sm">{hoveredNode}</p>
                <p className="text-xs text-gray-500">
                  Frequency: {nodes.find((n) => n.text === hoveredNode)?.value || 0}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-purple-500" />
              <span>Central/High</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-pink-400" />
              <span>Medium</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-slate-400" />
              <span>Low</span>
            </div>
          </div>
          <span className="text-xs text-gray-500">
            {nodes.length} keywords • {edges.length} connections
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

export default KeywordNetwork;
