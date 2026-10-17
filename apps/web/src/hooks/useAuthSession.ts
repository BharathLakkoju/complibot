"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { clearStoredAuthToken, getStoredAuthToken } from "@/lib/authToken";

type Me = { email: string; name: string | null };

export function useAuthSession(requireAuth = false) {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(() => getStoredAuthToken());
  const [user, setUser] = useState<Me | null>(null);
  const [authChecked, setAuthChecked] = useState(() => getStoredAuthToken() === null);

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
        clearStoredAuthToken();
        setToken(null);
        setUser(null);
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
    clearStoredAuthToken();
    setToken(null);
    setUser(null);
    setAuthChecked(true);
    router.push("/login");
  }, [router]);

  const ready = token === null || authChecked;

  return { token, user, ready, signOut, isSignedIn: Boolean(token && user) };
}
