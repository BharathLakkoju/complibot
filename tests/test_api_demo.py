import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from complibot.main import app


@pytest.mark.asyncio
async def test_demo_review_produces_findings() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/dev-login",
            json={"email": "pytest@complibot.local", "name": "Pytest"},
        )
        assert login.status_code == 200
        token = login.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "Test project", "frameworkCodes": ["GDPR"]},
        )
        assert project.status_code == 200
        project_id = project.json()["id"]
        review = await client.post(f"/v1/projects/{project_id}/demo", headers=headers)
        assert review.status_code == 200
        review_id = review.json()["id"]
        for _ in range(20):
            findings = await client.get(f"/v1/reviews/{review_id}/findings", headers=headers)
            if findings.json():
                break
            await asyncio.sleep(0.25)
        assert findings.status_code == 200
        data = findings.json()
        assert len(data) >= 1
        quote = data[0]["citations"][0]["quote"]
        snap = await client.get(f"/v1/reviews/{review_id}/snapshot", headers=headers)
        doc_text = snap.json()["documents"][data[0]["citations"][0]["documentId"]]
        c0 = data[0]["citations"][0]
        assert quote == doc_text[c0["charStart"] : c0["charEnd"]]
