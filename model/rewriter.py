"""
Rule-based text simplifier with age-level adaptation
Includes autism-friendly mode with short sentences and calm tone
"""
import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class AgeAppropriateRewriter:
    """Rewrite content to be age-appropriate and autism-friendly"""

    def __init__(self):
        self.max_sentence_length = {
            'elementary': 15,
            'middle': 20,
            'high': 30
        }

    def rewrite(self, text: str, grade_level: str, autism_mode: bool = False) -> str:
        """Rewrite text to be age-appropriate"""
        # Determine complexity level
        level = self._determine_level(grade_level)

        # Split into sentences
        sentences = self._split_sentences(text)

        # Process each sentence
        rewritten = []
        for sentence in sentences:
            if autism_mode:
                sentence = self._autism_friendly(sentence)

            sentence = self._simplify_for_level(sentence, level)
            rewritten.append(sentence)

        return ' '.join(rewritten)

    def _determine_level(self, grade_level: str) -> str:
        """Determine complexity level from grade"""
        grade_num = ''.join(filter(str.isdigit, grade_level))

        if not grade_num or grade_num in ['1', '2', '3', '4', '5']:
            return 'elementary'
        elif grade_num in ['6', '7', '8']:
            return 'middle'
        else:
            return 'high'

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _autism_friendly(self, sentence: str) -> str:
        """Make sentence autism-friendly: short, clear, literal"""
        # Remove metaphors and idioms
        replacements = {
            'piece of cake': 'easy',
            'costs an arm and a leg': 'expensive',
            'under the weather': 'sick',
            'hit the books': 'study',
        }

        for idiom, replacement in replacements.items():
            sentence = sentence.replace(idiom, replacement)

        # Keep sentences short (max 12 words for autism mode)
        words = sentence.split()
        if len(words) > 12:
            mid = len(words) // 2
            sentence = ' '.join(words[:mid]) + '. ' + ' '.join(words[mid:])

        return sentence

    def _simplify_for_level(self, sentence: str, level: str) -> str:
        """Simplify sentence based on grade level"""
        # Complex word replacements for elementary
        if level == 'elementary':
            simple_words = {
                'utilize': 'use',
                'demonstrate': 'show',
                'acquire': 'get',
                'comprehend': 'understand',
                'assist': 'help',
                'commence': 'start',
                'terminate': 'end',
            }

            for complex_word, simple in simple_words.items():
                sentence = re.sub(r'\b' + complex_word + r'\b', simple, sentence, flags=re.IGNORECASE)

        return sentence
