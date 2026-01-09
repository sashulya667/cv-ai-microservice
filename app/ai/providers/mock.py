import json

from app.ai.base import LLMClient, LLMInput, LLMResponse


class MockClient(LLMClient):
    async def generate(self, *, inp: LLMInput) -> LLMResponse:
        payload = {
            "overall_score": 78,
            "ats_score": 72,
            "summary": "Clear structure and relevant experience, but impact metrics are often missing.",
            "strengths": [
                "Clear experience section and progression",
                "Relevant skills listed for the target domain",
            ],
            "weaknesses": [
                "Limited quantified achievements",
                "Some bullets are long and not outcome-focused",
            ],
            "improvements": [
                "Add measurable impact (%, $, latency, throughput) to each role",
                "Tailor the summary to the target role and seniority",
                "Shorten bullet points to 1–2 lines and start with strong verbs",
                "Group skills by category and prioritize the most relevant ones",
            ],
            "section_feedback": {
                "header": "Ensure email/links are clickable and location is consistent.",
                "summary": "Good, but tailor it and mention a niche strength.",
                "experience": "Add outcomes and metrics; make bullets consistent.",
                "skills": "Group by categories; remove weak/irrelevant items.",
                "education": "Add thesis/project highlights if relevant.",
                "projects": "Pick 1–2 standout projects and include results.",
            },
        }

        return LLMResponse(
            text=json.dumps(payload),
            raw={"mock": True},
        )
