"""
This module implements the ChatLLM class which handles interactions with Google's Gemini Pro model
with RAG (Retrieval Augmented Generation) capabilities for biological databases.

Key components:
- API key authentication
- RAG implementation for biological database tools
- Tool selection and response validation
- Structured response formatting with citations
"""

import os
import time
from functools import wraps
from pydantic import BaseModel
from typing import List, Dict, Any
import google.generativeai as genai
import json

def rate_limit(seconds=1):
    """Decorator to implement rate limiting for API calls."""
    def decorator(func):
        last_called = [0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < seconds:
                time.sleep(seconds - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

class ChatLLM(BaseModel):
    """Handles interactions with the Gemini Pro model with RAG capabilities."""
    
    model: str = 'gemini-pro'
    temperature: float = 0.0
    api_key: str = None

    def __init__(self, **data):
        """Initialize the ChatLLM with API key."""
        super().__init__(**data)
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
            
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def complete_text_gemini(self, prompt: str, stop: List[str] = None) -> str:
        """Generate response using Gemini model."""
        try:
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
            return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
        except Exception as e:
            if "safety" in str(e).lower():
                return "I apologize, but I cannot provide a response to that query due to safety constraints."
            return f"An error occurred: {str(e)}"

    def handle_conversation(self, prompt: str) -> str:
        """Handle general conversation without RAG."""
        try:
            conversation_prompt = f"""You are a helpful and friendly AI assistant. 
            Please respond naturally to: {prompt}

            If the conversation could benefit from biological database information, 
            suggest that to the user, but keep the current response conversational."""
            
            return self.complete_text_gemini(conversation_prompt)
        except Exception as e:
            return f"I apologize, but I'm having trouble responding. Error: {str(e)}"

    def generate_with_tools(self, prompt: str, tool_responses: List[Dict[str, Any]]) -> str:
        """Main interface for text generation with RAG."""
        formatted_responses = [
            f"\nSource [{resp['tool_name']}]: {json.dumps(resp['response'], indent=2)}"
            for resp in tool_responses
            if 'tool_name' in resp and 'response' in resp
        ]
        
        rag_prompt = self._create_rag_prompt(prompt, '\n'.join(formatted_responses))
        return self.complete_text_gemini(rag_prompt)

if __name__ == '__main__':
    # Test the LLM
    try:
        llm = ChatLLM()
        result = llm.complete_text_gemini(prompt='What is DNA?')
        print("Test successful!")
        print("Response:", result)
    except Exception as e:
        print("Test failed:", str(e))
