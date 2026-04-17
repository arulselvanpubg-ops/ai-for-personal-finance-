import os
from huggingface_hub import InferenceClient

HF_API_KEY = os.getenv('HF_API_KEY')
HF_CATEGORIZER_MODEL = os.getenv('HF_CATEGORIZER_MODEL', 'facebook/bart-large-mnli')

# Predefined categories
CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Shopping",
    "Entertainment",
    "Bills & Utilities",
    "Healthcare",
    "Education",
    "Travel",
    "Income",
    "Transfer",
    "Other"
]

# Simple keyword-based fallback categorization
KEYWORD_MAPPING = {
    "Food & Dining": ["restaurant", "cafe", "food", "grocery", "supermarket", "pizza", "burger", "lunch", "dinner", "breakfast"],
    "Transportation": ["gas", "fuel", "car", "uber", "taxi", "transit", "bus", "train", "parking"],
    "Shopping": ["store", "shop", "amazon", "mall", "retail", "purchase"],
    "Entertainment": ["movie", "cinema", "theater", "spotify", "netflix", "game", "concert"],
    "Bills & Utilities": ["electric", "water", "gas bill", "internet", "phone", "utility"],
    "Healthcare": ["doctor", "hospital", "pharmacy", "medical", "health", "clinic"],
    "Education": ["school", "university", "tuition", "course", "book", "education"],
    "Travel": ["hotel", "flight", "airline", "travel", "booking"],
    "Income": ["salary", "paycheck", "payment", "income", "deposit"],
}

class TransactionCategorizer:
    def __init__(self):
        self.use_api = False
        if HF_API_KEY:
            try:
                self.client = InferenceClient(api_key=HF_API_KEY)
                self.use_api = True
            except Exception as e:
                print(f"HuggingFace API not available: {e}, falling back to keyword matching")
                self.use_api = False
    
    def categorize(self, description: str) -> str:
        """Categorize a transaction description."""
        if self.use_api:
            return self._categorize_api(description)
        else:
            return self._categorize_keyword(description)
    
    def _categorize_api(self, description: str) -> str:
        """Use HuggingFace Inference API."""
        try:
            result = self.client.zero_shot_classification(
                text=description,
                candidate_labels=CATEGORIES,
                model=HF_CATEGORIZER_MODEL
            )
            return result['labels'][0]  # Highest confidence
        except Exception as e:
            print(f"API categorization failed: {e}, using keyword fallback")
            return self._categorize_keyword(description)
    
    def _categorize_keyword(self, description: str) -> str:
        """Use keyword-based categorization as fallback."""
        description_lower = description.lower()
        
        for category, keywords in KEYWORD_MAPPING.items():
            for keyword in keywords:
                if keyword in description_lower:
                    return category
        
        return "Other"

# Global instance
try:
    categorizer = TransactionCategorizer()
except Exception as e:
    print(f"Failed to initialize categorizer: {e}")
    categorizer = None

def categorize_transaction(description: str) -> str:
    """Convenience function to categorize a transaction."""
    if categorizer:
        return categorizer.categorize(description)
    else:
        # Fallback keyword categorization if categorizer failed to initialize
        description_lower = description.lower()
        for category, keywords in KEYWORD_MAPPING.items():
            for keyword in keywords:
                if keyword in description_lower:
                    return category
        return "Other"