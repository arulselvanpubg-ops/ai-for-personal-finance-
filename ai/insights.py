import os
from openai import OpenAI
from core.finance import get_monthly_summary
from datetime import datetime
from utils.helpers import get_env
from utils.monitoring import log_event, log_exception

NVIDIA_API_KEY = get_env('NVIDIA_API_KEY')
NVIDIA_BASE_URL = get_env('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1')
NVIDIA_MODEL = get_env('NVIDIA_MODEL', 'meta/llama-3.1-70b-instruct')

class FinancialInsights:
    def __init__(self):
        if not NVIDIA_API_KEY:
            raise ValueError("NVIDIA_API_KEY not set")
        
        self.client = OpenAI(
            base_url=NVIDIA_BASE_URL,
            api_key=NVIDIA_API_KEY
        )
    
    def _generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                max_tokens=800,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            log_exception("insights_generation_failed", e)
            raise e
            
    def generate_monthly_summary(self, year: int, month: int) -> str:
        """Generate a natural language summary of monthly finances."""
        summary = get_monthly_summary(year, month)
        
        prompt = f"""
Based on the following financial data for {datetime(year, month, 1).strftime('%B %Y')}, 
generate a concise, encouraging monthly financial summary:

Income: ₹{summary['income']:.2f}
Expenses: ₹{summary['expenses']:.2f}
Net: ₹{summary['net']:.2f}
Top categories: {', '.join([f"{cat}: ₹{amt:.2f}" for cat, amt in list(summary['categories'].items())[:5]])}

Write 2-3 paragraphs that:
- Highlights positive trends
- Identifies areas for improvement
- Provides gentle encouragement
- Uses friendly, supportive tone
"""
        try:
            return self._generate(prompt)
        except Exception:
            return "Unable to generate a monthly summary right now. Please try again shortly."
    
    def forecast_cash_flow(self, months_ahead: int = 3) -> str:
        """Generate cash flow forecast."""
        now = datetime.now()
        summaries = []
        for i in range(3, 0, -1):
            month = now.month - i
            year = now.year
            if month <= 0:
                month += 12
                year -= 1
            summaries.append(get_monthly_summary(year, month))
        
        prompt = f"""
Analyze the following 3-month financial trend and forecast the next {months_ahead} months:

Month 1: Income ₹{summaries[0]['income']:.2f}, Expenses ₹{summaries[0]['expenses']:.2f}, Net ₹{summaries[0]['net']:.2f}
Month 2: Income ₹{summaries[1]['income']:.2f}, Expenses ₹{summaries[1]['expenses']:.2f}, Net ₹{summaries[1]['net']:.2f}
Month 3: Income ₹{summaries[2]['income']:.2f}, Expenses ₹{summaries[2]['expenses']:.2f}, Net ₹{summaries[2]['net']:.2f}

Provide a forecast that includes:
- Expected income and expense trends
- Potential savings opportunities
- Risk factors to watch
- Actionable recommendations
"""
        try:
            return self._generate(prompt)
        except Exception:
            return "Unable to generate a forecast right now. Please try again shortly."
    
    def suggest_budget(self) -> str:
        """Suggest budget based on past spending."""
        summary = get_monthly_summary(datetime.now().year, datetime.now().month)
        
        prompt = f"""
Based on current spending of ₹{summary['expenses']:.2f} per month with income of ₹{summary['income']:.2f},
suggest a realistic monthly budget allocation.

Current category breakdown: {', '.join([f"{cat}: ₹{amt:.2f}" for cat, amt in summary['categories'].items()])}

Provide specific budget recommendations for each major category, with reasoning.
"""
        try:
            return self._generate(prompt)
        except Exception:
            return "Unable to generate budget suggestions right now. Please try again shortly."

# Global instance
try:
    insights = FinancialInsights()
except ValueError as e:
    log_event("warning", "insights_unavailable", reason=str(e))
    insights = None

def get_monthly_insight(year: int, month: int) -> str:
    """Get monthly insight."""
    if insights:
        return insights.generate_monthly_summary(year, month)
    return "Insights are not available because AI is not configured."

def get_cash_flow_forecast(months: int = 3) -> str:
    """Get cash flow forecast."""
    if insights:
        return insights.forecast_cash_flow(months)
    return "Forecast is not available because AI is not configured."

def get_budget_suggestion() -> str:
    """Get budget suggestion."""
    if insights:
        return insights.suggest_budget()
    return "Budget suggestion is not available because AI is not configured."
