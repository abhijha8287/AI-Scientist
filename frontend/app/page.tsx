"use client";
import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadPapers, listPapers, startPipeline, fetchFromWikipedia, type Paper } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Upload, FileText, FlaskConical, Loader2, CheckCircle2,
  AlertCircle, Play, Globe
} from "lucide-react";

export default function UploadPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [wikiTopic, setWikiTopic] = useState("");
  const [wikiFetching, setWikiFetching] = useState(false);
  const [wikiError, setWikiError] = useState<string | null>(null);

  const { data: papersData, isLoading } = useQuery({
    queryKey: ["papers"],
    queryFn: listPapers,
    refetchInterval: 5000,
  });

  const papers = papersData?.papers ?? [];

  const handleFiles = useCallback(async (files: FileList | File[]) => {
    const pdfs = Array.from(files).filter((f) => f.name.toLowerCase().endsWith(".pdf"));
    if (!pdfs.length) return;
    setUploading(true);
    setUploadError(null);
    try {
      const result = await uploadPapers(pdfs);
      queryClient.invalidateQueries({ queryKey: ["papers"] });
      result.papers.forEach((p) => {
        setSelectedIds((prev) => new Set(Array.from(prev).concat(p.id)));
      });
    } catch (e) {
      setUploadError((e as Error).message);
    } finally {
      setUploading(false);
    }
  }, [queryClient]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const onFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) handleFiles(e.target.files);
    e.target.value = "";
  };

  const handleWikiFetch = async () => {
    const topic = wikiTopic.trim();
    if (!topic) return;
    setWikiFetching(true);
    setWikiError(null);
    try {
      const result = await fetchFromWikipedia(topic);
      queryClient.invalidateQueries({ queryKey: ["papers"] });
      result.papers.forEach((p) => {
        setSelectedIds((prev) => new Set(Array.from(prev).concat(p.id)));
      });
      setWikiTopic("");
    } catch (e) {
      setWikiError((e as Error).message);
    } finally {
      setWikiFetching(false);
    }
  };

  const startMutation = useMutation({
    mutationFn: () => startPipeline([...selectedIds]),
    onSuccess: (data) => router.push(`/pipeline/${data.job_id}`),
  });

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(Array.from(prev));
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const statusColor = (s: string) => {
    if (s === "processed") return "success";
    if (s === "parse_failed") return "destructive";
    return "secondary";
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
      {/* Hero */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary/10 mb-2">
          <FlaskConical className="w-7 h-7 text-primary" />
        </div>
        <h1 className="text-3xl font-bold tracking-tight">AI Scientist</h1>
        <p className="text-muted-foreground max-w-md mx-auto">
          Upload research papers. The AI reads them, finds gaps nobody studied,
          generates hypotheses, and designs experiments.
        </p>
      </div>

      {/* Upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
          dragging
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50 hover:bg-secondary/30"
        }`}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={onFileInput}
        />
        {uploading ? (
          <div className="flex flex-col items-center gap-2 text-muted-foreground">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <span>Uploading papers...</span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 text-muted-foreground">
            <Upload className="w-8 h-8" />
            <p className="font-medium text-foreground">Drop PDF papers here</p>
            <p className="text-sm">or click to browse — multiple files supported</p>
          </div>
        )}
      </div>

      {uploadError && (
        <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span><strong>Upload failed:</strong> {uploadError}</span>
        </div>
      )}

      {/* Wikipedia topic input */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-blue-500" />
            <CardTitle className="text-base">Fetch from Wikipedia</CardTitle>
          </div>
          <CardDescription>
            Enter a research topic — the app fetches the Wikipedia article plus related articles and runs the same pipeline on them.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <input
              type="text"
              value={wikiTopic}
              onChange={(e) => setWikiTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleWikiFetch()}
              placeholder="e.g. quantum computing, CRISPR, transformer neural network…"
              className="flex-1 px-3 py-2 text-sm rounded-md border border-input bg-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={wikiFetching}
            />
            <Button onClick={handleWikiFetch} disabled={wikiFetching || !wikiTopic.trim()} className="gap-2">
              {wikiFetching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />}
              {wikiFetching ? "Fetching…" : "Fetch Articles"}
            </Button>
          </div>
          {wikiError && (
            <div className="flex items-center gap-2 mt-3 p-2 bg-destructive/10 border border-destructive/20 rounded-md text-destructive text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{wikiError}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Papers list */}
      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      ) : papers.length > 0 ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Uploaded Papers</CardTitle>
                <CardDescription>
                  Select papers to include in the next analysis run
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={() => setSelectedIds(new Set(papers.map((p) => p.id)))}>
                  Select all
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setSelectedIds(new Set())}>
                  Clear
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {papers.map((paper: Paper) => (
              <div
                key={paper.id}
                onClick={() => toggleSelect(paper.id)}
                className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedIds.has(paper.id)
                    ? "border-primary/50 bg-primary/5"
                    : "border-border hover:border-border/80 hover:bg-secondary/30"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded border flex items-center justify-center ${
                    selectedIds.has(paper.id) ? "bg-primary border-primary" : "border-muted-foreground"
                  }`}>
                    {selectedIds.has(paper.id) && <CheckCircle2 className="w-3 h-3 text-primary-foreground" />}
                  </div>
                  {paper.source === "wikipedia" ? (
                    <Globe className="w-4 h-4 text-blue-500 shrink-0" />
                  ) : (
                    <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
                  )}
                  <span className="text-sm font-medium truncate max-w-xs">{paper.filename}</span>
                </div>
                <div className="flex items-center gap-2">
                  {paper.source === "wikipedia" && (
                    <Badge variant="outline" className="text-blue-500 border-blue-300 text-xs">W</Badge>
                  )}
                  <Badge variant={statusColor(paper.status) as "success" | "destructive" | "secondary"}>
                    {paper.status}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {new Date(paper.uploaded_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {/* Run button */}
      {selectedIds.size > 0 && (
        <div className="flex items-center justify-between p-4 bg-primary/5 border border-primary/20 rounded-xl">
          <div>
            <p className="font-medium">{selectedIds.size} paper{selectedIds.size > 1 ? "s" : ""} selected</p>
            <p className="text-sm text-muted-foreground">
              The AI will extract knowledge, detect gaps, and generate hypotheses
            </p>
          </div>
          <Button
            size="lg"
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending}
            className="gap-2"
          >
            {startMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Run AI Scientist
          </Button>
        </div>
      )}

      {startMutation.isError && (
        <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {(startMutation.error as Error).message}
        </div>
      )}
    </div>
  );
}
