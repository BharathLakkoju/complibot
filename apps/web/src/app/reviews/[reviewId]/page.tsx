"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { FindingCard } from "@/components/FindingCard";
import { useAuthSession } from "@/hooks/useAuthSession";
import { useReviewSocket } from "@/hooks/useReviewSocket";
import { apiFetch } from "@/lib/api";
import { mergeFindingMaps } from "@/lib/mergeFindings";
import type { Finding } from "@/lib/types";

export default function ReviewPage() {
  const params = useParams();
  const reviewId = String(params.reviewId);
  const { token, user, signOut, ready } = useAuthSession(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [highlight, setHighlight] = useState<{ start: number; end: number } | null>(null);
  const highlightRef = useRef<HTMLElement>(null);
  const { state, setReviewStatus, submitDecision, clearDecisionError, disconnect } =
    useReviewSocket(reviewId, token);

  function handleSignOut() {
    disconnect();
    signOut();
  }

  const [bootFindings, setBootFindings] = useState<Finding[]>([]);
  const [restStatus, setRestStatus] = useState<string>("queued");

  useEffect(() => {
    if (!token) return;
    apiFetch<{ documents: Record<string, string>; findings: Finding[] }>(
      `/v1/reviews/${reviewId}/snapshot`,
      { token },
    ).then((snap) => {
      setBootFindings(snap.findings ?? []);
    });
    apiFetch<{ status: string }>(`/v1/reviews/${reviewId}`, { token }).then((r) => {
      setRestStatus(r.status);
      setReviewStatus(r.status);
    });
  }, [token, reviewId, setReviewStatus]);

  useEffect(() => {
    if (!token) return;
    const poll = window.setInterval(() => {
      apiFetch<{ status: string }>(`/v1/reviews/${reviewId}`, { token }).then((r) => {
        setRestStatus(r.status);
        if (state.reviewStatus === "queued" && r.status !== "queued") {
          setReviewStatus(r.status);
        }
      });
    }, 3000);
    return () => window.clearInterval(poll);
  }, [token, reviewId, setReviewStatus, state.reviewStatus]);

  const findings = useMemo(() => {
    const bootMap: Record<string, Finding> = {};
    for (const f of bootFindings) bootMap[f.id] = f;
    const merged = mergeFindingMaps(bootMap, state.findings);
    return merged.sort((a, b) => {
      const order = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
      return order[a.severity] - order[b.severity];
    });
  }, [state.findings, bootFindings]);

  const tallies = useMemo(() => {
    const counts = { accepted: 0, rejected: 0, open: 0, other: 0 };
    for (const f of findings) {
      if (f.status === "accepted") counts.accepted += 1;
      else if (f.status === "rejected") counts.rejected += 1;
      else if (f.status === "open") counts.open += 1;
      else counts.other += 1;
    }
    return counts;
  }, [findings]);

  const selected = findings.find((f) => f.id === selectedId) ?? findings[0];
  const docId = selected?.citations[0]?.documentId;
  const [docText, setDocText] = useState<Record<string, string>>({});
  const fullText = docId ? docText[docId] ?? "" : "";

  useEffect(() => {
    if (!token) return;
    apiFetch<{ documents: Record<string, string> }>(`/v1/reviews/${reviewId}/snapshot`, {
      token,
    }).then((snap) => setDocText(snap.documents));
  }, [token, reviewId]);

  useEffect(() => {
    if (highlight && highlightRef.current) {
      highlightRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [highlight, fullText]);

  const roleLoaded = state.role !== null;
  const canDecide = state.role === "owner" || state.role === "reviewer";
  const decisionsState: "loading" | "enabled" | "view_only" = !roleLoaded
    ? "loading"
    : canDecide
      ? "enabled"
      : "view_only";
  const displayStatus = state.reviewStatus !== "queued" ? state.reviewStatus : restStatus;

  useEffect(() => {
    if (!selected) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) return;
      if (e.key === "g" || e.key === "G") {
        const c = selected.citations[0];
        if (c) {
          setHighlight({ start: c.charStart, end: c.charEnd });
        }
      }
      if ((e.key === "a" || e.key === "A") && canDecide && selected.status === "open") {
        submitDecision(selected.id, "accept", selected.version);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected, submitDecision, canDecide]);

  if (!ready || !token) return null;

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] bg-[var(--surface)] px-4 py-3">
        <div>
          <Link href="/projects" className="text-xs text-[var(--text-muted)] underline">
            Projects
          </Link>
          <h1 className="text-lg font-semibold">Live review</h1>
          <p className="text-xs text-[var(--text-muted)]">
            Status: {displayStatus} · Accepted {tallies.accepted} · Rejected {tallies.rejected} ·
            Open {tallies.open} ·{" "}
            {state.connected ? "Connected" : "Reconnecting… changes are paused"}
          </p>
        </div>
        <div className="flex flex-col items-end gap-2 text-xs text-[var(--text-muted)]">
          {user && (
            <div className="flex items-center gap-2">
              <span>{user.email}</span>
              <button
                type="button"
                className="rounded border border-[var(--border-strong)] px-2 py-0.5"
                onClick={handleSignOut}
              >
                Sign out
              </button>
            </div>
          )}
          <p className="max-w-md text-right">Not legal advice. AI proposes; your team decides.</p>
        </div>
      </header>
      {state.decisionError && (
        <div
          className="flex items-center justify-between bg-[var(--critical-subtle)] px-4 py-2 text-sm text-[var(--critical)]"
          role="alert"
        >
          <span>{state.decisionError}</span>
          <button type="button" className="text-xs underline" onClick={clearDecisionError}>
            Dismiss
          </button>
        </div>
      )}
      {!state.connected && (
        <div className="bg-[var(--medium-subtle)] px-4 py-2 text-center text-sm">
          Reconnecting… changes are paused
        </div>
      )}
      <div className="grid flex-1 lg:grid-cols-2">
        <section className="min-h-[320px] border-r border-[var(--border)] p-4">
          <h2 className="mb-2 text-sm font-medium text-[var(--text-secondary)]">Document</h2>
          <pre className="max-h-[calc(100vh-8rem)] overflow-auto whitespace-pre-wrap rounded-md border border-[var(--border)] bg-[var(--surface)] p-4 text-sm leading-relaxed font-serif">
            {highlight && fullText ? (
              <>
                {fullText.slice(0, highlight.start)}
                <mark
                  ref={highlightRef}
                  className="rounded bg-[var(--medium-subtle)] ring-2 ring-[var(--accent)]"
                >
                  {fullText.slice(highlight.start, highlight.end)}
                </mark>
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
                decisionsState={decisionsState}
                onSelect={() => setSelectedId(f.id)}
                onShowInDoc={() => {
                  const c = f.citations[0];
                  if (c) {
                    setHighlight({ start: c.charStart, end: c.charEnd });
                  }
                }}
                onAccept={() => submitDecision(f.id, "accept", f.version)}
                onReject={(reason) => submitDecision(f.id, "reject", f.version, reason)}
              />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
