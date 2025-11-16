from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


@dataclass
class SalesMetrics:
    total_revenue: float
    total_orders: int
    average_order_value: float
    period: str


@dataclass
class UserMetrics:
    total_users: int
    active_users: int
    new_users: int
    retention_rate: float


def calculate_growth_rate(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100.0


class AnalyticsService:
    def __init__(self) -> None:
        self.sales_data: List[Dict[str, Any]] = []
        self.user_data: List[Dict[str, Any]] = []
        self.events: List[Any] = []

    # Sales tracking
    def track_sale(self, amount: float, order_id: Optional[str], user_id: Optional[str]) -> bool:
        try:
            if amount is None or float(amount) <= 0:
                return False
        except (TypeError, ValueError):
            return False
        if not order_id or not user_id:
            return False

        sale = {
            "amount": float(amount),
            "order_id": order_id,
            "user_id": user_id,
            "timestamp": datetime.now(),
        }
        self.sales_data.append(sale)
        return True

    def get_sales_metrics(self, period: str = "daily") -> SalesMetrics:
        total_revenue = sum(s["amount"] for s in self.sales_data)
        total_orders = len(self.sales_data)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
        return SalesMetrics(
            total_revenue=total_revenue,
            total_orders=total_orders,
            average_order_value=average_order_value,
            period=period,
        )

    # User registration and metrics
    def register_user(self, user_id: Optional[str], is_active: bool = True) -> bool:
        if not user_id:
            return False
        self.user_data.append(
            {
                "user_id": user_id,
                "is_active": bool(is_active),
                "registered_at": datetime.now(),
            }
        )
        return True

    def get_user_metrics(self) -> UserMetrics:
        total_users = len(self.user_data)
        active_users = sum(1 for u in self.user_data if u.get("is_active"))
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        new_users = sum(1 for u in self.user_data if u.get("registered_at") and u["registered_at"] >= seven_days_ago)
        retention_rate = (active_users / total_users * 100.0) if total_users > 0 else 0.0
        return UserMetrics(
            total_users=total_users,
            active_users=active_users,
            new_users=new_users,
            retention_rate=retention_rate,
        )

    # Events
    def track_event(self, event: Any) -> bool:
        if not getattr(event, "user_id", None) or not getattr(event, "event_type", None):
            return False
        if not hasattr(event, "timestamp") or not isinstance(event.timestamp, datetime):
            return False
        self.events.append(event)
        return True

    def get_top_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        counts: Dict[str, int] = {}
        for e in self.events:
            etype = getattr(e, "event_type", None)
            if etype:
                counts[etype] = counts.get(etype, 0) + 1
        sorted_events = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        result = [{"event_type": etype, "count": count} for etype, count in sorted_events[: max(0, limit)]]
        return result

    def calculate_revenue_growth(self, days: int = 30) -> float:
        now = datetime.now()
        start_current = now - timedelta(days=days)
        end_current = now
        start_previous = now - timedelta(days=2 * days)
        end_previous = start_current

        def in_range(ts: datetime, start: datetime, end: datetime) -> bool:
            return start < ts <= end

        current_revenue = sum(
            s["amount"] for s in self.sales_data if in_range(s["timestamp"], start_current, end_current)
        )
        previous_revenue = sum(
            s["amount"] for s in self.sales_data if in_range(s["timestamp"], start_previous, end_previous)
        )

        return calculate_growth_rate(current_revenue, previous_revenue)

    def get_user_activity_stats(self, user_id: Optional[str]) -> Dict[str, Any]:
        if not user_id:
            return {"error": "user_id is required"}
        user_events = [e for e in self.events if getattr(e, "user_id", None) == user_id]
        user_sales = [s for s in self.sales_data if s.get("user_id") == user_id]

        total_events = len(user_events)
        total_purchases = len(user_sales)
        total_spent = sum(s["amount"] for s in user_sales)
        average_purchase = total_spent / total_purchases if total_purchases > 0 else 0.0

        activity_level = self._calculate_activity_level(total_events, total_purchases)

        # If no activity at all
        if total_events == 0 and total_purchases == 0:
            activity_level = "inactive"

        return {
            "user_id": user_id,
            "total_events": total_events,
            "total_purchases": total_purchases,
            "total_spent": total_spent,
            "average_purchase": average_purchase,
            "activity_level": activity_level,
        }

    def _calculate_activity_level(self, events: int, purchases: int) -> str:
        score = int(events) + int(purchases) * 5
        if score >= 50:
            return "highly_active"
        if score >= 20:
            return "active"
        if score >= 5:
            return "moderate"
        if score >= 1:
            return "low"
        return "inactive"

    def get_inactive_users(self, days: int) -> List[str]:
        if days <= 0:
            return []
        cutoff = datetime.now() - timedelta(days=days)
        user_ids = {u["user_id"] for u in self.user_data}
        inactive: List[str] = []
        for uid in user_ids:
            user_events = [e.timestamp for e in self.events if getattr(e, "user_id", None) == uid]
            user_sales = [s["timestamp"] for s in self.sales_data if s.get("user_id") == uid]
            last_event = max(user_events) if user_events else None
            last_sale = max(user_sales) if user_sales else None

            last_activity = None
            if last_event and last_sale:
                last_activity = max(last_event, last_sale)
            elif last_event:
                last_activity = last_event
            elif last_sale:
                last_activity = last_sale

            # No events/sales or last activity before or equal to cutoff -> inactive
            if last_activity is None or last_activity <= cutoff:
                inactive.append(uid)

        return sorted(inactive)

    def calculate_engagement_rate(self, window_days: int = 7) -> float:
        total_users = len(self.user_data)
        if total_users == 0:
            return 0.0
        cutoff = datetime.now() - timedelta(days=window_days)
        engaged_users = {e.user_id for e in self.events if getattr(e, "timestamp", None) and e.timestamp >= cutoff}
        rate = (len(engaged_users) / total_users) * 100.0
        return round(rate, 2)