from .categorizer import categorize_transaction
from .chat import send_chat_message
from .insights import get_monthly_insight, get_cash_flow_forecast, get_budget_suggestion
from .invest_advisor import get_ai_investment_advice

class AIRouter:
    def __init__(self):
        self.tasks = {
            'categorize': self._route_categorize,
            'chat': self._route_chat,
            'insights': self._route_insights,
            'forecast': self._route_forecast,
            'budget_suggest': self._route_budget,
            'invest_advice': self._route_invest_advice
        }
    
    def route(self, task: str, **kwargs):
        """Route AI task to appropriate service."""
        if task in self.tasks:
            return self.tasks[task](**kwargs)
        else:
            raise ValueError(f"Unknown AI task: {task}")
    
    def _route_categorize(self, description: str, **kwargs):
        """Route to HuggingFace categorizer."""
        return categorize_transaction(description)
    
    def _route_chat(self, user_message: str, history=None, **kwargs):
        """Route to NVIDIA NIM chat."""
        return send_chat_message(user_message, history)
    
    def _route_insights(self, year: int, month: int, **kwargs):
        """Route to Gemini insights."""
        return get_monthly_insight(year, month)
    
    def _route_forecast(self, months: int = 3, **kwargs):
        """Route to Gemini forecast."""
        return get_cash_flow_forecast(months)
    
    def _route_budget(self, **kwargs):
        """Route to Gemini budget suggestion."""
        return get_budget_suggestion()
        
    def _route_invest_advice(self, portfolio_data: list, stream: bool = False, **kwargs):
        """Route to Investment Advisor."""
        return get_ai_investment_advice(portfolio_data, stream=stream)

# Global router
router = AIRouter()

def route_ai_task(task: str, **kwargs):
    """Convenience function for AI routing."""
    return router.route(task, **kwargs)