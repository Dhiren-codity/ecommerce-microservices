from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class SalesMetric(BaseModel):
    total_revenue: float = Field(ge=0)
    total_orders: int = Field(ge=0)
    average_order_value: float = Field(ge=0)
    period: str


class UserMetric(BaseModel):
    total_users: int = Field(ge=0)
    active_users: int = Field(ge=0)
    new_users: int = Field(ge=0)
    retention_rate: float = Field(ge=0, le=100)


class Event(BaseModel):
    user_id: str
    event_type: str
    timestamp: datetime
    metadata: Optional[Dict] = None


def calculate_average(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_growth_rate(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def filter_by_date_range(events: List[Event], start_date: datetime, end_date: datetime) -> List[Event]:
    return [e for e in events if start_date <= e.timestamp <= end_date]
