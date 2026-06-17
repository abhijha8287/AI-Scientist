"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { listJobs } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Lightbulb, ArrowRight, Clock } from "lucide-react";
import Link from "next/link";

export default function HypothesesIndexPage() {
  const router = useRouter();
  const { data, isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: listJobs,
  });

  const jobs = data?.jobs ?? [];
  const completedJobs = jobs.filter((j) => j.status === "complete");

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (completedJobs.length === 0) {
    return (
      <div className="max-w-xl mx-auto px-6 py-24 text-center space-y-4">
        <Lightbulb className="w-10 h-10 text-muted-foreground mx-auto" />
        <h2 className="text-xl font-semibold">No analyses yet</h2>
        <p className="text-muted-foreground text-sm">Upload papers and run the AI Scientist pipeline to see hypotheses.</p>
        <Button onClick={() => router.push("/")}>Upload Papers</Button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-10 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analysis Runs</h1>
        <p className="text-muted-foreground text-sm">Select a completed run to view hypotheses</p>
      </div>
      <div className="space-y-3">
        {completedJobs.map((job) => (
          <Link key={job.id} href={`/hypotheses/${job.id}`}>
            <Card className="hover:border-primary/50 transition-colors cursor-pointer">
              <CardContent className="flex items-center justify-between p-4">
                <div className="space-y-0.5">
                  <p className="text-sm font-medium">Job {job.id.slice(0, 8)}</p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Clock className="w-3 h-3" />
                    {new Date(job.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="success">{job.status}</Badge>
                  <ArrowRight className="w-4 h-4 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
