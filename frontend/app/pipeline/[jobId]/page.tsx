"use client";
import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getPipelineStatus } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  FileText, Brain, Search, Lightbulb, FlaskConical,
  CheckCircle2, Loader2, Clock, AlertCircle, ArrowRight
} from "lucide-react";

const NODES = [
  { key: "paper_reader", label: "Paper Reader", icon: FileText, desc: "Extracting text and chunking PDFs" },
  { key: "knowledge_extractor", label: "Knowledge Extractor", icon: Brain, desc: "Identifying concepts and relationships" },
  { key: "gap_detector", label: "Gap Detector", icon: Search, desc: "Analyzing what hasn't been studied" },
  { key: "hypothesis_generator", label: "Hypothesis Generator", icon: Lightbulb, desc: "Generating testable hypotheses" },
  { key: "experiment_designer", label: "Experiment Designer", icon: FlaskConical, desc: "Designing experimental protocols" },
];

const NODE_ORDER = NODES.map((n) => n.key);

function nodeStatus(currentNode: string, nodeKey: string, jobStatus: string) {
  if (jobStatus === "complete") return "done";
  if (jobStatus === "failed") {
    const currentIdx = NODE_ORDER.indexOf(currentNode);
    const nodeIdx = NODE_ORDER.indexOf(nodeKey);
    if (nodeIdx < currentIdx) return "done";
    if (nodeIdx === currentIdx) return "error";
    return "pending";
  }
  const currentIdx = NODE_ORDER.indexOf(currentNode === "done" ? "experiment_designer" : currentNode);
  const nodeIdx = NODE_ORDER.indexOf(nodeKey);
  if (nodeIdx < currentIdx) return "done";
  if (nodeIdx === currentIdx) return "running";
  return "pending";
}

export default function PipelinePage() {
  const { jobId } = useParams<{ jobId: string }>();
  const router = useRouter();

  const { data, isLoading } = useQuery({
    queryKey: ["pipeline-status", jobId],
    queryFn: () => getPipelineStatus(jobId),
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      if (s === "complete" || s === "failed") return false;
      return 2000;
    },
  });

  useEffect(() => {
    if (data?.status === "complete") {
      setTimeout(() => router.push(`/hypotheses/${jobId}`), 1500);
    }
  }, [data?.status, jobId, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const job = data!;
  const counts = job.counts || {};

  return (
    <div className="max-w-2xl mx-auto px-6 py-10 space-y-8">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold">Running AI Scientist Pipeline</h1>
        <p className="text-muted-foreground text-sm">Job {jobId.slice(0, 8)}...</p>
      </div>

      {/* Overall status */}
      <div className={`p-4 rounded-xl border ${
        job.status === "complete"
          ? "border-emerald-500/30 bg-emerald-500/5"
          : job.status === "failed"
          ? "border-destructive/30 bg-destructive/5"
          : "border-primary/30 bg-primary/5"
      }`}>
        <div className="flex items-center gap-3">
          {job.status === "complete" ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : job.status === "failed" ? (
            <AlertCircle className="w-5 h-5 text-destructive" />
          ) : (
            <Loader2 className="w-5 h-5 animate-spin text-primary" />
          )}
          <div>
            <p className="font-medium capitalize">{job.status === "complete" ? "Analysis complete — redirecting..." : job.status}</p>
            {job.error && <p className="text-sm text-destructive mt-1">{job.error}</p>}
          </div>
        </div>
      </div>

      {/* Pipeline nodes */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Pipeline Progress</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          {NODES.map((node, idx) => {
            const status = nodeStatus(job.current_node, node.key, job.status);
            const Icon = node.icon;
            return (
              <div key={node.key}>
                <div className={`flex items-center gap-4 p-3 rounded-lg ${
                  status === "running" ? "bg-primary/5 node-running border border-primary/20" : ""
                }`}>
                  <div className={`flex items-center justify-center w-9 h-9 rounded-full border-2 shrink-0 ${
                    status === "done"
                      ? "bg-emerald-500/10 border-emerald-500/50"
                      : status === "running"
                      ? "bg-primary/10 border-primary"
                      : status === "error"
                      ? "bg-destructive/10 border-destructive/50"
                      : "bg-secondary border-border"
                  }`}>
                    {status === "done" ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : status === "running" ? (
                      <Loader2 className="w-4 h-4 text-primary animate-spin" />
                    ) : status === "error" ? (
                      <AlertCircle className="w-4 h-4 text-destructive" />
                    ) : (
                      <Icon className="w-4 h-4 text-muted-foreground" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className={`text-sm font-medium ${
                        status === "pending" ? "text-muted-foreground" : "text-foreground"
                      }`}>{node.label}</p>
                      {status === "running" && (
                        <Badge variant="default" className="text-[10px] py-0">running</Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">{node.desc}</p>
                  </div>
                  <div className="text-right shrink-0">
                    {Object.entries(counts)
                      .filter(([k]) => !["status"].includes(k))
                      .map(([k, v]) => status === "running" || status === "done" ? (
                        <p key={k} className="text-xs text-muted-foreground">
                          {k}: <span className="text-foreground font-medium">{String(v)}</span>
                        </p>
                      ) : null)}
                  </div>
                </div>
                {idx < NODES.length - 1 && (
                  <div className="ml-[1.625rem] w-px h-4 bg-border" />
                )}
              </div>
            );
          })}
        </CardContent>
      </Card>

      {job.status === "complete" && (
        <Button onClick={() => router.push(`/hypotheses/${jobId}`)} className="w-full gap-2">
          View Hypotheses <ArrowRight className="w-4 h-4" />
        </Button>
      )}

      {job.status === "failed" && (
        <Button variant="outline" onClick={() => router.push("/")} className="w-full">
          Back to Upload
        </Button>
      )}
    </div>
  );
}
