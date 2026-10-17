"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { useAuthSession } from "@/hooks/useAuthSession";
import { apiFetch } from "@/lib/api";
import type { Project } from "@/lib/types";

const FRAMEWORKS = ["GDPR", "SOC2", "ISO27001", "HIPAA"] as const;

export default function ProjectsPage() {
  const router = useRouter();
  const { token, ready } = useAuthSession(true);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [frameworks, setFrameworks] = useState<string[]>(["GDPR"]);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!token) return;
    apiFetch<Project[]>("/v1/projects", { token })
      .then(setProjects)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load projects"))
      .finally(() => setLoading(false));
  }, [token]);

  function toggleFramework(code: string) {
    setFrameworks((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code],
    );
  }

  async function createProject(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setCreating(true);
    setError(null);
    try {
      const project = await apiFetch<Project>("/v1/projects", {
        method: "POST",
        token,
        body: JSON.stringify({ name, frameworkCodes: frameworks }),
      });
      setProjects((p) => [project, ...p]);
      setName("");
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create project");
    } finally {
      setCreating(false);
    }
  }

  if (!ready || !token) return null;

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <AppHeader title="Projects" />

      <form
        onSubmit={createProject}
        className="mb-10 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4"
      >
        <h2 className="text-sm font-medium">New project</h2>
        <label className="mt-3 flex flex-col gap-1 text-sm">
          Name
          <input
            required
            className="rounded border border-[var(--border)] px-3 py-2"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <p className="mt-3 text-xs text-[var(--text-muted)]">Frameworks</p>
        <div className="mt-1 flex flex-wrap gap-2">
          {FRAMEWORKS.map((code) => (
            <button
              key={code}
              type="button"
              className={`rounded border px-2 py-1 text-xs ${
                frameworks.includes(code)
                  ? "border-[var(--accent)] bg-[var(--accent)] text-[var(--accent-fg)]"
                  : "border-[var(--border)]"
              }`}
              onClick={() => toggleFramework(code)}
            >
              {code}
            </button>
          ))}
        </div>
        <button
          type="submit"
          disabled={creating || !name || frameworks.length === 0}
          className="mt-4 rounded bg-[var(--accent)] px-4 py-2 text-sm text-[var(--accent-fg)] disabled:opacity-50"
        >
          {creating ? "Creating…" : "Create project"}
        </button>
      </form>

      {error && (
        <p className="mb-4 text-sm text-[var(--critical)]" role="alert">
          {error}
        </p>
      )}
      {loading && <p className="text-sm text-[var(--text-muted)]">Loading projects…</p>}
      {!loading && projects.length === 0 && (
        <p className="text-sm text-[var(--text-muted)]">No projects yet — create one above.</p>
      )}
      <ul className="flex flex-col gap-2">
        {projects.map((p) => (
          <li key={p.id}>
            <Link
              href={`/projects/${p.id}`}
              className="block rounded border border-[var(--border)] px-4 py-3 hover:border-[var(--accent)]"
            >
              <span className="font-medium">{p.name}</span>
              <span className="ml-2 text-xs text-[var(--text-muted)]">
                {p.frameworkCodes.join(", ")}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
