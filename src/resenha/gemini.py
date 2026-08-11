import logging
import time

from google import genai
from google.genai import errors as genai_errors

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model="gemini-flash-lite-latest",
                    contents=prompt,
                    config={"max_output_tokens": max_tokens},
                )
                return response.text or ""
            except genai_errors.ClientError as e:
                if e.code == 429 and attempt < 2:
                    delay = 2 ** (attempt + 1)
                    logger.warning(
                        "Gemini rate limited (429), retry %d/3 in %ds",
                        attempt + 1, delay,
                    )
                    time.sleep(delay)
                    continue
                raise
            except Exception:
                raise
        return ""
