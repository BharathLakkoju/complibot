"use client";

import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import { getWsUrl } from "@/lib/api";
import type { Finding } from "@/lib/types";

type State = {
  findings: Record<string, Finding>;
  reviewStatus: string;
  lastSeq: number;
  connected: boolean;
  role: string;
};

type Action =
  | { type: "welcome"; lastSeq: number; role: string }
  | { type: "finding"; finding: Finding }
  | { type: "status"; status: string }
  | { type: "connected"; value: boolean };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "welcome":
      return { ...state, lastSeq: action.lastSeq, role: action.role, connected: true };
    case "finding":
      return {
        ...state,
        findings: { ...state.findings, [action.finding.id]: action.finding },
      };
    case "status":
      return { ...state, reviewStatus: action.status };
    case "connected":
      return { ...state, connected: action.value };
    default:
      return state;
  }
}

export function useReviewSocket(reviewId: string, token: string | null) {
  const [state, dispatch] = useReducer(reducer, {
    findings: {},
    reviewStatus: "queued",
    lastSeq: 0,
    connected: false,
    role: "viewer",
  });
  const [docText, setDocText] = useState<Record<string, string>>({});
  const lastSeqRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!token) return;
    const ws = new WebSocket(getWsUrl(reviewId));
    wsRef.current = ws;
    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          v: 1,
          type: "client.hello",
          payload: { token, lastSeq: lastSeqRef.current, clientVersion: "0.1.0" },
        }),
      );
    };
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.seq) {
        lastSeqRef.current = Math.max(lastSeqRef.current, msg.seq);
        dispatch({ type: "welcome", lastSeq: msg.seq, role: state.role });
      }
      if (msg.type === "server.welcome") {
        dispatch({
          type: "welcome",
          lastSeq: msg.payload.currentSeq,
          role: msg.payload.role,
        });
      }
      if (msg.type === "finding.created" || msg.type === "finding.updated") {
        dispatch({ type: "finding", finding: msg.payload.finding });
      }
      if (msg.type === "review.status") {
        dispatch({ type: "status", status: msg.payload.status });
      }
    };
    ws.onclose = () => dispatch({ type: "connected", value: false });
    ws.onerror = () => dispatch({ type: "connected", value: false });
  }, [reviewId, token, state.role]);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const submitDecision = useCallback(
    (findingId: string, action: string, findingVersion: number, reason?: string) => {
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

  return { state, docText, setDocText, submitDecision, lastSeqRef };
}
