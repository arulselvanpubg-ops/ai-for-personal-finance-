import os
import google.generativeai as genai
from core.finance import get_monthly_summary
from datetime import datetime

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

class FinancialInsights:
    def __init__(self):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set")
        
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def generate_monthly_summary(self, year: int, month: int) -> str:
        """Generate a natural language summary of monthly finances."""
        summary = get_monthly_summary(year, month)
        
        prompt = f"""
Based on the following financial data for {datetime(year, month, 1).strftime('%B %Y')}, 
generate a concise, encouraging monthly financial summary:

Income: ${summary['income']:.2f}
Expenses: ${summary['expenses']:.2f}
Net: ${summary['net']:.2f}
Top categories: {', '.join([f"{cat}: ${amt:.2f}" for cat, amt in list(summary['categories'].items())[:5]])}

Write 2-3 paragraphs that:
- Highlights positive trends
- Identifies areas for improvement
- Provides gentle encouragement
- Uses friendly, supportive tone
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Unable to generate summary: {str(e)}"
    
    def forecast_cash_flow(self, months_ahead: int = 3) -> str:
        """Generate cash flow forecast."""
        # Get last 3 months data for trend analysis
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

Month 1: Income ${summaries[0]['income']:.2f}, Expenses ${summaries[0]['expenses']:.2f}, Net ${summaries[0]['net']:.2f}
Month 2: Income ${summaries[1]['income']:.2f}, Expenses ${summaries[1]['expenses']:.2f}, Net ${summaries[1]['net']:.2f}
Month 3: Income ${summaries[2]['income']:.2f}, Expenses ${summaries[2]['expenses']:.2f}, Net ${summaries[2]['net']:.2f}

Provide a forecast that includes:
- Expected income and expense trends
- Potential savings opportunities
- Risk factors to watch
- Actionable recommendations
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Unable to generate forecast: {str(e)}"
    
    def suggest_budget(self) -> str:
        """Suggest budget based on past spending."""
        summary = get_monthly_summary(datetime.now().year, datetime.now().month)
        
        prompt = f"""
Based on current spending of ${summary['expenses']:.2f} per month with income of ${summary['income']:.2f},
suggest a realistic monthly budget allocation.

Current category breakdown: {', '.join([f"{cat}: ${amt:.2f}" for cat, amt in summary['categories'].items()])}

Provide specific budget recommendations for each major category, with reasoning.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Unable to generate budget suggestion: {str(e)}"

# Global instance
try:
    insights = FinancialInsights()
except ValueError as e:
    print(f"Warning: {e}")
    insights = None

def get_monthly_insight(year: int, month: int) -> str:
    if insights:
        return insights.generate_monthly_summary(year, month)
    return "Insights service is not available."

def get_cash_flow_forecast(months: int = 3) -> str:
    if insights:
        return insights.forecast_cash_flow(months)
    return "Forecast service is not available."

def get_budget_suggestion() -> str:
    if insights:
        return insights.suggest_budget()
    return "Budget suggestion service is not available."