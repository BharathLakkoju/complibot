import type { Finding, FindingStatus } from "@/lib/types";

const DECIDED: ReadonlySet<FindingStatus> = new Set([
  "accepted",
  "rejected",
  "edited",
  "escalated",
]);

/** Prefer newer version; never downgrade a decided finding to open via stale REST bootstrap. */
export function mergeFinding(live: Finding, other: Finding): Finding {
  if (live.version > other.version) return live;
  if (other.version > live.version) return other;
  if (DECIDED.has(live.status) && !DECIDED.has(other.status)) return live;
  if (DECIDED.has(other.status) && !DECIDED.has(live.status)) return other;
  return live;
}

export function mergeFindingMaps(
  boot: Record<string, Finding>,
  live: Record<string, Finding>,
): Finding[] {
  const merged: Record<string, Finding> = { ...boot };
  for (const [id, f] of Object.entries(live)) {
    const prev = merged[id];
    merged[id] = prev ? mergeFinding(f, prev) : f;
  }
  return Object.values(merged);
}
