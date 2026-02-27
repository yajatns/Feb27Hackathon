"""Video Audit Cron — analyzes training/onboarding videos for compliance.

Uses Reka Vision to check videos against Senso policies.
"""

import json
from datetime import datetime, timezone

from integrations.reka import reka_client
from integrations.senso import senso_client
from integrations.neo4j_client import neo4j_client


async def run_video_audit(db_session=None) -> dict:
    """Audit training videos for compliance using Reka Vision."""
    findings = []

    # Sample training videos to audit (in production, from DB)
    videos_to_audit = [
        {"name": "Safety Training 2026", "url": "https://example.com/safety-training.mp4",
         "compliance_check": "Does this video cover all required safety topics?"},
        {"name": "Onboarding Orientation", "url": "https://example.com/onboarding.mp4",
         "compliance_check": "Does this orientation video include diversity and harassment policies?"},
    ]

    for video in videos_to_audit:
        try:
            # Upload to Reka
            upload = await reka_client.upload_video(video["url"], name=video["name"])
            video_id = upload.get("id", upload.get("video_id", ""))

            if video_id:
                # Analyze compliance
                analysis = await reka_client.qa_chat(video_id, video["compliance_check"])
                finding = {
                    "video": video["name"],
                    "analysis": analysis,
                    "status": "analyzed",
                }
            else:
                finding = {"video": video["name"], "status": "upload_failed", "detail": upload}
        except Exception as e:
            finding = {"video": video["name"], "status": "error", "error": str(e)}

        # Check against Senso policies
        try:
            policy = await senso_client.search_policy(f"training compliance requirements {video['name']}")
            finding["policy_check"] = json.dumps(policy, default=str)[:500]
        except Exception as e:
            finding["policy_check"] = f"Error: {e}"

        findings.append(finding)

        # Log to Neo4j
        try:
            await neo4j_client.log_completion(
                agent_name="VideoAuditCron",
                task=f"video_audit_{video['name']}",
                result=json.dumps(finding, default=str)[:500],
                tool_used="reka+senso",
                hire_request_id=f"cron-video-{datetime.now(timezone.utc).strftime('%Y%m%d')}")
        except Exception:
            pass

    return {
        "cron_type": "video_audit",
        "videos_audited": len(findings),
        "findings": findings,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
