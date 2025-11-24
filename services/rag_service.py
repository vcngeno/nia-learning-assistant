"""
Enhanced RAG Service with Educational Content Integration
"""
import logging
from typing import List, Dict, Optional
from anthropic import Anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from services.content_manager import content_manager

logger = logging.getLogger(__name__)


class RAGService:
    """Enhanced RAG service with educational content"""

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    async def search_relevant_content(
        self,
        db: AsyncSession,
        query: str,
        child_grade_level: str = None,
        limit: int = 3
    ) -> List[Dict]:
        """Search for relevant educational content"""

        # Extract subject keywords from query
        subject_keywords = {
            'math': ['math', 'arithmetic', 'algebra', 'geometry', 'fraction', 'multiply', 'divide', 'add', 'subtract', 'equation'],
            'science': ['science', 'biology', 'chemistry', 'physics', 'photosynthesis', 'plant', 'animal', 'water cycle', 'energy'],
            'history': ['history', 'washington', 'revolution', 'american', 'civil war', 'president', 'colony'],
            'english': ['english', 'grammar', 'writing', 'sentence', 'paragraph', 'noun', 'verb', 'adjective'],
            'geography': ['geography', 'continent', 'ocean', 'state', 'country', 'map', 'capital']
        }

        # Determine subject from query
        query_lower = query.lower()
        detected_subject = None

        for subject, keywords in subject_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_subject = subject
                break

        # Map grade levels
        grade_mapping = {
            'kindergarten': 'elementary',
            '1st grade': 'elementary',
            '2nd grade': 'elementary',
            '3rd grade': 'elementary',
            '4th grade': 'elementary',
            '5th grade': 'elementary',
            '6th grade': 'middle',
            '7th grade': 'middle',
            '8th grade': 'middle',
            '9th grade': 'high',
            '10th grade': 'high',
            '11th grade': 'high',
            '12th grade': 'high',
        }

        grade_level_category = grade_mapping.get(child_grade_level, 'elementary')

        # Search content
        results = await content_manager.search_content(
            db=db,
            query=query,
            subject=detected_subject,
            grade_level=grade_level_category,
            limit=limit
        )

        # Format results
        formatted_results = []
        for content in results:
            formatted_results.append({
                'id': content.id,
                'title': content.title,
                'subject': content.subject,
                'grade_level': content.grade_level,
                'topic': content.topic,
                'content': content.content,
                'relevance': 'high' if detected_subject == content.subject else 'medium'
            })

        return formatted_results

    def build_context_from_content(
        self,
        search_results: List[Dict],
        max_tokens: int = 3000
    ) -> str:
        """Build context string from search results"""

        if not search_results:
            return ""

        context_parts = ["Here is relevant educational content from our curriculum:\n"]
        current_tokens = 0

        for i, result in enumerate(search_results, 1):
            content_preview = result['content'][:1500]  # Limit each piece

            section = f"\n--- Source {i}: {result['title']} ({result['subject']} - {result['grade_level']}) ---\n{content_preview}\n"

            # Rough token estimation (4 chars ≈ 1 token)
            estimated_tokens = len(section) // 4

            if current_tokens + estimated_tokens > max_tokens:
                break

            context_parts.append(section)
            current_tokens += estimated_tokens

        return "".join(context_parts)

    async def generate_response(
        self,
        db: AsyncSession,
        question: str,
        child_profile: Dict,
        conversation_history: List[Dict] = None,
        current_depth: int = 1
    ) -> Dict:
        """Generate response using RAG with educational content"""

        # Search for relevant content
        search_results = await self.search_relevant_content(
            db=db,
            query=question,
            child_grade_level=child_profile.get('grade_level'),
            limit=3
        )

        # Build context from search results
        context = self.build_context_from_content(search_results)

        # Determine if we have curated content
        has_curated_content = len(search_results) > 0

        # Build system prompt
        system_prompt = self._build_system_prompt(
            child_profile=child_profile,
            has_curated_content=has_curated_content,
            current_depth=current_depth
        )

        # Build user message
        if context:
            user_message = f"{context}\n\nStudent's Question: {question}"
        else:
            user_message = f"Student's Question: {question}"

        # Prepare messages
        messages = []

        # Add conversation history if exists
        if conversation_history:
            for msg in conversation_history[-4:]:  # Last 4 messages for context
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current question
        messages.append({
            "role": "user",
            "content": user_message
        })

        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                temperature=0.7,
                system=system_prompt,
                messages=messages
            )

            answer_text = response.content[0].text

            # Determine source label
            if has_curated_content:
                source_label = "📚 From our curriculum"
            else:
                source_label = "ℹ️ From what I know"

            # Format response
            formatted_answer = f"{source_label}:\n\n{answer_text}"

            return {
                'text': formatted_answer,
                'source_label': source_label,
                'has_curated_content': has_curated_content,
                'sources': search_results,
                'model_used': 'claude-sonnet-4-20250514',
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def _build_system_prompt(
        self,
        child_profile: Dict,
        has_curated_content: bool,
        current_depth: int
    ) -> str:
        """Build system prompt based on child profile and context"""

        base_prompt = f"""You are Nia, a friendly and encouraging AI tutor for K-12 students in the United States.

Student Profile:
- Grade Level: {child_profile.get('grade_level', 'elementary')}
- Preferred Language: {child_profile.get('preferred_language', 'en')}
- Reading Level: {child_profile.get('reading_level', 'at grade level')}

Teaching Approach:
- Be warm, encouraging, and patient
- Use age-appropriate language for {child_profile.get('grade_level', 'elementary')} level
- Explain concepts clearly with examples
- Use US curriculum standards (Common Core)
- Include emojis to make learning fun (but not too many!)

"""

        # Add content source instruction
        if has_curated_content:
            base_prompt += """IMPORTANT: You have been provided with curated educational content from our curriculum. Use this content as your PRIMARY source. Explain the concepts from this material in your own words, adapted to the student's level.

"""

        # Add language instruction
        if child_profile.get('preferred_language') == 'es':
            base_prompt += """CRITICAL: Respond in SPANISH. The student prefers Spanish, so your entire response must be in Spanish.

"""

        # Add depth-based instructions
        if current_depth == 1:
            base_prompt += """This is an introductory explanation. Keep it clear and simple, covering the main concepts.

"""
        elif current_depth == 2:
            base_prompt += """This is a deeper dive. Provide more details, examples, and explanations than before.

"""
        elif current_depth == 3:
            base_prompt += """This is the deepest level. Provide comprehensive information with advanced details, multiple examples, and connections to related concepts.

"""

        # Add accommodations if any
        accommodations = child_profile.get('learning_accommodations', [])
        if accommodations:
            base_prompt += f"\nLearning Accommodations: {', '.join(accommodations)}\n"

            if 'autism_support' in accommodations:
                base_prompt += "- Use literal language, avoid metaphors\n- Provide clear, structured explanations\n- List steps explicitly\n"

            if 'dyslexia_support' in accommodations:
                base_prompt += "- Use simple sentences\n- Break information into bullet points\n- Use clear formatting\n"

            if 'adhd_support' in accommodations:
                base_prompt += "- Keep responses concise and focused\n- Use engaging language\n- Highlight key points\n"

            if 'visual_learner' in accommodations:
                base_prompt += "- Use visual descriptions\n- Describe spatial relationships\n- Paint mental pictures\n"

        base_prompt += """\nResponse Format:
- Start with the explanation
- Use examples relevant to the student's life
- End with follow-up questions to check understanding (unless at max depth)
- Be encouraging and supportive!
"""

        return base_prompt


# Singleton instance
rag_service = RAGService()
