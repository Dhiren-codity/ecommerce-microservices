from src.services.analytics import AnalyticsService
from src.models.metrics import Event
from datetime import datetime


def main():
    service = AnalyticsService()

    print("=== E-Commerce Analytics Service ===\n")

    service.track_sale(99.99, "order-001", "user-123")
    service.track_sale(149.50, "order-002", "user-456")
    service.track_sale(75.00, "order-003", "user-789")

    metrics = service.get_sales_metrics("daily")
    print(f"Sales Metrics:")
    print(f"  Total Revenue: ${metrics.total_revenue:.2f}")
    print(f"  Total Orders: {metrics.total_orders}")
    print(f"  Average Order Value: ${metrics.average_order_value:.2f}\n")

    service.register_user("user-123", is_active=True)
    service.register_user("user-456", is_active=True)
    service.register_user("user-789", is_active=False)

    user_metrics = service.get_user_metrics()
    print(f"User Metrics:")
    print(f"  Total Users: {user_metrics.total_users}")
    print(f"  Active Users: {user_metrics.active_users}")
    print(f"  Retention Rate: {user_metrics.retention_rate:.1f}%\n")

    service.track_event(Event(user_id="user-123", event_type="page_view", timestamp=datetime.now()))
    service.track_event(Event(user_id="user-456", event_type="add_to_cart", timestamp=datetime.now()))
    service.track_event(Event(user_id="user-123", event_type="page_view", timestamp=datetime.now()))

    top_events = service.get_top_events(5)
    print(f"Top Events:")
    for event in top_events:
        print(f"  {event['event_type']}: {event['count']} times")


if __name__ == "__main__":
    main()
