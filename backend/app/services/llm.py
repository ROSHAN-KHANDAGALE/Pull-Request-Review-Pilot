import json
from groq import AsyncGroq
from fastapi import HTTPException
from app.config import settings

class LLMService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = settings.model_name

    async def analyze_diff(self, diff: str) -> dict:
        system_prompt = """
            You are an expert code reviewer. Analyze the git diff and return ONLY a valid JSON object with no extra text.

            Return this exact structure:
            {
            "issues": [
                {
                "severity": "critical|major|minor|info",
                "category": "correctness|security|maintainability|test_coverage|documentation",
                "title": "short title",
                "description": "detailed explanation",
                "file_path": "path/to/file or null",
                "line_number": 42 or null,
                "suggestion": "how to fix it or null"
                }
            ]
            }

            Rules:
            - severity must be exactly one of: critical, major, minor, info
            - category must be exactly one of: correctness, security, maintainability, test_coverage, documentation
            - Return an empty issues array if no issues found
            - Never return null for the issues array
            - file_path and line_number may be null if not determinable
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Review this diff:\n\n{diff}"}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=502, detail=f"LLM returned invalid JSON: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Groq error: {str(e)}")