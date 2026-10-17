"use client";

import { useCallback, useEffect, useReducer, useRef, type Dispatch } from "react";
import { getWsUrl } from "@/lib/api";
import type { Finding } from "@/lib/types";

type State = {
  findings: Record<string, Finding>;
  reviewStatus: string;
  lastSeq: number;
  connected: boolean;
  role: string;
  decisionError: string | null;
};

type Action =
  | { type: "welcome"; lastSeq: number; role: string }
  | { type: "finding"; finding: Finding }
  | { type: "status"; status: string }
  | { type: "connected"; value: boolean }
  | { type: "decisionError"; message: string | null };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "welcome":
      return {
        ...state,
        lastSeq: action.lastSeq,
        role: action.role,
        connected: true,
        decisionError: null,
      };
    case "finding":
      return {
        ...state,
        findings: { ...state.findings, [action.finding.id]: action.finding },
      };
    case "status":
      return { ...state, reviewStatus: action.status };
    case "connected":
      return { ...state, connected: action.value };
    case "decisionError":
      return { ...state, decisionError: action.message };
    default:
      return state;
  }
}

function handleServerMessage(
  msg: { type?: string; seq?: number; payload?: Record<string, unknown> },
  dispatch: Dispatch<Action>,
  lastSeqRef: React.MutableRefObject<number>,
) {
  if (typeof msg.seq === "number") {
    lastSeqRef.current = Math.max(lastSeqRef.current, msg.seq);
  }
  const payload = msg.payload ?? {};
  if (msg.type === "server.welcome") {
    dispatch({
      type: "welcome",
      lastSeq: Number(payload.currentSeq ?? lastSeqRef.current),
      role: String(payload.role ?? "viewer"),
    });
    return;
  }
  if (msg.type === "finding.created" || msg.type === "finding.updated") {
    const finding = payload.finding as Finding;
    if (finding?.id) {
      dispatch({ type: "finding", finding });
    }
    return;
  }
  if (msg.type === "review.status") {
    const status = payload.status as string;
    if (status) dispatch({ type: "status", status });
    return;
  }
  if (msg.type === "decision.rejected") {
    const code = String(payload.code ?? "rejected");
    dispatch({ type: "decisionError", message: `Decision not applied: ${code}` });
  }
}

export function useReviewSocket(reviewId: string, token: string | null) {
  const [state, dispatch] = useReducer(reducer, {
    findings: {},
    reviewStatus: "queued",
    lastSeq: 0,
    connected: false,
    role: "viewer",
    decisionError: null,
  });
  const lastSeqRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);

  const setReviewStatus = useCallback((status: string) => {
    dispatch({ type: "status", status });
  }, []);

  const clearDecisionError = useCallback(() => {
    dispatch({ type: "decisionError", message: null });
  }, []);

  useEffect(() => {
    if (!token) return;
    let closed = false;
    const ws = new WebSocket(getWsUrl(reviewId));
    wsRef.current = ws;

    ws.onopen = () => {
      if (closed) return;
      dispatch({ type: "connected", value: true });
      ws.send(
        JSON.stringify({
          v: 1,
          type: "client.hello",
          payload: { token, lastSeq: lastSeqRef.current, clientVersion: "0.1.0" },
        }),
      );
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data as string);
        handleServerMessage(msg, dispatch, lastSeqRef);
      } catch {
        /* ignore malformed frames */
      }
    };

    ws.onclose = () => {
      if (!closed) dispatch({ type: "connected", value: false });
    };
    ws.onerror = () => dispatch({ type: "connected", value: false });

    return () => {
      closed = true;
      ws.close();
      wsRef.current = null;
    };
  }, [reviewId, token]);

  const submitDecision = useCallback(
    (findingId: string, action: string, findingVersion: number, reason?: string) => {
      dispatch({ type: "decisionError", message: null });
      const clientMsgId = crypto.randomUUID();
      wsRef.current?.send(
        JSON.stringify({
          v: 1,
          type: "decision.submit",
          payload: { clientMsgId, findingId, action, findingVersion, reason },
        }),
      );
    },
    [],
  );

  return {
    state,
    setReviewStatus,
    submitDecision,
    clearDecisionError,
    lastSeqRef,
  };
}
