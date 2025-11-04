from openai import OpenAI
from typing import Dict, List, Optional
from content_summarizer import NiaSummarizer
from safety_filter import ChildSafetyFilter
import os

class NiaTutor:
    """Nia - An Intelligent Learning Summarization Assistant"""
    
    def __init__(self, safety_filter: ChildSafetyFilter):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)
        self.safety = safety_filter
        self.summarizer = NiaSummarizer()
        self._load_educational_content()
    
    def _load_educational_content(self):
        sample_content = [
            """Photosynthesis is the process by which plants use sunlight, water, 
            and carbon dioxide to create oxygen and energy in the form of sugar.""",
            """The water cycle describes the continuous movement of water on, above, 
            and below the surface of the Earth.""",
        ]
        try:
            self.summarizer.create_lsi_model(sample_content)
        except:
            pass
    
    def create_student_profile(self, name: str, age: int, grade: int,
                              special_needs: Optional[List[str]] = None,
                              reading_level: Optional[int] = None) -> Dict:
        return {
            "id": None,
            "name": name,
            "age": age,
            "grade": grade,
            "reading_level": reading_level or grade,
            "special_needs": special_needs or [],
            "interests": [],
            "conversation_history": [],
            "progress": {},
            "summarization_preferences": {
                "preferred_length": "medium",
                "include_examples": True,
                "use_simple_words": grade <= 5
            }
        }
    
    def build_system_prompt(self, student: Dict) -> str:
        base_prompt = f"""You are Nia, an intelligent learning assistant for students.

STUDENT: {student['name']}, Age {student['age']}, Grade {student['grade']}

YOUR MISSION:
- Help students understand complex topics
- Provide clear, age-appropriate explanations
- Be encouraging and patient
- Make learning engaging

COMMUNICATION:
- Use simple language for grade {student['grade']}
- Keep responses 2-4 paragraphs
- Use relatable examples
- Be warm and supportive"""

        if student['special_needs']:
            base_prompt += f"\n\nSPECIAL NEEDS: {', '.join(student['special_needs'])}"
        
        return base_prompt
    
    def summarize_content(self, content: str, student: Dict) -> Dict:
        summary_result = self.summarizer.summarize_for_age(
            text=content,
            age=student['age'],
            grade=student['reading_level']
        )
        
        if student['summarization_preferences']['use_simple_words']:
            summary_result['summary'] = self.summarizer.simplify_vocabulary(
                summary_result['summary'],
                student['reading_level']
            )
        
        return summary_result
    
    def process_study_material(self, material: str, student: Dict) -> Dict:
        summary = self.summarize_content(material, student)
        key_sentences = self.summarizer.extract_key_sentences(material, num_sentences=5)
        
        questions_prompt = f"""Based on this summary: {summary['summary']}

Create 3 comprehension questions for a {student['grade']}th grader.
Format: Just the questions, numbered 1-3."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": questions_prompt}],
                max_tokens=300
            )
            practice_questions = response.choices[0].message.content
        except:
            practice_questions = "Questions coming soon!"
        
        return {
            "summary": summary['summary'],
            "key_points": key_sentences,
            "practice_questions": practice_questions,
            "reading_time_minutes": summary['summary_length'] // 50,
            "original_length": summary['original_length'],
            "compression_ratio": f"{summary['compression_ratio']:.1%}"
        }
    
    def chat(self, student: Dict, message: str) -> Dict:
        is_safe, reason = self.safety.check_input_safety(message)
        
        if not is_safe:
            return self._handle_unsafe_input(reason, message)
        
        system_prompt = self.build_system_prompt(student)
        messages = self._build_message_history(student, message)
        
        # Add system message at the beginning
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=full_messages,
                max_tokens=800
            )
            
            ai_response = response.choices[0].message.content
            
            is_safe, _ = self.safety.validate_output(ai_response, student['reading_level'])
            
            if not is_safe:
                return {
                    "success": False,
                    "response": "Let me think about that differently..."
                }
            
            student['conversation_history'].extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": ai_response}
            ])
            
            if len(student['conversation_history']) > 20:
                student['conversation_history'] = student['conversation_history'][-20:]
            
            return {
                "success": True,
                "response": ai_response,
                "needs_intervention": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": "I'm having trouble thinking right now. Can you try again?",
                "error": str(e)
            }
    
    def _build_message_history(self, student: Dict, current_message: str) -> List[Dict]:
        messages = student['conversation_history'][-10:] if student['conversation_history'] else []
        messages.append({"role": "user", "content": current_message})
        return messages
    
    def _handle_unsafe_input(self, reason: str, message: str) -> Dict:
        distress_keywords = ["hurt myself", "kill myself", "suicide"]
        needs_intervention = any(kw in message.lower() for kw in distress_keywords)
        
        if needs_intervention:
            return {
                "success": True,
                "response": """I'm worried about you. Please talk to a trusted adult right away.

National Suicide Prevention Lifeline: 988
Crisis Text Line: Text HOME to 741741

You matter.""",
                "needs_intervention": True,
                "alert_type": "crisis"
            }
        
        return {
            "success": True,
            "response": "I can't help with that topic, but I'd love to help you learn! What are you studying?",
            "needs_intervention": False
        }
