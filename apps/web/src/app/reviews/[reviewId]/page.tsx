"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { FindingCard } from "@/components/FindingCard";
import { useReviewSocket } from "@/hooks/useReviewSocket";
import { apiFetch } from "@/lib/api";
import type { Finding } from "@/lib/types";

export default function ReviewPage() {
  const params = useParams();
  const reviewId = String(params.reviewId);
  const [token, setToken] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [highlight, setHighlight] = useState<{ start: number; end: number } | null>(null);
  const [citationOpened, setCitationOpened] = useState<Record<string, boolean>>({});
  const { state, docText, setDocText, submitDecision } = useReviewSocket(reviewId, token);

  useEffect(() => {
    setToken(localStorage.getItem("cc_token"));
  }, []);

  const [bootFindings, setBootFindings] = useState<Finding[]>([]);

  useEffect(() => {
    if (!token) return;
    apiFetch<{ documents: Record<string, string>; findings: Finding[] }>(
      `/v1/reviews/${reviewId}/snapshot`,
      { token },
    ).then((snap) => {
      setDocText(snap.documents);
      setBootFindings(snap.findings ?? []);
    });
    apiFetch<Finding[]>(`/v1/reviews/${reviewId}/findings`, { token }).then(setBootFindings);
  }, [token, reviewId, setDocText]);

  const findings = useMemo(() => {
    const merged = { ...state.findings };
    for (const f of bootFindings) merged[f.id] = f;
    return Object.values(merged).sort((a, b) => {
      const order = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
      return order[a.severity] - order[b.severity];
    });
  }, [state.findings, bootFindings]);

  const selected = findings.find((f) => f.id === selectedId) ?? findings[0];
  const docId = selected?.citations[0]?.documentId;
  const fullText = docId ? docText[docId] ?? "" : "";

  useEffect(() => {
    if (!selected) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "g" || e.key === "G") {
        const c = selected.citations[0];
        if (c) {
          setHighlight({ start: c.charStart, end: c.charEnd });
          setCitationOpened((m) => ({ ...m, [selected.id]: true }));
        }
      }
      if (e.key === "a" || e.key === "A") {
        if (citationOpened[selected.id]) {
          submitDecision(selected.id, "accept", selected.version);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected, citationOpened, submitDecision]);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface)] px-4 py-3">
        <div>
          <h1 className="text-lg font-semibold">Live review</h1>
          <p className="text-xs text-[var(--text-muted)]">
            Status: {state.reviewStatus} · {state.connected ? "Connected" : "Reconnecting… changes are paused"}
          </p>
        </div>
        <p className="max-w-md text-right text-xs text-[var(--text-muted)]">
          Not legal advice. AI proposes; your team decides.
        </p>
      </header>
      {!state.connected && (
        <div className="bg-[var(--medium-subtle)] px-4 py-2 text-center text-sm">
          Reconnecting… changes are paused
        </div>
      )}
      <div className="grid flex-1 lg:grid-cols-2">
        <section className="min-h-[320px] border-r border-[var(--border)] p-4">
          <h2 className="mb-2 text-sm font-medium text-[var(--text-secondary)]">Document</h2>
          <pre className="max-h-[calc(100vh-8rem)] overflow-auto whitespace-pre-wrap rounded-md border border-[var(--border)] bg-[var(--surface)] p-4 text-sm leading-relaxed">
            {highlight && fullText ? (
              <>
                {fullText.slice(0, highlight.start)}
                <mark className="bg-[var(--medium-subtle)]">{fullText.slice(highlight.start, highlight.end)}</mark>
                {fullText.slice(highlight.end)}
              </>
            ) : (
              fullText || "Loading document text…"
            )}
          </pre>
        </section>
        <section className="flex flex-col gap-3 p-4">
          <h2 className="text-sm font-medium text-[var(--text-secondary)]">Findings</h2>
          <div className="flex flex-col gap-3 overflow-y-auto">
            {findings.length === 0 && (
              <p className="text-sm text-[var(--text-muted)]">Waiting for verified findings…</p>
            )}
            {findings.map((f) => (
              <FindingCard
                key={f.id}
                finding={f}
                selected={f.id === (selectedId ?? findings[0]?.id)}
                lowConfidence={f.confidence.band === "low"}
                onSelect={() => setSelectedId(f.id)}
                onShowInDoc={() => {
                  const c = f.citations[0];
                  if (c) {
                    setHighlight({ start: c.charStart, end: c.charEnd });
                    setCitationOpened((m) => ({ ...m, [f.id]: true }));
                  }
                }}
                onAccept={() => {
                  if (citationOpened[f.id]) {
                    submitDecision(f.id, "accept", f.version);
                  }
                }}
              />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
