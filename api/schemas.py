from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    user_id: str = Field(..., examples=["u_00001"])
    amount: float = Field(..., examples=[-42.5])
    currency: str = Field(default="EUR", examples=["EUR"])
    label: str = Field(..., examples=["UBER TRIP PARIS"])
    booking_date: date | None = None
    merchant: str | None = None


class PredictResponse(BaseModel):
    category: str
    confidence: float
    source: str
    meta: dict[str, Any] = Field(default_factory=dict)
