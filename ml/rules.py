from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RulePrediction:
    category: str
    confidence: float
    rule_id: str


class RuleBasedCategorizer:
    """
    Couche 1: règles rapides et déterministes (latence ~0).
    On garde volontairement un petit set de règles à fort signal,
    et on laisse le ML/LLM gérer le long tail.
    """

    def __init__(self) -> None:
        self._rules: list[tuple[str, re.Pattern[str], str, float]] = [
            ("r_netflix", re.compile(r"\bNETFLIX\b"), "subscriptions", 0.98),
            ("r_spotify", re.compile(r"\bSPOTIFY\b"), "subscriptions", 0.98),
            ("r_uber", re.compile(r"\bUBER\b"), "transport", 0.95),
            ("r_sncf", re.compile(r"\bSNCF\b"), "transport", 0.95),
            ("r_ratp", re.compile(r"\bRATP\b|\bNAVIGO\b"), "transport", 0.92),
            ("r_edf", re.compile(r"\bEDF\b"), "utilities", 0.95),
            ("r_orange", re.compile(r"\bORANGE\b"), "utilities", 0.95),
            ("r_rent", re.compile(r"\bLOYER\b"), "rent", 0.97),
            ("r_salary", re.compile(r"\bSALAIRE\b"), "salary", 0.99),
            ("r_atm", re.compile(r"\bRETRAIT\b|\bATM\b|\bDAB\b"), "cash_withdrawal", 0.94),
            ("r_fees", re.compile(r"\bFRAIS\b|\bCOMMISSION\b"), "fees", 0.93),
            ("r_pharma", re.compile(r"\bPHARMACIE\b"), "health", 0.90),
            ("r_doctolib", re.compile(r"\bDOCTOLIB\b"), "health", 0.92),
            ("r_airfrance", re.compile(r"\bAIR\s*FRANCE\b|\bAIRFRANCE\b"), "travel", 0.92),
        ]

    def predict(self, label_norm: str, merchant: str | None = None) -> RulePrediction | None:
        text = f"{label_norm} {merchant or ''}".upper()
        for rule_id, pattern, cat, conf in self._rules:
            if pattern.search(text):
                return RulePrediction(category=cat, confidence=conf, rule_id=rule_id)
        return None

