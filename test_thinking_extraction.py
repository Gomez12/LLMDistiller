#!/usr/bin/env python3
"""
Test script to verify thinking extraction functionality.
"""

import sys
import os
import re
from typing import Optional
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Direct implementation for testing
class ThinkingExtractor:
    """Utility class for extracting thinking from LLM responses."""
    
    @staticmethod
    def extract_thinking(content: str, separate_reasoning: Optional[str] = None) -> tuple[str, Optional[str]]:
        """Extract thinking/reasoning from model response.
        
        Args:
            content: The full response content
            separate_reasoning: Separate reasoning context if provided by model
            
        Returns:
            Tuple of (cleaned_content, thinking)
        """
        thinking = None
        cleaned_content = content
        
        # If separate reasoning is provided, use it
        if separate_reasoning and separate_reasoning.strip():
            thinking = separate_reasoning.strip()
            return cleaned_content, thinking
        
        # Look for thinking tags in the content
        # Pattern: <thinking>...</thinking>
        thinking_pattern = r'<thinking>(.*?)</thinking>'
        thinking_match = re.search(thinking_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            # Remove thinking tags from content
            cleaned_content = re.sub(thinking_pattern, '', content, flags=re.DOTALL | re.IGNORECASE).strip()
        else:
            # Look for reasoning tags as fallback
            reasoning_pattern = r'<reasoning>(.*?)</reasoning>'
            reasoning_match = re.search(reasoning_pattern, content, re.DOTALL | re.IGNORECASE)
            
            if reasoning_match:
                thinking = reasoning_match.group(1).strip()
                # Remove reasoning tags from content
                cleaned_content = re.sub(reasoning_pattern, '', content, flags=re.DOTALL | re.IGNORECASE).strip()
        
        return cleaned_content, thinking

def test_thinking_extraction():
    """Test thinking extraction from various response formats."""
    
    # Test 1: Response with thinking tags
    response1 = """<thinking>
I need to solve this step by step.
First, I'll analyze the question.
Then I'll formulate my answer.
</thinking>

The answer is 42 because it's the answer to life, the universe, and everything."""
    
    cleaned1, thinking1 = ThinkingExtractor.extract_thinking(response1)
    print("Test 1 - Thinking tags:")
    print(f"Original: {repr(response1[:50])}...")
    print(f"Cleaned: {repr(cleaned1)}")
    print(f"Thinking: {repr(thinking1)}")
    print()
    
    # Test 2: Response with reasoning tags
    response2 = """<reasoning>
Let me think about this carefully.
The question asks for a calculation.
I need to multiply 6 by 7.
</reasoning>

The result is 42."""
    
    cleaned2, thinking2 = ThinkingExtractor.extract_thinking(response2)
    print("Test 2 - Reasoning tags:")
    print(f"Original: {repr(response2[:50])}...")
    print(f"Cleaned: {repr(cleaned2)}")
    print(f"Thinking: {repr(thinking2)}")
    print()
    
    # Test 3: Response without thinking tags
    response3 = "The answer is simply 42."
    
    cleaned3, thinking3 = ThinkingExtractor.extract_thinking(response3)
    print("Test 3 - No thinking tags:")
    print(f"Original: {repr(response3)}")
    print(f"Cleaned: {repr(cleaned3)}")
    print(f"Thinking: {repr(thinking3)}")
    print()
    
    # Test 4: Response with separate reasoning
    response4 = "The answer is 42."
    separate_reasoning = "I calculated this by multiplying 6 by 7."
    
    cleaned4, thinking4 = ThinkingExtractor.extract_thinking(response4, separate_reasoning)
    print("Test 4 - Separate reasoning:")
    print(f"Original: {repr(response4)}")
    print(f"Separate reasoning: {repr(separate_reasoning)}")
    print(f"Cleaned: {repr(cleaned4)}")
    print(f"Thinking: {repr(thinking4)}")
    print()
    
    # Test 5: Empty response
    response5 = ""
    
    cleaned5, thinking5 = ThinkingExtractor.extract_thinking(response5)
    print("Test 5 - Empty response:")
    print(f"Original: {repr(response5)}")
    print(f"Cleaned: {repr(cleaned5)}")
    print(f"Thinking: {repr(thinking5)}")
    print()
    
    # Verify results
    assert thinking1 == "I need to solve this step by step.\nFirst, I'll analyze the question.\nThen I'll formulate my answer."
    assert cleaned1 == "The answer is 42 because it's the answer to life, the universe, and everything."
    
    assert thinking2 == "Let me think about this carefully.\nThe question asks for a calculation.\nI need to multiply 6 by 7."
    assert cleaned2 == "The result is 42."
    
    assert thinking3 is None
    assert cleaned3 == "The answer is simply 42."
    
    assert thinking4 == "I calculated this by multiplying 6 by 7."
    assert cleaned4 == "The answer is 42."
    
    assert thinking5 is None
    assert cleaned5 == ""
    
    print("✓ All tests passed!")

if __name__ == "__main__":
    test_thinking_extraction()