import os
from openai import OpenAI
from core.db import ChatHistory
from core.finance import get_monthly_summary
from typing import List, Dict
from utils.helpers import get_env
from utils.monitoring import log_event, log_exception
from utils.validators import sanitize_input

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
- Monthly Income: ₹{summary['income']:.2f}
- Monthly Expenses: ₹{summary['expenses']:.2f}
- Net Cash Flow: ₹{summary['net']:.2f}

Top spending categories: {', '.join([f"{cat}: ₹{amt:.2f}" for cat, amt in list(summary['categories'].items())[:3]])}

Guidelines:
- Be helpful, encouraging, and professional
- Focus on practical financial advice tailored to their spending patterns
- Use simple language, avoid jargon unless explaining it
- Keep responses concise but comprehensive (aim for 2-4 sentences)
- Always prioritize user's financial well-being and long-term goals
- If asked about investments, remind about risks and suggest consulting professionals
- Reference their actual spending data when giving advice
- Be proactive in suggesting improvements based on their financial data

Remember previous conversation context when responding. If this is a follow-up question, build upon previous advice."""
        
        return prompt
    
    def chat(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """Send message to FinSight Chat and get response."""
        if conversation_history is None:
            conversation_history = []
        user_message = sanitize_input(user_message, max_length=1000)
        if not user_message:
            return "Please enter a message so I can help."
        
        # Get recent chat history (last 10 exchanges to keep context manageable)
        recent_history = ChatHistory.find_recent(limit=20)  # 20 messages = 10 exchanges
        
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        # Add recent history (limit to prevent token overflow)
        history_messages = []
        for hist in recent_history:
            history_messages.extend([
                {"role": "user", "content": hist['user_message']},
                {"role": "assistant", "content": hist['ai_response']}
            ])
        
        # Keep only the most recent history to stay within token limits
        history_messages = history_messages[-20:]  # Last 10 exchanges
        messages.extend(history_messages)
        
        # Add current conversation
        for msg in conversation_history[-10:]:  # Last 10 messages
            messages.append(msg)
        
        messages.append({"role": "user", "content": user_message})
        
        # Retry logic for API calls
        max_retries = 2
        for attempt in range(max_retries + 1):
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
                log_event("info", "chat_response_generated", history_count=len(recent_history))
                
                return ai_response
                
            except Exception as e:
                error_msg = str(e).lower()
                log_exception("chat_request_failed", e, attempt=attempt)
                
                # Check for specific error types
                if "401" in error_msg or "unauthorized" in error_msg:
                    return "Authentication failed. Please check the API key configuration."
                elif "429" in error_msg or "rate limit" in error_msg:
                    if attempt < max_retries:
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return "I'm receiving too many requests. Please wait a moment and try again."
                elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                    if attempt < max_retries:
                        import time
                        time.sleep(1)
                        continue
                    return "The AI service is temporarily unavailable. Please try again later."
                else:
                    if attempt < max_retries:
                        import time
                        time.sleep(1)
                        continue
                    return "Sorry, I'm having trouble responding right now. Please try again in a moment."

# Global instance
try:
    chatbot = FinSightChat()
except ValueError as e:
    log_event("warning", "chat_unavailable", reason=str(e))
    chatbot = None

def send_chat_message(user_message: str, history: List[Dict] = None) -> str:
    """Convenience function for chat."""
    if chatbot:
        return chatbot.chat(user_message, history)
    return "Chat is not available right now because the AI configuration is missing."
