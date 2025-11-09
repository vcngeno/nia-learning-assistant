from enum import Enum
from typing import Dict, Any, List

class QuestionType(Enum):
    LITERACY = "literacy"
    REAL_TIME = "real_time"
    GENERAL_KNOWLEDGE = "general_knowledge"
    OFF_TOPIC = "off_topic"
    MATH = "math"

class QuestionClassifier:
    """
    Intelligent question classifier for Nia learning assistant
    """
    
    def __init__(self):
        # Define keyword patterns for each question type
        self.real_time_keywords = [
            'today', 'now', 'current', 'weather', 'temperature',
            'time', 'latest', 'recent news', 'right now', 'this week',
            'yesterday', 'tomorrow', 'tonight'
        ]
        
        self.literacy_keywords = [
            'read', 'write', 'spell', 'word', 'letter', 'alphabet',
            'story', 'book', 'sentence', 'paragraph', 'essay',
            'vocabulary', 'meaning', 'define', 'pronunciation',
            'rhyme', 'syllable', 'grammar', 'punctuation',
            'noun', 'verb', 'adjective', 'synonym', 'antonym'
        ]
        
        self.math_keywords = [
            'add', 'subtract', 'multiply', 'divide', 'plus', 'minus',
            'times', 'math', 'number', 'count', 'calculate',
            'equation', 'problem', 'solve', 'answer is'
        ]
        
        self.off_topic_keywords = [
            'video game', 'youtube', 'tiktok', 'instagram',
            'buy', 'purchase', 'money', 'phone number',
            'password', 'hack'
        ]
    
    def classify(self, question: str) -> QuestionType:
        """
        Classify the question into a specific type
        
        Args:
            question: The user's question string
            
        Returns:
            QuestionType enum value
        """
        question_lower = question.lower()
        
        # Check for off-topic first (highest priority to redirect)
        if self._contains_keywords(question_lower, self.off_topic_keywords):
            return QuestionType.OFF_TOPIC
        
        # Check for real-time data questions
        if self._contains_keywords(question_lower, self.real_time_keywords):
            return QuestionType.REAL_TIME
        
        # Check for literacy questions (Nia's core competency)
        if self._contains_keywords(question_lower, self.literacy_keywords):
            return QuestionType.LITERACY
        
        # Check for math questions
        if self._contains_keywords(question_lower, self.math_keywords):
            return QuestionType.MATH
        
        # Default to general knowledge
        return QuestionType.GENERAL_KNOWLEDGE
    
    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """
        Check if text contains any of the specified keywords
        """
        return any(keyword in text for keyword in keywords)


class ResponseStrategyBuilder:
    """
    Builds appropriate response strategies based on question type
    """
    
    @staticmethod
    def get_strategy(question_type: QuestionType) -> Dict[str, Any]:
        """
        Get the response strategy for a given question type
        
        Returns:
            Dictionary with system_addition and configuration
        """
        strategies = {
            QuestionType.LITERACY: {
                "system_addition": """This is a LITERACY question - your core strength! 

Provide detailed, helpful educational content:
- Explain clearly with examples
- Use age-appropriate language
- Make it fun and engaging
- Encourage practice
- Use 1-2 emojis maximum

Example: If asked to spell a word, spell it out, give a memory tip, and ask them to use it in a sentence.""",
                "should_search": False,
                "temperature": 0.7
            },
            
            QuestionType.REAL_TIME: {
                "system_addition": """This question asks for REAL-TIME DATA you don't have access to.

Respond by:
1. Warmly acknowledge you don't have live data
2. Teach them HOW to find this information (search online, ask adult, check app)
3. Turn it into a learning opportunity (teach related vocabulary, concepts)
4. Stay encouraging and helpful

Example: "I don't have today's weather data, but let me teach you how to find it! You can search 'New York weather' with an adult's help. Let's learn weather words: sunny, cloudy, rainy..."

DO NOT make up or guess real-time information.""",
                "should_search": False,
                "temperature": 0.6
            },
            
            QuestionType.GENERAL_KNOWLEDGE: {
                "system_addition": """This is a GENERAL KNOWLEDGE question.

Answer helpfully and:
- Provide accurate, age-appropriate information
- Connect it to literacy/learning when possible
- Encourage curiosity
- Suggest related topics to explore
- Use simple, clear language

Example: "Great question about dinosaurs! Dinosaurs lived millions of years ago. Let's learn some dinosaur vocabulary words..."

Keep responses educational and engaging.""",
                "should_search": False,
                "temperature": 0.7
            },
            
            QuestionType.MATH: {
                "system_addition": """This is a MATH question.

You can help with basic math:
- Explain the concept step-by-step
- Show the work/process
- Use visual descriptions or examples
- Encourage them to practice
- Connect to real-world situations

Example: "Let's solve 5 + 3! Count with me: 5... 6, 7, 8. So 5 + 3 = 8! Can you think of 8 things around you?"

Keep it simple and encouraging.""",
                "should_search": False,
                "temperature": 0.5
            },
            
            QuestionType.OFF_TOPIC: {
                "system_addition": """This question is OFF-TOPIC or potentially inappropriate.

Respond by:
1. Stay kind and friendly (never scold)
2. Gently redirect to learning
3. Suggest interesting learning topics
4. Keep the student engaged positively

Example: "That's interesting! I'm here to help you with reading, writing, and learning. Would you like to read a fun story together, or learn some new vocabulary words?"

Never be harsh - always redirect with warmth.""",
                "should_search": False,
                "temperature": 0.7
            }
        }
        
        return strategies.get(question_type, strategies[QuestionType.GENERAL_KNOWLEDGE])


# Create global instances
classifier = QuestionClassifier()
strategy_builder = ResponseStrategyBuilder()

# Convenience functions for easy import
def classify_question(question: str) -> QuestionType:
    """Classify a question - convenience function"""
    return classifier.classify(question)

def get_response_strategy(question_type: QuestionType) -> Dict[str, Any]:
    """Get response strategy - convenience function"""
    return strategy_builder.get_strategy(question_type)