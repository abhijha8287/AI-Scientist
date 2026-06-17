"use client";
import { useState, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getKnowledge, type Concept, type Relationship } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Loader2, Search, Network, ArrowRight } from "lucide-react";

const TYPE_COLORS: Record<string, string> = {
  method: "default",
  entity: "secondary",
  result: "success",
  hypothesis: "warning",
  material: "outline",
  disease: "destructive",
  protein: "default",
  algorithm: "secondary",
  drug: "warning",
  gene: "success",
  pathway: "outline",
  other: "secondary",
};

function KnowledgeContent() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job_id") ?? undefined;
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [activeTab, setActiveTab] = useState<"concepts" | "relationships">("concepts");

  const { data, isLoading } = useQuery({
    queryKey: ["knowledge", jobId],
    queryFn: () => getKnowledge(jobId),
  });

  const concepts = data?.concepts ?? [];
  const relationships = data?.relationships ?? [];

  const conceptTypes = useMemo(() => {
    const types = new Set(concepts.map((c) => c.type));
    return ["all", ...Array.from(types)];
  }, [concepts]);

  const filteredConcepts = useMemo(() => {
    return concepts.filter((c) => {
      const matchSearch = !search || c.name.toLowerCase().includes(search.toLowerCase()) || c.context?.toLowerCase().includes(search.toLowerCase());
      const matchType = typeFilter === "all" || c.type === typeFilter;
      return matchSearch && matchType;
    });
  }, [concepts, search, typeFilter]);

  const filteredRels = useMemo(() => {
    return relationships.filter((r) => {
      if (!search) return true;
      const q = search.toLowerCase();
      return r.subject.toLowerCase().includes(q) || r.object.toLowerCase().includes(q) || r.predicate.toLowerCase().includes(q);
    });
  }, [relationships, search]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold">Knowledge Map</h1>
        <p className="text-muted-foreground text-sm">
          {concepts.length} concepts · {relationships.length} relationships extracted from papers
        </p>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48 max-w-xs">
          <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search concepts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
        <div className="flex gap-1 flex-wrap">
          {conceptTypes.slice(0, 8).map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                typeFilter === t
                  ? "bg-primary text-primary-foreground border-primary"
                  : "border-border text-muted-foreground hover:text-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="flex border border-border rounded-md overflow-hidden ml-auto">
          <button
            onClick={() => setActiveTab("concepts")}
            className={`px-3 py-1.5 text-sm ${activeTab === "concepts" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-secondary"}`}
          >
            Concepts
          </button>
          <button
            onClick={() => setActiveTab("relationships")}
            className={`px-3 py-1.5 text-sm border-l border-border ${activeTab === "relationships" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-secondary"}`}
          >
            Relationships
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : (
        <>
          {activeTab === "concepts" && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {filteredConcepts.length === 0 ? (
                <div className="col-span-3 py-16 text-center text-muted-foreground">
                  <Network className="w-10 h-10 mx-auto mb-3 opacity-30" />
                  <p>No concepts found{search ? ` for "${search}"` : ""}.</p>
                </div>
              ) : (
                filteredConcepts.map((c: Concept) => (
                  <Card key={c.id} className="hover:border-border/80 transition-colors">
                    <CardContent className="pt-4 pb-3 space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <p className="font-medium text-sm leading-tight">{c.name}</p>
                        <Badge
                          variant={(TYPE_COLORS[c.type] ?? "secondary") as "default" | "secondary" | "outline" | "destructive" | "success" | "warning"}
                          className="shrink-0 text-[10px]"
                        >
                          {c.type}
                        </Badge>
                      </div>
                      {c.context && (
                        <p className="text-xs text-muted-foreground leading-snug">{c.context}</p>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          )}

          {activeTab === "relationships" && (
            <div className="space-y-2">
              {filteredRels.length === 0 ? (
                <div className="py-16 text-center text-muted-foreground">
                  <Network className="w-10 h-10 mx-auto mb-3 opacity-30" />
                  <p>No relationships found.</p>
                </div>
              ) : (
                filteredRels.map((r: Relationship) => (
                  <div
                    key={r.id}
                    className="flex items-center gap-2 p-3 rounded-lg border border-border bg-card hover:bg-secondary/30 transition-colors"
                  >
                    <span className="text-sm font-medium text-foreground bg-secondary px-2 py-0.5 rounded">
                      {r.subject}
                    </span>
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <ArrowRight className="w-3 h-3" />
                      <span className="text-xs italic">{r.predicate}</span>
                      <ArrowRight className="w-3 h-3" />
                    </div>
                    <span className="text-sm font-medium text-foreground bg-secondary px-2 py-0.5 rounded">
                      {r.object}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}

          <p className="text-xs text-muted-foreground text-right">
            Showing {activeTab === "concepts" ? filteredConcepts.length : filteredRels.length} of{" "}
            {activeTab === "concepts" ? concepts.length : relationships.length} items
          </p>
        </>
      )}
    </div>
  );
}

export default function KnowledgePage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-32"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>}>
      <KnowledgeContent />
    </Suspense>
  );
}
