"""
Enhanced AI Services with multiple API integrations
Supports NVIDIA, Google Gemini, Hugging Face, and OpenAI APIs
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import openai
from google import generativeai as genai
from huggingface_hub import InferenceClient
from utils.helpers import get_env
from utils.monitoring import log_event, log_exception

class EnhancedAIServices:
    """Enhanced AI services with multiple API providers"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
        self.primary_provider = self._get_primary_provider()
    
    def _initialize_providers(self) -> Dict[str, Any]:
        """Initialize all available API providers"""
        providers = {}
        
        # NVIDIA NIM API
        nvidia_key = get_env('NVIDIA_API_KEY')
        if nvidia_key:
            providers['nvidia'] = {
                'client': openai.OpenAI(
                    base_url=get_env('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1'),
                    api_key=nvidia_key
                ),
                'model': get_env('NVIDIA_MODEL', 'meta/llama-3.1-70b-instruct'),
                'available': True
            }
            log_event("info", "nvidia_api_initialized")
        
        # Google Gemini API
        google_key = get_env('GOOGLE_API_KEY')
        if google_key:
            try:
                genai.configure(api_key=google_key)
                providers['google'] = {
                    'client': genai.GenerativeModel(
                        model_name=get_env('GOOGLE_MODEL', 'gemini-1.5-pro')
                    ),
                    'model': get_env('GOOGLE_MODEL', 'gemini-1.5-pro'),
                    'available': True
                }
                log_event("info", "google_api_initialized")
            except Exception as e:
                log_exception("google_api_init_failed", e)
                providers['google'] = {'available': False, 'error': str(e)}
        
        # Hugging Face API
        hf_key = get_env('HUGGINGFACE_API_KEY')
        if hf_key:
            try:
                providers['huggingface'] = {
                    'client': InferenceClient(
                        model=get_env('HF_MODEL', 'mistralai/Mixtral-8x7B-Instruct-v0.1'),
                        token=hf_key
                    ),
                    'model': get_env('HF_MODEL', 'mistralai/Mixtral-8x7B-Instruct-v0.1'),
                    'available': True
                }
                log_event("info", "huggingface_api_initialized")
            except Exception as e:
                log_exception("huggingface_api_init_failed", e)
                providers['huggingface'] = {'available': False, 'error': str(e)}
        
        # OpenAI API
        openai_key = get_env('OPENAI_API_KEY')
        if openai_key:
            try:
                providers['openai'] = {
                    'client': openai.OpenAI(api_key=openai_key),
                    'model': get_env('OPENAI_MODEL', 'gpt-4'),
                    'available': True
                }
                log_event("info", "openai_api_initialized")
            except Exception as e:
                log_exception("openai_api_init_failed", e)
                providers['openai'] = {'available': False, 'error': str(e)}
        
        return providers
    
    def _get_primary_provider(self) -> str:
        """Get the primary AI provider based on availability and priority"""
        priority_order = ['nvidia', 'openai', 'google', 'huggingface']
        
        for provider in priority_order:
            if provider in self.providers and self.providers[provider].get('available'):
                return provider
        
        return 'fallback'  # Use local fallback if no APIs available
    
    def generate_insight(self, prompt: str, provider: Optional[str] = None) -> str:
        """Generate AI insight using available provider"""
        provider = provider or self.primary_provider
        
        if provider == 'fallback':
            return self._fallback_response(prompt)
        
        try:
            if provider == 'nvidia':
                return self._nvidia_generate(prompt)
            elif provider == 'google':
                return self._google_generate(prompt)
            elif provider == 'huggingface':
                return self._huggingface_generate(prompt)
            elif provider == 'openai':
                return self._openai_generate(prompt)
            else:
                return f"Provider {provider} not available"
        except Exception as e:
            log_exception("ai_generation_failed", e, provider=provider)
            return self._fallback_response(prompt)
    
    def _nvidia_generate(self, prompt: str) -> str:
        """Generate using NVIDIA NIM API"""
        client = self.providers['nvidia']['client']
        model = self.providers['nvidia']['model']
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    def _google_generate(self, prompt: str) -> str:
        """Generate using Google Gemini API"""
        model = self.providers['google']['client']
        
        response = model.generate_content(prompt)
        return response.text
    
    def _huggingface_generate(self, prompt: str) -> str:
        """Generate using Hugging Face API"""
        client = self.providers['huggingface']['client']
        
        messages = [{"role": "user", "content": prompt}]
        response = client.chat_completion(messages, max_tokens=800, temperature=0.7)
        return response.choices[0].message.content
    
    def _openai_generate(self, prompt: str) -> str:
        """Generate using OpenAI API"""
        client = self.providers['openai']['client']
        model = self.providers['openai']['model']
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback response when no APIs are available"""
        return "AI insights are currently unavailable. Please configure API keys to enable advanced AI features."
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                'available': provider.get('available', False),
                'model': provider.get('model', 'N/A'),
                'error': provider.get('error', None)
            }
        return status
    
    def enhance_dashboard_insights(self, financial_data: Dict) -> Dict[str, str]:
        """Generate enhanced dashboard insights"""
        insights = {}
        
        # Financial Health Analysis
        health_prompt = f"""
        Analyze this financial data and provide insights:
        Income: Rs.{financial_data.get('income', 0):,.2f}
        Expenses: Rs.{financial_data.get('expenses', 0):,.2f}
        Net: Rs.{financial_data.get('net', 0):,.2f}
        Categories: {financial_data.get('categories', {})}
        
        Provide a concise financial health analysis (2-3 sentences) focusing on:
        1. Overall financial health status
        2. Key areas of concern or improvement
        3. One actionable recommendation
        """
        
        insights['health_analysis'] = self.generate_insight(health_prompt)
        
        # Spending Pattern Analysis
        spending_prompt = f"""
        Analyze these spending patterns and provide insights:
        {financial_data.get('categories', {})}
        
        Provide spending pattern insights (2-3 sentences) focusing on:
        1. Top spending categories and their impact
        2. Unusual spending patterns
        3. Optimization suggestions
        """
        
        insights['spending_analysis'] = self.generate_insight(spending_prompt)
        
        # Financial Goals
        goals_prompt = f"""
        Based on this financial data:
        Monthly Income: Rs.{financial_data.get('income', 0):,.2f}
        Monthly Expenses: Rs.{financial_data.get('expenses', 0):,.2f}
        Monthly Savings: Rs.{financial_data.get('net', 0):,.2f}
        
        Provide financial goal recommendations (2-3 sentences) focusing on:
        1. Realistic savings targets
        2. Investment suggestions
        3. Risk management advice
        """
        
        insights['goals_recommendations'] = self.generate_insight(goals_prompt)
        
        return insights

# Global enhanced AI services instance
enhanced_ai = EnhancedAIServices()


def get_enhanced_dashboard_insights(financial_data: Dict) -> Dict[str, str]:
    """Get enhanced AI insights for dashboard"""
    return enhanced_ai.enhance_dashboard_insights(financial_data)


def get_api_provider_status() -> Dict[str, Any]:
    """Get status of all API providers"""
    return enhanced_ai.get_provider_status()


def setup_api_keys_guide() -> str:
    """Return setup guide for API keys"""
    return """
# API Keys Setup Guide

## 1. NVIDIA NIM API (Recommended)
1. Go to https://build.nvidia.com/
2. Sign up and get API key
3. Set environment variable: NVIDIA_API_KEY=your_key_here
4. Optional: NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
5. Optional: NVIDIA_MODEL=meta/llama-3.1-70b-instruct

## 2. Google Gemini API
1. Go to https://aistudio.google.com/app/apikey
2. Create new API key
3. Set environment variable: GOOGLE_API_KEY=your_key_here
4. Optional: GOOGLE_MODEL=gemini-1.5-pro

## 3. Hugging Face API
1. Go to https://huggingface.co/settings/tokens
2. Create new token
3. Set environment variable: HUGGINGFACE_API_KEY=your_token_here
4. Optional: HF_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1

## 4. OpenAI API
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Set environment variable: OPENAI_API_KEY=your_key_here
4. Optional: OPENAI_MODEL=gpt-4

## Environment Variables Setup
For local development, set these in your system environment:
- Windows: set NVIDIA_API_KEY=your_key_here
- Mac/Linux: export NVIDIA_API_KEY=your_key_here

For Streamlit Cloud, add these to your app secrets:
- NVIDIA_API_KEY
- GOOGLE_API_KEY
- HUGGINGFACE_API_KEY
- OPENAI_API_KEY
"""
