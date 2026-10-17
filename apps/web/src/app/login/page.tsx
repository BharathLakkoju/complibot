"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "@/lib/api";

type AuthResponse = { accessToken: string };

export default function LoginPage() {
  const router = useRouter();
  const [mode] = useState<"login" | "register">(() =>
    typeof window !== "undefined" && window.location.search.includes("mode=register")
      ? "register"
      : "login",
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const path = mode === "register" ? "/v1/auth/register" : "/v1/auth/login";
      const body =
        mode === "register"
          ? { email, password, name: name || undefined }
          : { email, password };
      const res = await apiFetch<AuthResponse>(path, {
        method: "POST",
        body: JSON.stringify(body),
      });
      localStorage.setItem("cc_token", res.accessToken);
      router.push("/projects");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-6 py-16">
      <div>
        <h1 className="text-2xl font-semibold">
          {mode === "register" ? "Create account" : "Sign in"}
        </h1>
        <p className="mt-2 text-sm text-[var(--text-secondary)]">
          Email and password access to your compliance review projects.
        </p>
      </div>
      <form className="flex flex-col gap-4" onSubmit={submit}>
        {mode === "register" && (
          <label className="flex flex-col gap-1 text-sm">
            Name
            <input
              className="rounded border border-[var(--border)] px-3 py-2"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
            />
          </label>
        )}
        <label className="flex flex-col gap-1 text-sm">
          Email
          <input
            type="email"
            required
            className="rounded border border-[var(--border)] px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Password
          <input
            type="password"
            required
            minLength={8}
            className="rounded border border-[var(--border)] px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === "register" ? "new-password" : "current-password"}
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-[var(--accent)] px-4 py-2 text-sm font-medium text-[var(--accent-fg)] disabled:opacity-60"
        >
          {loading ? "Please wait…" : mode === "register" ? "Create account" : "Sign in"}
        </button>
      </form>
      {error && <p className="text-sm text-[var(--critical)]" role="alert">{error}</p>}
      <p className="text-sm text-[var(--text-muted)]">
        {mode === "register" ? (
          <>
            Already have an account?{" "}
            <Link href="/login" className="text-[var(--accent-text)] underline">
              Sign in
            </Link>
          </>
        ) : (
          <>
            New here?{" "}
            <Link href="/login?mode=register" className="text-[var(--accent-text)] underline">
              Create account
            </Link>
          </>
        )}
      </p>
      <Link href="/" className="text-xs text-[var(--text-muted)] underline">
        Back to home
      </Link>
    </main>
  );
}
