import anthropic, os, logging, httpx
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        http_client = httpx.Client(timeout=60.0, limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))
        self.client = anthropic.Anthropic(api_key=self.api_key, http_client=http_client)
        logger.info("✅ RAG Service initialized")
    
    def query(self, question: str, grade_level: str = "5th grade", depth_level: int = 1, child_age: Optional[int] = None) -> Dict:
        try:
            system = f"You are Nia, a friendly AI learning assistant for {grade_level} students. Use web search for current info. Be clear and encouraging! 🌟"
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                temperature=0.7,
                system=system,
                messages=[{"role": "user", "content": question}],
                tools=[{"type": "web_search_20250305", "name": "web_search"}]
            )
            
            answer, sources = "", []
            for block in response.content:
                if block.type == "text":
                    answer += block.text
                elif block.type == "tool_use" and block.name == "web_search":
                    sources.append({"type": "web_search", "query": block.input.get("query", ""), "verified": True})
            
            used_web = any(s["type"] == "web_search" for s in sources)
            if used_web and "🌐" not in answer:
                answer = "🌐 From the web:\n\n" + answer
            elif not used_web and "ℹ️" not in answer:
                answer = "ℹ️ From what I know:\n\n" + answer
            
            return {"answer": answer, "sources": sources, "model_used": "claude-sonnet-4", "used_web_search": used_web}
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            raise

_rag_service = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
