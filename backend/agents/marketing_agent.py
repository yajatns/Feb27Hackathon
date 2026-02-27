"""Marketing Agent — Reka video analysis for training and brand content."""

import json
from agents.base import BaseAgent
from integrations.reka import reka_client


class MarketingAgent(BaseAgent):
    name = "Marketing"
    description = "Video analysis, training content review, brand compliance"
    tools = ["reka_analyze", "reka_clips"]

    async def execute(self, task: str, context: dict, hire_request_id: str) -> dict:
        video_url = context.get("video_url", "")
        question = context.get("question", "Analyze this content for compliance and quality")

        if not video_url:
            return {"agent": self.name, "tool": "reka", "result": {"skip": "No video URL provided"}}

        try:
            upload = await reka_client.upload_video(video_url)
            video_id = upload.get("id", upload.get("video_id", ""))
            if video_id:
                analysis = await reka_client.qa_chat(video_id, question)
                clips = await reka_client.get_clips(video_id, "key moments")
                result = {"analysis": analysis, "clips": clips}
            else:
                result = {"upload": upload}
        except Exception as e:
            result = {"error": str(e)}

        await self.log_action(
            task=f"Video analysis",
            result=json.dumps(result, default=str)[:1000],
            tool="reka_vision",
            hire_request_id=hire_request_id)

        return {"agent": self.name, "tool": "reka_vision", "result": result}


marketing_agent = MarketingAgent()
