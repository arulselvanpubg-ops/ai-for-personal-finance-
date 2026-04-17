import os
from openai import OpenAI
from core.db import ChatHistory
from core.finance import get_monthly_summary
from typing import List, Dict
from utils.helpers import get_env

NVIDIA_API_KEY = get_env('NVIDIA_API_KEY')
NVIDIA_BASE_URL = get_env('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1')
NVIDIA_MODEL = get_env('NVIDIA_MODEL', 'meta/llama-3.1-70b-instruct')

class FinSightChat:
    def __init__(self):
        if not NVIDIA_API_KEY:
            raise ValueError("NVIDIA_API_KEY not set")
        
        self.client = OpenAI(
            base_url=NVIDIA_BASE_URL,
            api_key=NVIDIA_API_KEY
        )
    
    def get_system_prompt(self) -> str:
        """Generate system prompt with user's financial context."""
        # Get recent financial summary
        from datetime import datetime
        now = datetime.now()
        summary = get_monthly_summary(now.year, now.month)
        
        prompt = f"""You are FinSight AI, a friendly and knowledgeable personal finance assistant.

User's current financial snapshot:
- Monthly Income: ${summary['income']:.2f}
- Monthly Expenses: ${summary['expenses']:.2f}
- Net Cash Flow: ${summary['net']:.2f}

Top spending categories: {', '.join([f"{cat}: ${amt:.2f}" for cat, amt in list(summary['categories'].items())[:3]])}

Guidelines:
- Be helpful, encouraging, and professional
- Focus on practical financial advice
- Use simple language, avoid jargon unless explaining it
- Keep responses concise but comprehensive
- Always prioritize user's financial well-being
- If asked about investments, remind about risks and suggest consulting professionals

Remember previous conversation context when responding."""
        
        return prompt
    
    def chat(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """Send message to FinSight Chat and get response."""
        if conversation_history is None:
            conversation_history = []
        
        # Get recent chat history (last 10 exchanges)
        recent_history = ChatHistory.find_recent(limit=20)
        recent_history.reverse()  # Oldest first
        
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        # Add recent history
        for hist in recent_history:
            messages.append({"role": "user", "content": hist['user_message']})
            messages.append({"role": "assistant", "content": hist['ai_response']})
        
        # Add current conversation
        for msg in conversation_history[-10:]:  # Last 10 messages
            messages.append(msg)
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=messages,
                stream=False,
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Save to history
            ChatHistory.create(user_message, ai_response)
            
            return ai_response
            
        except Exception as e:
            return f"Sorry, I'm having trouble connecting right now. Error: {str(e)}"

# Global instance
try:
    chatbot = FinSightChat()
except ValueError as e:
    print(f"Warning: {e}")
    chatbot = None

def send_chat_message(user_message: str, history: List[Dict] = None) -> str:
    """Convenience function for chat."""
    if chatbot:
        return chatbot.chat(user_message, history)
    return "Chat is not available because `NVIDIA_API_KEY` is not configured."
