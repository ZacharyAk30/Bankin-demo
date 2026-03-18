from __future__ import annotations


def classification_prompt(label: str, merchant: str | None, amount: float, currency: str) -> str:
    """
    Prompt “prod-like”: contrainte JSON, catégories fermées, explication courte.
    En vrai, on versionnerait les prompts (ex: prompt registry).
    """
    cats = [
        "groceries",
        "restaurants",
        "transport",
        "rent",
        "utilities",
        "salary",
        "shopping",
        "subscriptions",
        "health",
        "travel",
        "cash_withdrawal",
        "fees",
        "insurance",
        "unknown",
    ]
    merchant_txt = merchant or "unknown"
    return f"""
You are a fintech transaction categorization engine.

Task: classify the transaction into exactly one category from this list:
{', '.join(cats)}

Input:
- label: {label}
- merchant: {merchant_txt}
- amount: {amount}
- currency: {currency}

Return ONLY valid JSON with keys:
- category (string)
- confidence (number between 0 and 1)

Rules:
- If you are unsure, return category="unknown" with low confidence.
""".strip()

