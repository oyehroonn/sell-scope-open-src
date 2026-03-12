"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  AlertCircle,
  CheckCircle,
  Clock,
  Download,
  Loader2,
  Play,
  Search,
  Terminal,
} from "lucide-react";

interface ScrapeJob {
  id: string;
  query: string;
  status: "pending" | "running" | "completed" | "failed";
  resultsCount: number;
  startedAt: string;
  completedAt?: string;
  error?: string;
}

export default function ScraperPage() {
  const [query, setQuery] = useState("");
  const [maxResults, setMaxResults] = useState(500);
  const [scrapeDetails, setScrapeDetails] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [jobs, setJobs] = useState<ScrapeJob[]>([]);

  const handleStartScrape = async () => {
    if (!query.trim()) return;

    const newJob: ScrapeJob = {
      id: Date.now().toString(),
      query: query.trim(),
      status: "pending",
      resultsCount: 0,
      startedAt: new Date().toISOString(),
    };

    setJobs((prev) => [newJob, ...prev]);
    setIsRunning(true);

    setTimeout(() => {
      setJobs((prev) =>
        prev.map((job) =>
          job.id === newJob.id ? { ...job, status: "running" } : job
        )
      );
    }, 500);

    setTimeout(() => {
      setJobs((prev) =>
        prev.map((job) =>
          job.id === newJob.id
            ? {
                ...job,
                status: "completed",
                resultsCount: Math.floor(Math.random() * maxResults) + 100,
                completedAt: new Date().toISOString(),
              }
            : job
        )
      );
      setIsRunning(false);
    }, 3000);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pending":
        return (
          <Badge variant="secondary" className="gap-1">
            <Clock className="h-3 w-3" />
            Pending
          </Badge>
        );
      case "running":
        return (
          <Badge className="gap-1 bg-blue-500 hover:bg-blue-600">
            <Loader2 className="h-3 w-3 animate-spin" />
            Running
          </Badge>
        );
      case "completed":
        return (
          <Badge className="gap-1 bg-emerald-500 hover:bg-emerald-600">
            <CheckCircle className="h-3 w-3" />
            Completed
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="destructive" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            Failed
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Adobe Stock Scraper</h1>
        <p className="text-muted-foreground">
          Scrape product data from Adobe Stock search results
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Scraper Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              New Scrape Job
            </CardTitle>
            <CardDescription>
              Enter a search query to scrape Adobe Stock results
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="query">Search Query</Label>
              <Input
                id="query"
                placeholder="e.g., minimalist home office"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="maxResults">Maximum Results</Label>
              <Input
                id="maxResults"
                type="number"
                min={50}
                max={2000}
                value={maxResults}
                onChange={(e) => setMaxResults(parseInt(e.target.value) || 500)}
              />
              <p className="text-xs text-muted-foreground">
                Recommended: 500-1000 for comprehensive data
              </p>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="scrapeDetails"
                checked={scrapeDetails}
                onChange={(e) => setScrapeDetails(e.target.checked)}
                className="rounded border-gray-300"
              />
              <Label htmlFor="scrapeDetails" className="text-sm font-normal">
                Scrape keyword details (slower but more data)
              </Label>
            </div>

            <Button
              className="w-full gap-2"
              onClick={handleStartScrape}
              disabled={!query.trim() || isRunning}
            >
              {isRunning ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Scraping...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Start Scraping
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Instructions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Terminal className="h-5 w-5" />
              Command Line Usage
            </CardTitle>
            <CardDescription>
              Run the scraper from your terminal for more control
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg bg-muted p-4 font-mono text-sm">
              <p className="text-muted-foreground"># Install dependencies</p>
              <p>cd scraper && pip install -r requirements.txt</p>
              <br />
              <p className="text-muted-foreground"># Basic usage</p>
              <p>python adobe_stock_scraper.py "home office" -n 500</p>
              <br />
              <p className="text-muted-foreground"># With keyword details</p>
              <p>python adobe_stock_scraper.py "remote work" -n 200 --details</p>
              <br />
              <p className="text-muted-foreground"># Interactive mode</p>
              <p>python run_scraper.py</p>
            </div>

            <div className="text-sm text-muted-foreground space-y-2">
              <p>
                <strong>Tip:</strong> For best results, run the scraper from the
                command line. The web interface shows a preview of the workflow.
              </p>
              <p>
                Results are saved to <code>scraper/output/</code> as CSV and JSON
                files.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Jobs History */}
      {jobs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Scrape Jobs</CardTitle>
            <CardDescription>Recent scraping jobs and their status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between p-4 rounded-lg border"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{job.query}</p>
                      {getStatusBadge(job.status)}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Started: {new Date(job.startedAt).toLocaleString()}
                      {job.completedAt && (
                        <> • Completed: {new Date(job.completedAt).toLocaleString()}</>
                      )}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    {job.status === "running" && (
                      <div className="w-32">
                        <Progress value={45} className="h-2" />
                      </div>
                    )}
                    {job.status === "completed" && (
                      <>
                        <span className="text-sm font-medium">
                          {job.resultsCount} results
                        </span>
                        <Button variant="outline" size="sm" className="gap-1">
                          <Download className="h-4 w-4" />
                          Export
                        </Button>
                      </>
                    )}
                    {job.status === "failed" && (
                      <span className="text-sm text-destructive">{job.error}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {jobs.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No scrape jobs yet</h3>
            <p className="text-muted-foreground mb-4">
              Enter a search query above to start scraping Adobe Stock data
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
