from typing import Dict, List, Tuple
import re
import os

class ChildSafetyFilter:
    """Multi-layer content safety system for child interactions"""
    
    def __init__(self):
        # Strict input filtering - what users can ask
        self.blocked_input_keywords = [
            "sexual", "porn", "nude", "sex",
            "drug", "alcohol", "cigarette", "tobacco",
            "suicide", "self-harm", "cutting",
            "hate speech", "racist",
        ]
        
        # More lenient output filtering - allows educational content
        self.blocked_output_keywords = [
            "pornography", "sexual content", "explicit",
            "how to make drugs", "how to hurt",
        ]
        
        self.warning_patterns = [
            r'\b(how to make|build a)\s+(bomb|weapon)',
            r'\b(buy|purchase)\s+(drugs|alcohol)',
            r'\bhurt\s+(myself|yourself|someone)',
        ]
    
    def check_input_safety(self, user_input: str) -> Tuple[bool, str]:
        """Check if user input is safe - STRICT filtering"""
        user_input_lower = user_input.lower()
        
        for keyword in self.blocked_input_keywords:
            if keyword in user_input_lower:
                return False, f"inappropriate_content:{keyword}"
        
        for pattern in self.warning_patterns:
            if re.search(pattern, user_input_lower):
                return False, f"suspicious_pattern"
        
        return True, "safe"
    
    def validate_output(self, ai_response: str, age_level: int) -> Tuple[bool, str]:
        """Check if AI output is safe - LENIENT filtering for educational content"""
        ai_response_lower = ai_response.lower()
        
        # Only block truly inappropriate output content
        for keyword in self.blocked_output_keywords:
            if keyword in ai_response_lower:
                return False, f"output_unsafe:{keyword}"
        
        # Check for explicit harmful instructions
        harmful_patterns = [
            r'here\'s how to (hurt|harm|kill)',
            r'steps to (commit|perform) (suicide|self-harm)',
        ]
        
        for pattern in harmful_patterns:
            if re.search(pattern, ai_response_lower):
                return False, "harmful_instructions"
        
        return True, "approved"