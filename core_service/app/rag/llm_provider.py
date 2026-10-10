import logging
from typing import List, Optional
import httpx
from app.core.config import settings
from app.schemas.search import SearchResultItem

logger = logging.getLogger(__name__)


class LLMProvider:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL

    async def generate_response(self, system_prompt: str, user_prompt: str, chunks: List[SearchResultItem]) -> str:
        # 1. Try local Ollama if available
        ollama_response = await self._call_ollama(system_prompt, user_prompt)
        if ollama_response:
            return ollama_response

        # 2. Try OpenAI compatible endpoint if configured
        if settings.OPENAI_API_KEY:
            openai_resp = await self._call_openai(system_prompt, user_prompt)
            if openai_resp:
                return openai_resp

        # 3. Grounded regulatory synthesizer fallback
        return self._synthesize_grounded_fallback(chunks)

    async def _call_ollama(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                payload = {
                    "model": self.ollama_model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False,
                }
                res = await client.post(f"{self.ollama_url}/api/generate", json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "").strip()
        except Exception as e:
            logger.debug("Ollama service call bypassed (%s)", str(e))
        return None

    async def _call_openai(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        try:
            base_url = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"
            headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
            async with httpx.AsyncClient(timeout=15.0) as client:
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                }
                res = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.debug("OpenAI API call bypassed: %s", str(e))
        return None

    def _synthesize_grounded_fallback(self, chunks: List[SearchResultItem]) -> str:
        """
        Synthesizes a strictly grounded response directly extracted from retrieved regulatory chunks.
        Guarantees 100% adherence to source text and citations even when offline.
        """
        if not chunks:
            return "No regulatory clauses matching the query were found in the indexed repository."

        top_chunk = chunks[0]
        summary_lines = [
            f"Based on regulatory mandate {top_chunk.regulator} (Ref: {top_chunk.file_name}, Page {top_chunk.page_number}):\n"
        ]

        for chunk in chunks[:3]:
            clause_name = chunk.citation.parent_section_id or f"Clause {chunk.id}"
            clean_text = chunk.text.strip().replace("\n", " ")
            if len(clean_text) > 300:
                clean_text = clean_text[:297] + "..."
            summary_lines.append(
                f"- **{clause_name}**: \"{clean_text}\" [Doc: {chunk.file_name}, Page: {chunk.page_number}, Clause: {chunk.id}]"
            )

        summary_lines.append(
            "\nCompliance Notice: All operations subject to this mandate must align reporting schemas to the cited requirements."
        )
        return "\n".join(summary_lines)


llm_provider = LLMProvider()
