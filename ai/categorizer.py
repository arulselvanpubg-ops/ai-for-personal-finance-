from typing import Dict, List, Tuple

from huggingface_hub import InferenceClient
from utils.helpers import get_env
from utils.monitoring import log_event

HF_API_KEY = get_env("HF_API_KEY")
HF_CATEGORIZER_MODEL = get_env("HF_CATEGORIZER_MODEL", "facebook/bart-large-mnli")
# hybrid (default): dedupe descriptions, keyword match first, HF only for unique "Other" lines.
# keyword_only: import uses keywords only (no HF quota).
# api_per_row: one HF call per row (slow; max model use, not deduped).
IMPORT_CATEGORIZE_MODE = get_env("IMPORT_CATEGORIZE_MODE", "hybrid").strip().lower()

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
        """Categorize a single transaction (API first when configured)."""
        if self.use_api:
            return self._categorize_api(description)
        return self._categorize_keyword(description)

    def categorize_for_import(self, description: str) -> str:
        """Keyword first, then HF if still Other — one call per unique ambiguous line in bulk."""
        kw = self._categorize_keyword(description)
        if kw != "Other":
            return kw
        if self.use_api and IMPORT_CATEGORIZE_MODE != "keyword_only":
            return self._categorize_api(description)
        return "Other"

    def bulk_categorize_for_import(self, descriptions: List[str]) -> Tuple[List[str], int]:
        """
        Assign categories for many rows with minimal API usage.

        Deduplicates by normalized description, runs keyword then (optionally) HF
        once per unique string. Returns (categories aligned to descriptions, hf_calls).
        """
        if not descriptions:
            return [], 0

        def norm(d: str) -> str:
            return (d or "").lower().strip()[:240] or "__empty__"

        unique_order: List[str] = []
        seen: Dict[str, None] = {}
        for d in descriptions:
            key = norm(d)
            if key not in seen:
                seen[key] = None
                unique_order.append(d if d is not None else "")

        if IMPORT_CATEGORIZE_MODE == "api_per_row" and self.use_api:
            out = [self._categorize_api(d or "") for d in descriptions]
            log_event(
                "info",
                "bulk_categorize_import",
                rows=len(descriptions),
                unique=len(descriptions),
                hf_calls=len(descriptions),
                mode="api_per_row",
            )
            return out, len(descriptions)

        unique_to_cat: Dict[str, str] = {}
        hf_calls = 0
        for text in unique_order:
            key = norm(text)
            kw = self._categorize_keyword(text)
            if kw != "Other":
                unique_to_cat[key] = kw
                continue
            if self.use_api and IMPORT_CATEGORIZE_MODE != "keyword_only":
                unique_to_cat[key] = self._categorize_api(text)
                hf_calls += 1
            else:
                unique_to_cat[key] = "Other"

        out = [unique_to_cat[norm(d)] for d in descriptions]
        log_event(
            "info",
            "bulk_categorize_import",
            rows=len(descriptions),
            unique=len(unique_order),
            hf_calls=hf_calls,
            mode=IMPORT_CATEGORIZE_MODE,
        )
        return out, hf_calls
    
    def _categorize_api(self, description: str) -> str:
        """Use HuggingFace Inference API."""
        try:
            result = self.client.zero_shot_classification(
                text=description,
                candidate_labels=CATEGORIES,
                model=HF_CATEGORIZER_MODEL
            )
            # HF API returns a list of classification elements in newer versions
            if isinstance(result, list) and len(result) > 0:
                first = result[0]
                return first.get('label') if isinstance(first, dict) else getattr(first, 'label', 'Other')
            # Fallback for older versions returning a dict with a 'labels' key
            elif isinstance(result, dict) and 'labels' in result:
                return result['labels'][0]
            
            return "Other"
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
    description_lower = (description or "").lower()
    for category, keywords in KEYWORD_MAPPING.items():
        for keyword in keywords:
            if keyword in description_lower:
                return category
    return "Other"


def categorize_transactions_for_import(descriptions: List[str]) -> List[str]:
    """Bulk categorization for bank imports (minimal HF calls when configured)."""
    if categorizer:
        cats, _ = categorizer.bulk_categorize_for_import(descriptions)
        return cats
    return [categorize_transaction(d) for d in descriptions]