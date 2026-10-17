"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuthSession } from "@/hooks/useAuthSession";
import { apiFetch } from "@/lib/api";
import { setStoredAuthToken } from "@/lib/authToken";

export default function HomePage() {
  const router = useRouter();
  const { isSignedIn, ready, user } = useAuthSession();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function trySample() {
    setLoading(true);
    setError(null);
    try {
      const login = await apiFetch<{ accessToken: string }>("/v1/auth/dev-login", {
        method: "POST",
        body: JSON.stringify({ email: "demo@complibot.local", name: "Demo Analyst" }),
      });
      setStoredAuthToken(login.accessToken);
      const project = await apiFetch<{ id: string }>("/v1/projects", {
        method: "POST",
        token: login.accessToken,
        body: JSON.stringify({
          name: "Sample review",
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
        <h1 className="text-3xl font-semibold tracking-tight">Compliance Review Copilot</h1>
        <p className="mt-3 text-[var(--text-secondary)]">
          Draft findings with machine-verified citations, decide together in real time, and export an
          audit-ready report. Use synthetic or sample contracts in demo environments.
        </p>
      </div>
      <div
        className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 text-sm text-[var(--text-secondary)]"
        role="note"
      >
        Demo only: use synthetic or public sample contracts. Don&apos;t upload real confidential data.
      </div>
      {ready && isSignedIn && user ? (
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-sm text-[var(--text-secondary)]">Signed in as {user.email}</p>
          <Link
            href="/projects"
            className="inline-flex items-center justify-center rounded-md bg-[var(--accent)] px-5 py-3 text-sm font-medium text-[var(--accent-fg)] hover:bg-[var(--accent-hover)]"
          >
            Go to projects
          </Link>
        </div>
      ) : (
        <div className="flex flex-wrap gap-3">
          <Link
            href="/login"
            className="inline-flex items-center justify-center rounded-md bg-[var(--accent)] px-5 py-3 text-sm font-medium text-[var(--accent-fg)] hover:bg-[var(--accent-hover)]"
          >
            Sign in
          </Link>
          <Link
            href="/login?mode=register"
            className="inline-flex items-center justify-center rounded-md border border-[var(--border-strong)] px-5 py-3 text-sm font-medium"
          >
            Create account
          </Link>
        </div>
      )}
      <button
        type="button"
        onClick={trySample}
        disabled={loading}
        className="text-left text-sm text-[var(--accent-text)] underline disabled:opacity-60"
      >
        {loading ? "Starting sample review…" : "Try sample without an account (dev login)"}
      </button>
      {error && <p className="text-sm text-[var(--critical)]">{error}</p>}
      <p className="text-xs text-[var(--text-muted)]">
        Not legal advice. Findings describe what the reviewed text does or does not address.
      </p>
    </main>
  );
}
