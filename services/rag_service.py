import anthropic
import os
import logging
import httpx
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        http_client = httpx.Client(
            timeout=60.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
        self.client = anthropic.Anthropic(api_key=self.api_key, http_client=http_client)
        logger.info("✅ RAG Service initialized")

    def _build_system_prompt(
        self,
        grade_level: str,
        language: str = "en",
        accommodations: Optional[List[str]] = None,
        reading_level: Optional[str] = None
    ) -> str:
        """Build a customized system prompt based on child's needs"""

        # Base prompt
        if language == "es":
            base = f"Eres Nia, una asistente de aprendizaje amigable para estudiantes de {grade_level}."
        else:
            base = f"You are Nia, a friendly AI learning assistant for {grade_level} students."

        # Add accommodation-specific instructions
        accommodation_prompts = {
            "autism_support": {
                "en": "\n- Use clear, literal language without idioms or metaphors\n- Provide structured, predictable responses\n- Break information into small, clear steps\n- Avoid overwhelming visual descriptions",
                "es": "\n- Usa lenguaje claro y literal sin modismos o metáforas\n- Proporciona respuestas estructuradas y predecibles\n- Divide la información en pasos pequeños y claros\n- Evita descripciones visuales abrumadoras"
            },
            "dyslexia_support": {
                "en": "\n- Use simple sentence structures\n- Avoid long paragraphs\n- Use bullet points when helpful\n- Spell out numbers and dates clearly",
                "es": "\n- Usa estructuras de oraciones simples\n- Evita párrafos largos\n- Usa viñetas cuando sea útil\n- Deletrea números y fechas claramente"
            },
            "adhd_support": {
                "en": "\n- Keep responses concise and focused\n- Use engaging, varied language\n- Break content into manageable chunks\n- Provide clear transitions between topics",
                "es": "\n- Mantén las respuestas concisas y enfocadas\n- Usa lenguaje variado y atractivo\n- Divide el contenido en partes manejables\n- Proporciona transiciones claras entre temas"
            },
            "visual_learner": {
                "en": "\n- Describe concepts visually when possible\n- Use spatial analogies\n- Suggest mental imagery techniques",
                "es": "\n- Describe conceptos visualmente cuando sea posible\n- Usa analogías espaciales\n- Sugiere técnicas de imágenes mentales"
            },
            "simplified_language": {
                "en": "\n- Use simple, everyday vocabulary\n- Avoid technical jargon unless explaining it\n- Use short sentences\n- Define unfamiliar words",
                "es": "\n- Usa vocabulario simple y cotidiano\n- Evita jerga técnica a menos que la expliques\n- Usa oraciones cortas\n- Define palabras desconocidas"
            }
        }

        # Add accommodations to prompt
        if accommodations:
            if language == "es":
                base += "\n\nAdaptaciones especiales:"
            else:
                base += "\n\nSpecial accommodations:"

            for acc in accommodations:
                if acc in accommodation_prompts:
                    base += accommodation_prompts[acc].get(language, accommodation_prompts[acc]["en"])

        # Add reading level adjustment
        if reading_level and reading_level != grade_level:
            if language == "es":
                base += f"\n\nNivel de lectura: {reading_level} (ajusta el vocabulario apropiadamente)"
            else:
                base += f"\n\nReading level: {reading_level} (adjust vocabulary accordingly)"

        # Add source citation instruction
        if language == "es":
            base += "\n\n- Usa búsqueda web para información actual\n- Cita tus fuentes claramente\n- Sé alentador y paciente 🌟"
        else:
            base += "\n\n- Use web search for current information\n- Cite your sources clearly\n- Be encouraging and patient 🌟"

        return base

    def query(
        self,
        question: str,
        grade_level: str = "5th grade",
        depth_level: int = 1,
        child_age: Optional[int] = None,
        language: str = "en",
        accommodations: Optional[List[str]] = None,
        reading_level: Optional[str] = None
    ) -> Dict:
        """
        Query the RAG system with full accessibility support

        Args:
            question: The child's question
            grade_level: Child's grade level
            depth_level: Current depth in conversation (1-3)
            child_age: Child's age for age-appropriate responses
            language: 'en' for English, 'es' for Spanish
            accommodations: List of learning accommodations to apply
            reading_level: Reading level if different from grade level
        """
        try:
            system_prompt = self._build_system_prompt(
                grade_level=grade_level,
                language=language,
                accommodations=accommodations,
                reading_level=reading_level
            )

            # Add language instruction to question if Spanish
            if language == "es":
                question_with_lang = f"[Responde en español] {question}"
            else:
                question_with_lang = question

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": question_with_lang}],
                tools=[{"type": "web_search_20250305", "name": "web_search"}]
            )

            answer = ""
            sources = []
            citations = []

            # Process response blocks
            for block in response.content:
                if block.type == "text":
                    answer += block.text
                elif block.type == "tool_use" and block.name == "web_search":
                    search_query = block.input.get("query", "")
                    sources.append({
                        "type": "web_search",
                        "query": search_query,
                        "verified": True
                    })

            # Check if web search was used
            used_web = any(s["type"] == "web_search" for s in sources)

            # Add source indicator if not already present
            if language == "es":
                web_indicator = "🌐 Información de la web:\n\n"
                knowledge_indicator = "ℹ️ De lo que sé:\n\n"
            else:
                web_indicator = "🌐 From the web:\n\n"
                knowledge_indicator = "ℹ️ From what I know:\n\n"

            if used_web and "🌐" not in answer:
                answer = web_indicator + answer
            elif not used_web and "ℹ️" not in answer:
                answer = knowledge_indicator + answer

            # Extract citations from answer (look for [1], [2], etc.)
            import re
            citation_pattern = r'\[(\d+)\]'
            citation_numbers = re.findall(citation_pattern, answer)

            return {
                "answer": answer,
                "sources": sources,
                "citations": citation_numbers,
                "model_used": "claude-sonnet-4",
                "used_web_search": used_web,
                "language": language
            }

        except Exception as e:
            logger.error(f"RAG query error: {e}", exc_info=True)

            # Return error message in appropriate language
            if language == "es":
                error_msg = "Lo siento, tuve un problema procesando tu pregunta. ¿Podrías intentar preguntar de otra manera?"
            else:
                error_msg = "I'm sorry, I had trouble processing your question. Could you try asking in a different way?"

            return {
                "answer": error_msg,
                "sources": [],
                "citations": [],
                "model_used": "error",
                "used_web_search": False,
                "language": language,
                "error": str(e)
            }


_rag_service = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
