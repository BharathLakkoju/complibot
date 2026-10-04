"use client";

import type { Finding } from "@/lib/types";

const severityClass: Record<string, string> = {
  critical: "border-l-4 border-l-[var(--critical)] bg-[var(--critical-subtle)]",
  high: "border-l-4 border-l-[var(--high)] bg-[var(--high-subtle)]",
  medium: "border-l-4 border-l-[var(--medium)] bg-[var(--medium-subtle)]",
  low: "border-l-4 border-l-[var(--low)] bg-[var(--low-subtle)]",
  info: "border-l-4 border-l-[var(--border-strong)] bg-[var(--surface-2)]",
};

export function FindingCard({
  finding,
  selected,
  onSelect,
  onShowInDoc,
  onAccept,
  lowConfidence,
}: {
  finding: Finding;
  selected: boolean;
  onSelect: () => void;
  onShowInDoc: () => void;
  onAccept: () => void;
  lowConfidence: boolean;
}) {
  return (
    <article
      className={`rounded-md border p-3 ${selected ? "border-[var(--accent)]" : "border-[var(--border)]"} ${
        severityClass[finding.severity] ?? severityClass.info
      } ${lowConfidence ? "border-dashed" : ""}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onSelect()}
    >
      <header className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
            {finding.framework} · {finding.controlRef}
          </p>
          <h3 className="mt-1 text-sm font-semibold">{finding.title}</h3>
        </div>
        <span className="rounded px-2 py-0.5 text-xs font-medium capitalize">{finding.severity}</span>
      </header>
      <p className="mt-2 text-xs text-[var(--text-secondary)]">
        Confidence: {finding.confidence.band} — {finding.confidence.reason}
        {!finding.confidence.calibrated && " (uncalibrated estimate)"}
      </p>
      {lowConfidence && (
        <p className="mt-1 text-xs font-medium text-[var(--high)]">Needs careful review</p>
      )}
      <div className="mt-2 rounded bg-[var(--ai-tint)] p-2 text-sm text-[var(--text-secondary)]">
        {finding.rationale}
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded border border-[var(--border-strong)] px-2 py-1 text-xs"
          onClick={(e) => {
            e.stopPropagation();
            onShowInDoc();
          }}
        >
          Show in document (G)
        </button>
        <button
          type="button"
          className="rounded bg-[var(--success)] px-2 py-1 text-xs text-white disabled:opacity-40"
          disabled={finding.status !== "open"}
          onClick={(e) => {
            e.stopPropagation();
            onAccept();
          }}
        >
          Accept (A)
        </button>
        <span className="text-xs capitalize text-[var(--text-muted)]">{finding.status}</span>
      </div>
    </article>
  );
}
