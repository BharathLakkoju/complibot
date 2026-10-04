"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setLoading(true);
    setError(null);
    try {
      const login = await apiFetch<{ accessToken: string }>("/v1/auth/dev-login", {
        method: "POST",
        body: JSON.stringify({ email: "demo@complibot.local", name: "Demo Analyst" }),
      });
      localStorage.setItem("cc_token", login.accessToken);
      const project = await apiFetch<{ id: string }>("/v1/projects", {
        method: "POST",
        token: login.accessToken,
        body: JSON.stringify({
          name: "Interview demo review",
          frameworkCodes: ["GDPR", "SOC2"],
        }),
      });
      const review = await apiFetch<{ id: string }>(`/v1/projects/${project.id}/demo`, {
        method: "POST",
        token: login.accessToken,
      });
      router.push(`/reviews/${review.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start demo");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-8 px-6 py-16">
      <div>
        <p className="text-sm font-medium text-[var(--accent-text)]">Portfolio MVP</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Compliance Review Copilot</h1>
        <p className="mt-3 text-[var(--text-secondary)]">
          Draft findings with machine-verified citations, decide together in real time, and export an
          audit-ready report. This environment uses synthetic sample contracts only.
        </p>
      </div>
      <div
        className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 text-sm text-[var(--text-secondary)]"
        role="note"
      >
        Demo only: use synthetic or public sample contracts. Don&apos;t upload real confidential data.
      </div>
      <button
        type="button"
        onClick={start}
        disabled={loading}
        className="inline-flex items-center justify-center rounded-md bg-[var(--accent)] px-5 py-3 text-sm font-medium text-[var(--accent-fg)] hover:bg-[var(--accent-hover)] disabled:opacity-60"
      >
        {loading ? "Starting sample review…" : "Try with a sample contract"}
      </button>
      {error && <p className="text-sm text-[var(--critical)]">{error}</p>}
      <p className="text-xs text-[var(--text-muted)]">
        Not legal advice. Findings describe what the reviewed text does or does not address.
      </p>
    </main>
  );
}
