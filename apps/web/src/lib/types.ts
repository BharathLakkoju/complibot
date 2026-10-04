export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type ConfidenceBand = "high" | "medium" | "low";
export type FindingStatus = "open" | "accepted" | "rejected" | "edited" | "escalated";

export interface Finding {
  id: string;
  title: string;
  severity: Severity;
  status: FindingStatus;
  version: number;
  framework: string;
  controlRef: string;
  kind: string;
  rationale: string;
  confidence: { band: ConfidenceBand; reason: string; calibrated: boolean };
  citations: Array<{
    documentId: string;
    charStart: number;
    charEnd: number;
    quote: string;
  }>;
  remediation?: { summary: string } | null;
}

export interface Project {
  id: string;
  name: string;
  frameworkCodes: string[];
  createdAt: string;
}

export interface Review {
  id: string;
  projectId: string;
  status: string;
  lastSeq: number;
}
