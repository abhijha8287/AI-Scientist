"use client";
import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getPipelineResults, type Hypothesis, type Experiment } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Lightbulb, FlaskConical, ChevronDown, ChevronUp,
  Loader2, AlertCircle, MessageCircle, Beaker
} from "lucide-react";
import Link from "next/link";

function NoveltyBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = pct >= 70 ? "bg-emerald-500" : pct >= 40 ? "bg-amber-500" : "bg-primary";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 bg-secondary rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-muted-foreground w-8">{pct}%</span>
    </div>
  );
}

function ExperimentPanel({ exp }: { exp: Experiment }) {
  return (
    <div className="mt-4 p-4 bg-secondary/50 rounded-lg border border-border space-y-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-primary">
        <Beaker className="w-4 h-4" />
        Experiment Design
      </div>
      <div className="space-y-2 text-sm">
        <div>
          <span className="text-muted-foreground">Objective: </span>
          <span>{exp.objective}</span>
        </div>
        <div>
          <span className="text-muted-foreground font-medium">Methodology:</span>
          <p className="mt-1 text-sm whitespace-pre-line leading-relaxed">{exp.methodology}</p>
        </div>
        {exp.variables && (
          <div className="grid grid-cols-3 gap-3 mt-2">
            {Object.entries(exp.variables).map(([k, vals]) => (
              <div key={k} className="bg-background rounded p-2">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">{k}</p>
                {Array.isArray(vals) && vals.map((v, i) => (
                  <p key={i} className="text-xs">{v}</p>
                ))}
              </div>
            ))}
          </div>
        )}
        {exp.controls && (
          <div>
            <span className="text-muted-foreground">Controls: </span>
            <span className="text-sm">{exp.controls}</span>
          </div>
        )}
        {exp.metrics && exp.metrics.length > 0 && (
          <div>
            <p className="text-muted-foreground font-medium">Metrics:</p>
            <ul className="mt-1 space-y-0.5">
              {exp.metrics.map((m, i) => <li key={i} className="text-xs">• {m}</li>)}
            </ul>
          </div>
        )}
        {exp.criteria && (
          <div className="p-2 bg-primary/5 border border-primary/20 rounded text-xs">
            <span className="font-medium text-primary">Success criteria: </span>{exp.criteria}
          </div>
        )}
      </div>
    </div>
  );
}

function HypothesisCard({ h, defaultOpen }: { h: Hypothesis; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  const [showExp, setShowExp] = useState(false);
  const pct = Math.round(h.novelty_score * 100);

  return (
    <Card className={`transition-colors ${open ? "border-primary/30" : ""}`}>
      <CardHeader className="pb-3 cursor-pointer" onClick={() => setOpen(!open)}>
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant={pct >= 70 ? "success" : pct >= 40 ? "warning" : "default"}>
                {pct}% novel
              </Badge>
              {h.gap && (
                <Badge variant="outline" className="text-xs">
                  Gap: {h.gap.title}
                </Badge>
              )}
            </div>
            <CardTitle className="text-base leading-snug">{h.title}</CardTitle>
          </div>
          <div className="shrink-0 mt-1">
            {open ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
          </div>
        </div>
        <div className="w-48">
          <NoveltyBar score={h.novelty_score} />
        </div>
      </CardHeader>

      {open && (
        <CardContent className="space-y-4 pt-0">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">Reasoning</p>
            <p className="text-sm leading-relaxed">{h.reasoning}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">Mechanism</p>
            <p className="text-sm leading-relaxed font-medium text-foreground">{h.mechanism}</p>
          </div>
          {h.outcomes && h.outcomes.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wider">Expected Outcomes</p>
              <ul className="space-y-1">
                {h.outcomes.map((o, i) => (
                  <li key={i} className="text-sm flex gap-2">
                    <span className="text-primary mt-0.5">→</span>
                    <span>{o}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {h.risks && h.risks.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wider">Risk Factors</p>
              <ul className="space-y-1">
                {h.risks.map((r, i) => (
                  <li key={i} className="text-sm flex gap-2 text-muted-foreground">
                    <span className="text-amber-400 mt-0.5">⚠</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {h.experiment && (
            <Button variant="outline" size="sm" onClick={() => setShowExp(!showExp)} className="gap-2">
              <FlaskConical className="w-3.5 h-3.5" />
              {showExp ? "Hide" : "Show"} Experiment Design
            </Button>
          )}
          {showExp && h.experiment && <ExperimentPanel exp={h.experiment} />}
        </CardContent>
      )}
    </Card>
  );
}

export default function HypothesesPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const router = useRouter();
  const [sortBy, setSortBy] = useState<"novelty" | "rank">("novelty");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["results", jobId],
    queryFn: () => getPipelineResults(jobId),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-16 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-destructive mx-auto" />
        <p className="text-muted-foreground">Failed to load results.</p>
        <Button variant="outline" onClick={() => router.push("/")}>Back to Upload</Button>
      </div>
    );
  }

  const hypotheses = [...(data.hypotheses ?? [])].sort((a, b) => {
    if (sortBy === "novelty") return b.novelty_score - a.novelty_score;
    return (a.gap?.rank ?? 99) - (b.gap?.rank ?? 99);
  });

  const gaps = data.gaps ?? [];

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold">AI-Generated Hypotheses</h1>
          <p className="text-muted-foreground text-sm">
            {hypotheses.length} hypotheses from {gaps.length} research gaps · Job {jobId.slice(0, 8)}
          </p>
        </div>
        <Link href={`/chat?job_id=${jobId}`}>
          <Button variant="outline" size="sm" className="gap-2 shrink-0">
            <MessageCircle className="w-4 h-4" />
            Chat with AI Scientist
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Research Gaps", value: gaps.length, icon: "🔍" },
          { label: "Hypotheses", value: hypotheses.length, icon: "💡" },
          {
            label: "Top Novelty",
            value: hypotheses.length > 0
              ? `${Math.round(Math.max(...hypotheses.map((h) => h.novelty_score)) * 100)}%`
              : "—",
            icon: "✨"
          },
        ].map((s) => (
          <Card key={s.label}>
            <CardContent className="pt-5 pb-4 text-center">
              <p className="text-2xl mb-1">{s.icon}</p>
              <p className="text-2xl font-bold">{s.value}</p>
              <p className="text-xs text-muted-foreground">{s.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Sort */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Sort by:</span>
        <Button
          variant={sortBy === "novelty" ? "default" : "outline"}
          size="sm"
          onClick={() => setSortBy("novelty")}
        >Novelty Score</Button>
        <Button
          variant={sortBy === "rank" ? "default" : "outline"}
          size="sm"
          onClick={() => setSortBy("rank")}
        >Gap Priority</Button>
      </div>

      {/* Hypothesis cards */}
      {hypotheses.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Lightbulb className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">No hypotheses generated yet.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {hypotheses.map((h, i) => (
            <HypothesisCard key={h.id} h={h} defaultOpen={i === 0} />
          ))}
        </div>
      )}
    </div>
  );
}
