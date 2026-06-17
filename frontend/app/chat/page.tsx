"use client";
import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { sendChat, getChatHistory, listJobs, type ChatMessage } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { MessageCircle, Send, Loader2, FlaskConical, Bot, User } from "lucide-react";

const SUGGESTIONS = [
  "What research gaps did you find?",
  "Which hypothesis has the highest novelty score?",
  "Explain the mechanism behind hypothesis #1",
  "What experiment would you recommend starting with?",
  "Why was this gap identified as the top priority?",
  "What are the main risks in the top hypothesis?",
];

function ChatContent() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job_id") ?? undefined;
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Array<{ role: "user" | "ai"; text: string }>>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: jobsData } = useQuery({
    queryKey: ["jobs"],
    queryFn: listJobs,
  });

  const { data: historyData } = useQuery({
    queryKey: ["chat-history", jobId],
    queryFn: () => getChatHistory(jobId),
    enabled: true,
    staleTime: 0,
  });

  useEffect(() => {
    if (historyData?.history) {
      const loaded = historyData.history.flatMap((m: ChatMessage) => [
        { role: "user" as const, text: m.query },
        { role: "ai" as const, text: m.response },
      ]);
      setMessages(loaded);
    }
  }, [historyData]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMutation = useMutation({
    mutationFn: (query: string) => sendChat(query, jobId),
    onMutate: (query) => {
      setMessages((prev) => [...prev, { role: "user", text: query }]);
      setInput("");
    },
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { role: "ai", text: data.response }]);
    },
    onError: (err) => {
      setMessages((prev) => [...prev, { role: "ai", text: `Error: ${(err as Error).message}` }]);
    },
  });

  const submit = () => {
    if (!input.trim() || sendMutation.isPending) return;
    sendMutation.mutate(input.trim());
  };

  const jobs = jobsData?.jobs ?? [];
  const activeJob = jobs.find((j) => j.id === jobId) ?? jobs[0];

  return (
    <div className="max-w-3xl mx-auto px-6 py-10 space-y-6 h-[calc(100vh-3.5rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div className="space-y-0.5">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <MessageCircle className="w-5 h-5 text-primary" />
            Chat with AI Scientist
          </h1>
          {activeJob && (
            <p className="text-xs text-muted-foreground">
              Context: job {activeJob.id.slice(0, 8)} · {activeJob.status}
            </p>
          )}
        </div>
        {!jobId && jobs.length > 0 && (
          <Badge variant="outline" className="text-xs">
            Using latest analysis
          </Badge>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 min-h-0">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 py-8">
            <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center">
              <FlaskConical className="w-7 h-7 text-primary" />
            </div>
            <div className="space-y-1">
              <p className="font-semibold">Ask the AI Scientist anything</p>
              <p className="text-sm text-muted-foreground max-w-sm">
                The AI has read your papers, identified gaps, and generated hypotheses.
                Ask it to explain its reasoning.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-md">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => { setInput(s); }}
                  className="text-left text-xs p-2.5 rounded-lg border border-border hover:border-primary/50 hover:bg-primary/5 transition-colors text-muted-foreground"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role === "ai" && (
                <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5 text-primary" />
                </div>
              )}
              <div className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
                m.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-card border border-border"
              }`}>
                {m.text}
              </div>
              {m.role === "user" && (
                <div className="w-7 h-7 rounded-full bg-secondary flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-3.5 h-3.5 text-muted-foreground" />
                </div>
              )}
            </div>
          ))
        )}
        {sendMutation.isPending && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <Bot className="w-3.5 h-3.5 text-primary" />
            </div>
            <div className="bg-card border border-border rounded-xl px-4 py-2.5">
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2 shrink-0">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about research gaps, hypotheses, mechanisms..."
          rows={2}
          className="resize-none"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
        />
        <Button
          onClick={submit}
          disabled={!input.trim() || sendMutation.isPending}
          size="icon"
          className="h-auto aspect-square self-stretch"
        >
          {sendMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-32"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>}>
      <ChatContent />
    </Suspense>
  );
}
