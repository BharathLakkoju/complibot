"""Dispatch review pipeline by LLM provider."""

from __future__ import annotations

from complibot.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession

from complibot_worker.pipeline.bedrock_review import BedrockReviewError, run_bedrock_review
from complibot_worker.pipeline.mock_review import run_mock_review
from complibot_worker.pipeline.openrouter_review import run_openrouter_review


async def run_review(
    db: AsyncSession,
    *,
    tenant_id: str,
    review_id: str,
    frameworks_path: str,
    token_streaming: bool,
) -> None:
    settings = get_settings()
    provider = settings.llm_provider.strip().lower()
    if provider == "bedrock":
        try:
            await run_bedrock_review(
                db,
                tenant_id=tenant_id,
                review_id=review_id,
                frameworks_path=frameworks_path,
                token_streaming=token_streaming,
            )
        except BedrockReviewError:
            if settings.llm_bedrock_fallback_mock:
                await run_mock_review(
                    db,
                    tenant_id=tenant_id,
                    review_id=review_id,
                    frameworks_path=frameworks_path,
                    token_streaming=token_streaming,
                )
            else:
                raise
        return
    if provider == "openrouter":
        await run_openrouter_review(
            db,
            tenant_id=tenant_id,
            review_id=review_id,
            frameworks_path=frameworks_path,
            token_streaming=token_streaming,
        )
        return
    await run_mock_review(
        db,
        tenant_id=tenant_id,
        review_id=review_id,
        frameworks_path=frameworks_path,
        token_streaming=token_streaming,
    )
