"use client";

import Link from "next/link";
import { useAuthSession } from "@/hooks/useAuthSession";

export function AppHeader({ title }: { title?: string }) {
  const { user, isSignedIn, signOut, ready } = useAuthSession();

  return (
    <header className="mb-8 flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] pb-4">
      <div className="flex items-center gap-4">
        {title ? <h1 className="text-2xl font-semibold">{title}</h1> : null}
        <Link href="/" className="text-sm text-[var(--text-muted)] underline">
          Home
        </Link>
        {isSignedIn && (
          <Link href="/projects" className="text-sm text-[var(--text-muted)] underline">
            Projects
          </Link>
        )}
      </div>
      {ready && isSignedIn && user && (
        <div className="flex items-center gap-3 text-sm">
          <span className="text-[var(--text-secondary)]">{user.email}</span>
          <button
            type="button"
            onClick={signOut}
            className="rounded border border-[var(--border-strong)] px-3 py-1 text-xs"
          >
            Sign out
          </button>
        </div>
      )}
    </header>
  );
}
