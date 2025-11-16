from typing import List, Dict
from datetime import datetime, timedelta
from src.models.metrics import SalesMetric, UserMetric, Event, calculate_average, calculate_growth_rate


class AnalyticsService:
    def __init__(self):
        self.sales_data: List[Dict] = []
        self.user_data: List[Dict] = []
        self.events: List[Event] = []

    def track_sale(self, amount: float, order_id: str, user_id: str) -> bool:
        if amount <= 0:
            return False

        sale = {
            "amount": amount,
            "order_id": order_id,
            "user_id": user_id,
            "timestamp": datetime.now()
        }
        self.sales_data.append(sale)
        return True

    def get_sales_metrics(self, period: str = "daily") -> SalesMetric:
        if not self.sales_data:
            return SalesMetric(
                total_revenue=0.0,
                total_orders=0,
                average_order_value=0.0,
                period=period
            )

        total_revenue = sum(sale["amount"] for sale in self.sales_data)
        total_orders = len(self.sales_data)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0

        return SalesMetric(
            total_revenue=total_revenue,
            total_orders=total_orders,
            average_order_value=average_order_value,
            period=period
        )

    def register_user(self, user_id: str, is_active: bool = True) -> bool:
        if not user_id:
            return False

        user = {
            "user_id": user_id,
            "is_active": is_active,
            "registered_at": datetime.now()
        }
        self.user_data.append(user)
        return True

    def get_user_metrics(self) -> UserMetric:
        total_users = len(self.user_data)
        active_users = sum(1 for user in self.user_data if user.get("is_active", False))

        now = datetime.now()
        week_ago = now - timedelta(days=7)
        new_users = sum(1 for user in self.user_data if user["registered_at"] >= week_ago)

        retention_rate = (active_users / total_users * 100) if total_users > 0 else 0.0

        return UserMetric(
            total_users=total_users,
            active_users=active_users,
            new_users=new_users,
            retention_rate=retention_rate
        )

    def track_event(self, event: Event) -> bool:
        if not event.user_id or not event.event_type:
            return False

        self.events.append(event)
        return True

    def get_top_events(self, limit: int = 10) -> List[Dict]:
        event_counts = {}
        for event in self.events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        sorted_events = sorted(event_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"event_type": evt, "count": count} for evt, count in sorted_events[:limit]]

    def calculate_revenue_growth(self, days: int = 30) -> float:
        now = datetime.now()
        current_period_start = now - timedelta(days=days)
        previous_period_start = current_period_start - timedelta(days=days)

        current_revenue = sum(
            sale["amount"] for sale in self.sales_data
            if sale["timestamp"] >= current_period_start
        )

        previous_revenue = sum(
            sale["amount"] for sale in self.sales_data
            if previous_period_start <= sale["timestamp"] < current_period_start
        )

        return calculate_growth_rate(current_revenue, previous_revenue)
