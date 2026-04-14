"""
Unified LLM service. Priority: Gemini (fast, free) → Ollama (local) → empty string.
"""
import logging, httpx
logger = logging.getLogger(__name__)

def _key():
    from app.config import settings
    return settings.gemini_api_key

def _model():
    from app.config import settings
    return getattr(settings, "ollama_model", "mistral")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def _gemini_sync(prompt: str, system: str, max_tokens: int) -> str:
    key = _key()
    if not key:
        return ""
    full = f"{system}\n\n{prompt}" if system else prompt
    try:
        r = httpx.post(f"{GEMINI_URL}?key={key}",
                       json={"contents": [{"parts": [{"text": full}]}],
                             "generationConfig": {"maxOutputTokens": max_tokens}},
                       timeout=20)
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.debug("Gemini sync error: %s", e)
    return ""

async def _gemini_async(prompt: str, system: str, max_tokens: int) -> str:
    key = _key()
    if not key:
        return ""
    full = f"{system}\n\n{prompt}" if system else prompt
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as c:
            r = await c.post(f"{GEMINI_URL}?key={key}",
                             json={"contents": [{"parts": [{"text": full}]}],
                                   "generationConfig": {"maxOutputTokens": max_tokens}})
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.debug("Gemini async error: %s", e)
    return ""

def _ollama_sync(prompt: str, system: str, max_tokens: int) -> str:
    try:
        import ollama as _ol
        msgs = []
        if system: msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        r = _ol.chat(model=_model(), messages=msgs, options={"num_predict": max_tokens})
        return r["message"]["content"].strip()
    except Exception:
        return ""

async def llm_complete(prompt: str, max_tokens: int = 300, system: str = "") -> str:
    """Async: Gemini → Ollama → empty."""
    result = await _gemini_async(prompt, system, max_tokens)
    if result:
        return result
    return _ollama_sync(prompt, system, max_tokens)

def llm_complete_sync(prompt: str, max_tokens: int = 300, system: str = "") -> str:
    """Sync: Gemini → Ollama → empty."""
    result = _gemini_sync(prompt, system, max_tokens)
    if result:
        return result
    return _ollama_sync(prompt, system, max_tokens)
