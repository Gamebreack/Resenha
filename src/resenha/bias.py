import logging
from resenha.gemini import GeminiClient
from resenha.cache import Cache
from resenha.news import NewsItem

logger = logging.getLogger(__name__)
CACHE_KEY_PREFIX = "bias:"

def infer_source_bias(source_name: str, gemini: GeminiClient, cache: Cache | None = None) -> str:
    key = f"{CACHE_KEY_PREFIX}{source_name}"
    if cache:
        cached = cache.get(key, ttl_seconds=86400 * 30)  # 30 days
        if cached:
            return str(cached.get("bias", "unknown"))
    
    prompt = f"What is the ideological bias of {source_name}? Respond in 10 words or less."
    try:
        bias = gemini.generate(prompt, max_tokens=50).strip()
    except Exception as e:
        logger.warning(f"Failed to infer bias for {source_name}: {e}")
        return "unknown"
    
    if cache:
        cache.set(key, {"bias": bias})
    return bias

def annotate_news(news: list[NewsItem], gemini: GeminiClient, cache: Cache | None = None) -> dict[str, str]:
    unique_sources = {item.source for item in news}
    return {source: infer_source_bias(source, gemini, cache) for source in unique_sources}
