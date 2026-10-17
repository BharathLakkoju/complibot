"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Me = { email: string; name: string | null };

export function useAuthSession(requireAuth = false) {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(() =>
    typeof window !== "undefined" ? localStorage.getItem("cc_token") : null,
  );
  const [user, setUser] = useState<Me | null>(null);
  const [authChecked, setAuthChecked] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("cc_token") === null;
  });

  useEffect(() => {
    if (!token) {
      if (requireAuth) {
        router.replace("/login");
      }
      return;
    }
    let cancelled = false;
    apiFetch<Me>("/v1/auth/me", { token })
      .then((me) => {
        if (!cancelled) setUser(me);
      })
      .catch(() => {
        if (cancelled) return;
        localStorage.removeItem("cc_token");
        setToken(null);
        if (requireAuth) {
          router.replace("/login");
        }
      })
      .finally(() => {
        if (!cancelled) setAuthChecked(true);
      });
    return () => {
      cancelled = true;
    };
  }, [requireAuth, router, token]);

  const signOut = useCallback(() => {
    localStorage.removeItem("cc_token");
    setToken(null);
    setUser(null);
    setAuthChecked(true);
    router.push("/login");
  }, [router]);

  const ready = token === null || authChecked;

  return { token, user, ready, signOut, isSignedIn: Boolean(token && user) };
}
