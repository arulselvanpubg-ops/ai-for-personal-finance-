#!/usr/bin/env python3
"""
API Keys Setup Script
Helps users configure API keys for enhanced AI features
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with API key templates"""
    env_content = """# FinSight AI - API Keys Configuration
# Copy this file to .env and fill in your actual API keys

# NVIDIA NIM API (Recommended - Free tier available)
# Get your key from: https://build.nvidia.com/
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=meta/llama-3.1-70b-instruct

# Google Gemini API (Free tier available)
# Get your key from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_MODEL=gemini-1.5-pro

# Hugging Face API (Free tier available)
# Get your key from: https://huggingface.co/settings/tokens
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
HF_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1

# OpenAI API (Paid)
# Get your key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Database Configuration (already configured)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=finsight
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SQLITE_DB_PATH=data/finsight.db
"""
    
    env_file = Path(".env")
    if env_file.exists():
        print(".env file already exists. Please edit it directly.")
        return False
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("Created .env file with API key templates.")
    print("Please edit .env file and add your actual API keys.")
    return True

def check_api_keys():
    """Check which API keys are configured"""
    from utils.helpers import get_env
    
    print("=== API Keys Status ===")
    
    keys = {
        'NVIDIA API Key': get_env('NVIDIA_API_KEY'),
        'Google API Key': get_env('GOOGLE_API_KEY'),
        'Hugging Face API Key': get_env('HUGGINGFACE_API_KEY'),
        'OpenAI API Key': get_env('OPENAI_API_KEY')
    }
    
    configured = 0
    for name, value in keys.items():
        status = "Configured" if value else "Not configured"
        icon = "Configured" if value else "Not configured"
        print(f"{name}: {status}")
        if value:
            configured += 1
    
    print(f"\n{configured}/4 API keys configured")
    
    if configured == 0:
        print("\nNo API keys configured. AI features will use basic functionality.")
        print("Run 'python setup_api_keys.py --create-env' to create .env file template.")
    elif configured < 4:
        print("\nSome API keys configured. Enhanced AI features partially available.")
    else:
        print("\nAll API keys configured! Full AI features available.")
    
    return configured

def test_api_connections():
    """Test API connections"""
    print("\n=== Testing API Connections ===")
    
    try:
        from ai.enhanced_services import get_api_provider_status
        status = get_api_provider_status()
        
        for provider, info in status.items():
            if info['available']:
                print(f"Provider: {provider.title()} - Available")
                print(f"  Model: {info['model']}")
            else:
                print(f"Provider: {provider.title()} - Not available")
                if info.get('error'):
                    print(f"  Error: {info['error']}")
        
        return True
    except Exception as e:
        print(f"Error testing API connections: {e}")
        return False

def show_setup_guide():
    """Show detailed setup guide"""
    guide = """
# API Keys Setup Guide

## Quick Setup (Recommended)

1. **NVIDIA NIM API** (Free tier available)
   - Go to: https://build.nvidia.com/
   - Sign up for free account
   - Get your API key
   - Add to .env: NVIDIA_API_KEY=your_key_here

2. **Google Gemini API** (Free tier available)
   - Go to: https://aistudio.google.com/app/apikey
   - Create new API key
   - Add to .env: GOOGLE_API_KEY=your_key_here

3. **Hugging Face API** (Free tier available)
   - Go to: https://huggingface.co/settings/tokens
   - Create new token
   - Add to .env: HUGGINGFACE_API_KEY=your_token_here

## Environment Setup

### For Local Development:
1. Create .env file: python setup_api_keys.py --create-env
2. Edit .env file with your API keys
3. Restart your application

### For Windows:
set NVIDIA_API_KEY=your_key_here
set GOOGLE_API_KEY=your_key_here

### For Mac/Linux:
export NVIDIA_API_KEY=your_key_here
export GOOGLE_API_KEY=your_key_here

### For Streamlit Cloud:
Add API keys to your app secrets in Streamlit dashboard:
- NVIDIA_API_KEY
- GOOGLE_API_KEY
- HUGGINGFACE_API_KEY
- OPENAI_API_KEY

## Benefits of API Integration

- **Enhanced AI Insights**: Advanced financial analysis
- **Better Categorization**: More accurate transaction categorization
- **Predictive Analytics**: Cash flow forecasting
- **Personalized Recommendations**: Tailored financial advice
- **Real-time Analysis**: Faster processing with cloud AI

## Priority Order

The system will use APIs in this priority:
1. NVIDIA NIM (Fast, free tier available)
2. OpenAI GPT-4 (High quality, paid)
3. Google Gemini (Good quality, free tier)
4. Hugging Face (Good quality, free tier)
"""
    
    print(guide)

def main():
    """Main setup function"""
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--create-env":
            create_env_file()
        elif arg == "--check":
            check_api_keys()
        elif arg == "--test":
            test_api_connections()
        elif arg == "--guide":
            show_setup_guide()
        else:
            print("Usage: python setup_api_keys.py [--create-env|--check|--test|--guide]")
    else:
        print("=== FinSight AI - API Keys Setup ===")
        print("\nOptions:")
        print("  --create-env  Create .env file with templates")
        print("  --check      Check current API key configuration")
        print("  --test       Test API connections")
        print("  --guide      Show detailed setup guide")
        
        # Quick check
        configured = check_api_keys()
        
        if configured == 0:
            print("\nRecommendation: Run 'python setup_api_keys.py --create-env' to get started")

if __name__ == "__main__":
    main()
