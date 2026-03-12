"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Camera,
  Clock,
  Copy,
  Download,
  Lightbulb,
  Loader2,
  Palette,
  Sparkles,
  Tag,
  Target,
  Wand2,
} from "lucide-react";

interface Brief {
  keyword: string;
  opportunityScore: number;
  shotIdeas: {
    title: string;
    description: string;
    composition: string;
    lighting: string;
    mood: string;
  }[];
  styleDirection: {
    lighting: string;
    mood: string;
    props: string[];
  };
  colorPalette: string[];
  keywordStrategies: {
    name: string;
    keywords: string[];
    description: string;
  }[];
  aiPrompts: string[];
  complianceNotes: string[];
  timeToMoney: {
    daysToFirstSale: number;
    monthlyPotential: string;
    priority: string;
  };
}

const mockBrief: Brief = {
  keyword: "remote work lifestyle",
  opportunityScore: 87,
  shotIdeas: [
    {
      title: "Remote Work Lifestyle - Hero Shot",
      description: "Main subject centered, full context visible featuring remote work lifestyle",
      composition: "hero",
      lighting: "Clean, professional studio lighting or natural office light",
      mood: "Confident, productive, collaborative",
    },
    {
      title: "Remote Work Lifestyle - Detail",
      description: "Close-up on key element or texture",
      composition: "detail",
      lighting: "Soft natural light with gentle shadows",
      mood: "Focused, intimate, professional",
    },
    {
      title: "Remote Work Lifestyle - Lifestyle Context",
      description: "Subject in use within real home office environment",
      composition: "lifestyle",
      lighting: "Warm, natural golden hour or soft indoor lighting",
      mood: "Relaxed, authentic, aspirational",
    },
    {
      title: "Remote Work Lifestyle - Flat Lay",
      description: "Top-down arrangement of work essentials",
      composition: "flat_lay",
      lighting: "Even, diffused lighting with soft shadows",
      mood: "Organized, clean, minimalist",
    },
    {
      title: "Remote Work Lifestyle - Negative Space",
      description: "Subject with ample copy space for text overlay",
      composition: "negative_space",
      lighting: "Clean background with subject focus",
      mood: "Clean, commercial-ready",
    },
  ],
  styleDirection: {
    lighting: "Clean, professional studio lighting or natural office light",
    mood: "Confident, productive, collaborative",
    props: ["laptop", "notebook", "coffee", "modern desk", "plants"],
  },
  colorPalette: ["#2563eb", "#1e40af", "#3b82f6", "#f8fafc", "#64748b"],
  keywordStrategies: [
    {
      name: "Literal Descriptive",
      keywords: ["remote work", "work from home", "home office", "remote worker", "telecommute"],
      description: "Exact match and direct descriptive terms for literal searches",
    },
    {
      name: "Buyer Intent",
      keywords: ["remote work for business", "professional home office", "corporate remote", "remote team"],
      description: "Terms that indicate commercial purchase intent",
    },
    {
      name: "Long-tail Specific",
      keywords: ["modern remote work setup", "minimalist home office", "remote work lifestyle aesthetic"],
      description: "Specific variations with lower competition",
    },
  ],
  aiPrompts: [
    "Professional stock photo of remote work lifestyle, clean modern home office setup, natural window lighting, productive mood, high resolution, commercial quality",
    "Clean and modern remote worker photograph, laptop on wooden desk, indoor plants, white minimalist background, 8k quality",
    "Remote work lifestyle in cozy home setting, lifestyle photography, authentic and candid, warm color grading, editorial quality",
  ],
  complianceNotes: [
    "Standard compliance - ensure no identifiable trademarks, logos, or recognizable private property",
    "If AI-generated: Must disclose as AI-generated content per Adobe Stock guidelines",
    "Ensure keywords accurately describe visible content - avoid keyword stuffing",
  ],
  timeToMoney: {
    daysToFirstSale: 7,
    monthlyPotential: "$20-50",
    priority: "high",
  },
};

export default function BriefsPage() {
  const [keyword, setKeyword] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [brief, setBrief] = useState<Brief | null>(null);

  const handleGenerate = async () => {
    if (!keyword.trim()) return;
    
    setIsGenerating(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setBrief(mockBrief);
    setIsGenerating(false);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Brief Generator</h1>
        <p className="text-muted-foreground">
          Turn any keyword into a complete production brief with shot ideas, keywords, and AI prompts
        </p>
      </div>

      {/* Generator Input */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Lightbulb className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Enter a keyword to generate a production brief..."
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                className="pl-10"
              />
            </div>
            <Button onClick={handleGenerate} disabled={isGenerating} className="gap-2">
              {isGenerating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Wand2 className="h-4 w-4" />
              )}
              Generate Brief
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Generated Brief */}
      {brief && (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Shot Ideas */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Camera className="h-5 w-5 text-primary" />
                  Shot Ideas ({brief.shotIdeas.length})
                </CardTitle>
                <CardDescription>
                  Production-ready shot concepts for "{brief.keyword}"
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {brief.shotIdeas.map((shot, index) => (
                    <div key={index} className="p-4 rounded-lg border bg-card">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold">{shot.title}</h4>
                        <Badge variant="outline">{shot.composition}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">
                        {shot.description}
                      </p>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-muted-foreground">Lighting:</span>{" "}
                          {shot.lighting}
                        </div>
                        <div>
                          <span className="text-muted-foreground">Mood:</span>{" "}
                          {shot.mood}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Keyword Strategies */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Tag className="h-5 w-5 text-primary" />
                  Keyword Strategies
                </CardTitle>
                <CardDescription>
                  Multiple keyword approaches for maximum discoverability
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue={brief.keywordStrategies[0]?.name}>
                  <TabsList className="mb-4">
                    {brief.keywordStrategies.map((strategy) => (
                      <TabsTrigger key={strategy.name} value={strategy.name}>
                        {strategy.name}
                      </TabsTrigger>
                    ))}
                  </TabsList>
                  {brief.keywordStrategies.map((strategy) => (
                    <TabsContent key={strategy.name} value={strategy.name}>
                      <p className="text-sm text-muted-foreground mb-3">
                        {strategy.description}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {strategy.keywords.map((kw) => (
                          <Badge key={kw} variant="secondary">
                            {kw}
                          </Badge>
                        ))}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-4 gap-2"
                        onClick={() =>
                          copyToClipboard(strategy.keywords.join(", "))
                        }
                      >
                        <Copy className="h-4 w-4" />
                        Copy All
                      </Button>
                    </TabsContent>
                  ))}
                </Tabs>
              </CardContent>
            </Card>

            {/* AI Prompts */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  AI Generation Prompts
                </CardTitle>
                <CardDescription>
                  Ready-to-use prompts for AI image generation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {brief.aiPrompts.map((prompt, index) => (
                    <div
                      key={index}
                      className="p-3 rounded-lg border bg-muted/50 relative group"
                    >
                      <p className="text-sm pr-8">{prompt}</p>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => copyToClipboard(prompt)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Score & ROI */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-primary" />
                  Opportunity Score
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center mb-6">
                  <div className="text-5xl font-bold text-emerald-500">
                    {brief.opportunityScore}
                  </div>
                  <Badge className="mt-2">{brief.timeToMoney.priority} priority</Badge>
                </div>
                <Separator className="my-4" />
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Time to First Sale
                    </span>
                    <span className="font-medium">
                      ~{brief.timeToMoney.daysToFirstSale} days
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">
                      Monthly Potential
                    </span>
                    <span className="font-medium text-emerald-500">
                      {brief.timeToMoney.monthlyPotential}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Style Direction */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Palette className="h-5 w-5 text-primary" />
                  Style Direction
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">
                      Lighting
                    </div>
                    <p className="text-sm">{brief.styleDirection.lighting}</p>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">Mood</div>
                    <p className="text-sm">{brief.styleDirection.mood}</p>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground mb-2">
                      Suggested Props
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {brief.styleDirection.props.map((prop) => (
                        <Badge key={prop} variant="outline" className="text-xs">
                          {prop}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground mb-2">
                      Color Palette
                    </div>
                    <div className="flex gap-1">
                      {brief.colorPalette.map((color) => (
                        <div
                          key={color}
                          className="h-8 w-8 rounded-md border"
                          style={{ backgroundColor: color }}
                          title={color}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Compliance */}
            <Card>
              <CardHeader>
                <CardTitle>Compliance Notes</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  {brief.complianceNotes.map((note, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      {note}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Export */}
            <Button className="w-full gap-2">
              <Download className="h-4 w-4" />
              Export Brief
            </Button>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!brief && !isGenerating && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <Wand2 className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Generate Your First Brief</h3>
          <p className="text-muted-foreground max-w-md">
            Enter a keyword or niche and let AI create a complete production brief
            with shot ideas, keyword strategies, and more.
          </p>
        </div>
      )}
    </div>
  );
}
