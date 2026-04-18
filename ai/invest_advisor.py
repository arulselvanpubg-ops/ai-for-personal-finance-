import os
from openai import OpenAI
from utils.helpers import get_env
from utils.monitoring import log_event, log_exception
from datetime import datetime

def get_nvidia_config():
    return {
        'api_key': get_env('NVIDIA_API_KEY'),
        'base_url': get_env('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1'),
        'model': get_env('NVIDIA_MODEL', 'meta/llama-3.1-70b-instruct')
    }

class InvestmentAdvisor:
    def __init__(self):
        config = get_nvidia_config()
        if not config['api_key']:
            raise ValueError("NVIDIA_API_KEY not set")
        
        self.client = OpenAI(
            base_url=config['base_url'],
            api_key=config['api_key']
        )
        self.model = config['model']
    
    def get_advice_stream(self, portfolio_data: list):
        """Generate professional investment advice as a stream."""
        if not portfolio_data:
            yield "Your portfolio is currently empty. Add some investments to get personalized AI advice!"
            return
            
        # Format portfolio for the prompt
        portfolio_str = "\n".join([
            f"- {p['ticker']}: {p['quantity']} units at ₹{p['avg_cost']:.2f} (Current: ₹{p['current_price']:.2f}, P/L: ₹{p['pl']:.2f})"
            for p in portfolio_data
        ])
        
        total_value = sum(p['quantity'] * p['current_price'] for p in portfolio_data)
        total_pl = sum(p['pl'] for p in portfolio_data)
        
        prompt = f"""
As a professional AI Investment Advisor, analyze the following portfolio:
{portfolio_str}

Total Portfolio Value: ₹{total_value:,.2f}
Total Profit/Loss: ₹{total_pl:,.2f}

Provide a concise report with:
1. **Analysis**: Performance and risk assessment.
2. **Audit**: Diversification status.
3. **Action**: Rebalancing or diversification suggestions.
4. **Next Steps**: 2 specific actions.

Tone: Professional and analytical. Currency: Indian Rupees (₹).
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                max_tokens=600,
                temperature=0.7
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            log_exception("invest_advice_stream_failed", e)
            yield "Unable to generate investment advice right now. Please check your AI configuration."

    def get_advice(self, portfolio_data: list) -> str:
        """Fallback for non-streaming calls."""
        return "".join(list(self.get_advice_stream(portfolio_data)))

# Global instance
try:
    advisor = InvestmentAdvisor()
except ValueError as e:
    log_event("warning", "invest_advisor_unavailable", reason=str(e))
    advisor = None

def get_ai_investment_advice(portfolio_data: list, stream: bool = False):
    """Get AI investment advice."""
    if not advisor:
        return "Investment advice is not available because AI is not configured correctly."
    
    if stream:
        return advisor.get_advice_stream(portfolio_data)
    return advisor.get_advice(portfolio_data)
