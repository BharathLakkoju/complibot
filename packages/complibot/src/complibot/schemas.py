"""Wire-format Pydantic models (camelCase aliases)."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        ser_json_timedelta="iso8601",
    )


FrameworkCode = Literal["GDPR", "SOC2", "ISO27001", "HIPAA", "INTERNAL"]
Severity = Literal["critical", "high", "medium", "low", "info"]
FindingKind = Literal["violation", "gap", "partial", "compliant"]
FindingStatus = Literal["open", "accepted", "rejected", "edited", "escalated"]
ConfidenceBand = Literal["high", "medium", "low"]
ProjectRole = Literal["owner", "reviewer", "viewer"]


class Confidence(ApiModel):
    score: float
    band: ConfidenceBand
    reason: str
    calibrated: bool = False


class Citation(ApiModel):
    document_id: str
    chunk_id: str
    section_path: str | None = None
    page: int | None = None
    char_start: int
    char_end: int
    quote: str


class Remediation(ApiModel):
    summary: str
    suggested_clause: str | None = None
    effort: Literal["trivial", "moderate", "significant"] = "moderate"
    owner_hint: Literal["legal", "security", "privacy", "engineering", "procurement"] = "legal"


class FindingProvenance(ApiModel):
    provider: Literal["bedrock", "openrouter", "mock"] = "mock"
    model_id: str
    prompt_version: str
    pack_version: str


class Finding(ApiModel):
    id: str
    schema_version: str = "1.0"
    tenant_id: str
    project_id: str
    review_id: str
    framework: FrameworkCode
    control_id: str
    control_ref: str
    kind: FindingKind
    title: str
    severity: Severity
    confidence: Confidence
    rationale: str
    remediation: Remediation | None = None
    citations: list[Citation] = Field(default_factory=list)
    status: FindingStatus = "open"
    assignee_id: str | None = None
    version: int = 1
    system_flags: list[str] = Field(default_factory=list)
    provenance: FindingProvenance
    created_at: datetime


class ReviewDecision(ApiModel):
    id: str
    tenant_id: str
    finding_id: str
    review_id: str
    action: Literal["accept", "reject", "edit", "escalate", "reopen", "override", "comment"]
    actor_id: str
    at: datetime
    reason: str | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    finding_version: int
    client_msg_id: str


class UserOut(ApiModel):
    id: str
    email: str
    name: str


class ProjectCreate(ApiModel):
    name: str
    framework_codes: list[FrameworkCode]


class ProjectOut(ApiModel):
    id: str
    tenant_id: str
    name: str
    framework_codes: list[FrameworkCode]
    created_by: str
    created_at: datetime


class DocumentOut(ApiModel):
    id: str
    project_id: str
    filename: str
    mime_type: str
    status: str
    page_count: int | None = None
    created_at: datetime


class ReviewCreate(ApiModel):
    document_ids: list[str]


class ReviewOut(ApiModel):
    id: str
    project_id: str
    document_ids: list[str]
    framework_codes: list[FrameworkCode]
    status: str
    last_seq: int
    created_at: datetime


class PresignOut(ApiModel):
    upload_url: str
    document_id: str
    s3_key: str


class DevLoginIn(ApiModel):
    email: str = "demo@complibot.local"
    name: str = "Demo Analyst"


class DevLoginOut(ApiModel):
    access_token: str
    user: UserOut


class ReportOut(ApiModel):
    project_id: str
    version: int
    status: str
    json_url: str | None = None
    pdf_url: str | None = None
