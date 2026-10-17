"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { useAuthSession } from "@/hooks/useAuthSession";
import { apiFetch, getApiUrl } from "@/lib/api";

type DocumentRow = {
  id: string;
  filename: string;
  status: string;
  createdAt: string;
};

export default function ProjectPage() {
  const params = useParams();
  const projectId = String(params.projectId);
  const router = useRouter();
  const { token, ready } = useAuthSession(true);
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [pasteError, setPasteError] = useState<string | null>(null);
  const [pasteTitle, setPasteTitle] = useState("gdpr-policy");
  const [pasteText, setPasteText] = useState(
    "The controller shall maintain a record of processing activities. Personal data may be transferred to sub-processors without prior notice.",
  );
  const [uploading, setUploading] = useState(false);
  const [startingReview, setStartingReview] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    apiFetch<DocumentRow[]>(`/v1/projects/${projectId}/documents`, { token })
      .then(setDocuments)
      .catch((e) => setDocumentsError(e instanceof Error ? e.message : "Failed to load documents"))
      .finally(() => setLoading(false));
  }, [projectId, token]);

  function loadDocs(t: string) {
    return apiFetch<DocumentRow[]>(`/v1/projects/${projectId}/documents`, { token: t }).then(
      setDocuments,
    );
  }

  async function pasteDocument(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setPasteError(null);
    try {
      await apiFetch(`/v1/projects/${projectId}/documents/paste`, {
        method: "POST",
        token,
        body: JSON.stringify({ title: pasteTitle, text: pasteText }),
      });
      await loadDocs(token);
    } catch (err) {
      setPasteError(err instanceof Error ? err.message : "Paste failed");
    }
  }

  async function onFileSelected(file: File) {
    if (!token) return;
    setUploading(true);
    setUploadError(null);
    try {
      const presign = await apiFetch<{ uploadUrl: string; documentId: string }>(
        `/v1/projects/${projectId}/documents/presign`,
        {
          method: "POST",
          token,
          body: JSON.stringify({
            filename: file.name,
            contentType: file.type || "text/plain",
            sizeBytes: file.size,
          }),
        },
      );
      const contentType = file.type || "text/plain";
      const put = await fetch(presign.uploadUrl, {
        method: "PUT",
        headers: { "Content-Type": contentType },
        body: file,
      });
      if (!put.ok) {
        const body = await put.text().catch(() => "");
        throw new Error(
          body.trim()
            ? `Upload to storage failed (${put.status}): ${body.slice(0, 200)}`
            : `Upload to storage failed (${put.status} ${put.statusText})`,
        );
      }
      await apiFetch(`/v1/documents/${presign.documentId}/complete`, {
        method: "POST",
        token,
      });
      await loadDocs(token);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function startReview(documentId: string) {
    if (!token) return;
    setStartingReview(documentId);
    setDocumentsError(null);
    try {
      const review = await apiFetch<{ id: string }>(`/v1/projects/${projectId}/reviews`, {
        method: "POST",
        token,
        body: JSON.stringify({ documentIds: [documentId] }),
      });
      router.push(`/reviews/${review.id}`);
    } catch (err) {
      setDocumentsError(err instanceof Error ? err.message : "Could not start review");
      setStartingReview(null);
    }
  }

  async function trySample() {
    if (!token) return;
    setDocumentsError(null);
    try {
      const review = await apiFetch<{ id: string }>(`/v1/projects/${projectId}/demo`, {
        method: "POST",
        token,
      });
      router.push(`/reviews/${review.id}`);
    } catch (err) {
      setDocumentsError(err instanceof Error ? err.message : "Sample failed");
    }
  }

  if (!ready || !token) return null;

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <Link href="/projects" className="text-sm text-[var(--text-muted)] underline">
        ← Projects
      </Link>
      <AppHeader title="Project documents" />
      <p className="-mt-4 text-xs text-[var(--text-muted)]">
        Demo only: use synthetic or public sample contracts.
      </p>

      <section className="mt-6 rounded-lg border border-[var(--border)] p-4">
        <h2 className="text-sm font-medium">Upload file</h2>
        <p className="mt-1 text-xs text-[var(--text-muted)]">
          PDF (text layer), DOCX, TXT · up to 10 MB via {getApiUrl()}
        </p>
        <input
          type="file"
          accept=".txt,.md,.pdf,.docx,text/plain,application/pdf"
          className="mt-3 text-sm"
          disabled={uploading}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onFileSelected(f);
          }}
        />
        {uploading && <p className="mt-2 text-xs">Uploading…</p>}
        {uploadError && (
          <p className="mt-2 text-sm text-[var(--critical)]" role="alert">
            {uploadError}
          </p>
        )}
      </section>

      <form onSubmit={pasteDocument} className="mt-6 rounded-lg border border-[var(--border)] p-4">
        <h2 className="text-sm font-medium">Paste text</h2>
        <label className="mt-2 flex flex-col gap-1 text-sm">
          Title
          <input
            className="rounded border border-[var(--border)] px-3 py-2"
            value={pasteTitle}
            onChange={(e) => setPasteTitle(e.target.value)}
          />
        </label>
        <label className="mt-2 flex flex-col gap-1 text-sm">
          Contract text
          <textarea
            className="min-h-[120px] rounded border border-[var(--border)] px-3 py-2 font-mono text-xs"
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
          />
        </label>
        <button
          type="submit"
          className="mt-3 rounded bg-[var(--accent)] px-4 py-2 text-sm text-[var(--accent-fg)]"
        >
          Save as document
        </button>
        {pasteError && (
          <p className="mt-2 text-sm text-[var(--critical)]" role="alert">
            {pasteError}
          </p>
        )}
      </form>

      <button
        type="button"
        onClick={trySample}
        className="mt-4 text-sm text-[var(--accent-text)] underline"
      >
        Try sample contract (demo endpoint)
      </button>

      <h2 className="mt-8 text-sm font-medium">Documents</h2>
      {documentsError && (
        <p className="mt-2 text-sm text-[var(--critical)]" role="alert">
          {documentsError}
        </p>
      )}
      {loading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
      {!loading && documents.length === 0 && (
        <p className="text-sm text-[var(--text-muted)]">No documents yet.</p>
      )}
      <ul className="mt-2 flex flex-col gap-2">
        {documents.map((d) => (
          <li
            key={d.id}
            className="flex items-center justify-between rounded border border-[var(--border)] px-4 py-3"
          >
            <div>
              <p className="font-medium text-sm">{d.filename}</p>
              <p className="text-xs text-[var(--text-muted)] capitalize">{d.status}</p>
            </div>
            <button
              type="button"
              disabled={d.status !== "parsed" || startingReview === d.id}
              className="rounded bg-[var(--accent)] px-3 py-1 text-xs text-[var(--accent-fg)] disabled:opacity-40"
              onClick={() => startReview(d.id)}
            >
              {startingReview === d.id ? "Starting…" : "Start review"}
            </button>
          </li>
        ))}
      </ul>
    </main>
  );
}
