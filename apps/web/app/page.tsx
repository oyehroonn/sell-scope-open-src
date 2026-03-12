import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  BarChart3,
  Brain,
  Eye,
  Lightbulb,
  Search,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 border-b bg-background/80 backdrop-blur-sm">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <Target className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-bold text-xl">SellScope</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link href="/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="container max-w-6xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-8">
            <Zap className="h-4 w-4" />
            <span>Open Source Intelligence Platform</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
            Stop Guessing.
            <br />
            <span className="gradient-text">Start Selling.</span>
          </h1>

          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            The Bloomberg Terminal for Adobe Stock contributors. Real demand
            data, opportunity scoring, AI briefs, and automated workflows —
            all in one platform.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/dashboard">
              <Button size="lg" className="gap-2">
                Launch Dashboard
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link
              href="https://github.com/sellscope/sellscope"
              target="_blank"
            >
              <Button size="lg" variant="outline">
                View on GitHub
              </Button>
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-20 p-8 rounded-2xl bg-card border">
            <div>
              <div className="text-3xl font-bold text-primary">500K+</div>
              <div className="text-sm text-muted-foreground">
                Keywords Analyzed
              </div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary">50K+</div>
              <div className="text-sm text-muted-foreground">
                Portfolios Tracked
              </div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary">Real-time</div>
              <div className="text-sm text-muted-foreground">
                Market Data
              </div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary">100%</div>
              <div className="text-sm text-muted-foreground">
                Open Source
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4 bg-muted/50">
        <div className="container max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything You Need to Dominate Stock
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              From market research to automated publishing — a complete
              intelligence platform for serious contributors.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard
              icon={<Target className="h-6 w-6" />}
              title="Opportunity Scoring"
              description="Every keyword gets a 0-100 score based on demand, competition, seasonality, and production difficulty. Know exactly what to create next."
            />
            <FeatureCard
              icon={<Eye className="h-6 w-6" />}
              title="Visual Whitespace"
              description="AI-powered analysis of visual gaps in any niche. Find underrepresented styles, compositions, and color palettes."
            />
            <FeatureCard
              icon={<Lightbulb className="h-6 w-6" />}
              title="AI Brief Generator"
              description="Turn any opportunity into 20 shot ideas, style directions, keyword clusters, and compliance notes."
            />
            <FeatureCard
              icon={<BarChart3 className="h-6 w-6" />}
              title="Portfolio Coach"
              description="Identify underperformers, cannibalization, and expansion opportunities in your own portfolio."
            />
            <FeatureCard
              icon={<Brain className="h-6 w-6" />}
              title="Predictive Demand"
              description="Seasonal forecasting, event spikes, and trend detection — know what buyers want before they search."
            />
            <FeatureCard
              icon={<TrendingUp className="h-6 w-6" />}
              title="Live Market Pulse"
              description="Real-time trending searches, competitor uploads, and ranking changes for your tracked niches."
            />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4">
        <div className="container max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              From Research to Revenue in 3 Steps
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
                <Search className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">1. Discover</h3>
              <p className="text-muted-foreground">
                Search any keyword or niche. Get instant opportunity scores,
                competition analysis, and visual gap detection.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
                <Lightbulb className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">2. Create</h3>
              <p className="text-muted-foreground">
                Generate AI production briefs with shot ideas, style
                direction, and optimized keywords for maximum discoverability.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
                <TrendingUp className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">3. Optimize</h3>
              <p className="text-muted-foreground">
                Track performance, get coaching insights, and automate social
                promotion with Make.com integration.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="container max-w-4xl mx-auto">
          <div className="rounded-3xl bg-gradient-to-r from-primary/20 via-primary/10 to-purple-500/20 p-12 text-center border">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Ready to Transform Your Stock Business?
            </h2>
            <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
              Join contributors who stopped guessing and started earning
              more. Self-host for free or use our managed platform.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/register">
                <Button size="lg" className="gap-2">
                  Start Free
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/pricing">
                <Button size="lg" variant="outline">
                  View Pricing
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12 px-4">
        <div className="container max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <Target className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="font-bold">SellScope</span>
            </div>
            <div className="text-sm text-muted-foreground">
              Open source under MIT License. Built with data, not hype.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="p-6 rounded-2xl bg-card border hover:border-primary/50 transition-colors">
      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4 text-primary">
        {icon}
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground text-sm">{description}</p>
    </div>
  );
}
