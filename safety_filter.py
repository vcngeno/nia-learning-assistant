from typing import Dict, List, Tuple
import re
import os

class ChildSafetyFilter:
    """Multi-layer content safety system for child interactions"""
    
    def __init__(self):
        # Safety filter doesn't need API key
        self.blocked_keywords = [
            "violence", "weapon", "blood", "kill", "murder",
            "sexual", "porn", "nude", "sex",
            "drug", "alcohol", "cigarette", "tobacco",
            "suicide", "self-harm", "cutting",
            "hate speech", "racist", "discriminat",
        ]
        
        self.warning_patterns = [
            r'\b(how to make|build a)\s+(bomb|weapon)',
            r'\b(buy|purchase)\s+(drugs|alcohol)',
            r'\bhurt\s+(myself|yourself|someone)',
        ]
    
    def check_input_safety(self, user_input: str) -> Tuple[bool, str]:
        user_input_lower = user_input.lower()
        
        for keyword in self.blocked_keywords:
            if keyword in user_input_lower:
                return False, f"inappropriate_content:{keyword}"
        
        for pattern in self.warning_patterns:
            if re.search(pattern, user_input_lower):
                return False, f"suspicious_pattern"
        
        return True, "safe"
    
    def validate_output(self, ai_response: str, age_level: int) -> Tuple[bool, str]:
        is_safe, reason = self.check_input_safety(ai_response)
        if not is_safe:
            return False, f"output_unsafe:{reason}"
        
        return True, "approved"
