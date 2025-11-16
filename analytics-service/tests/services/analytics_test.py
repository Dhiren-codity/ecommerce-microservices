import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.services.analytics import AnalyticsService


@pytest.fixture
def analytics_service():
    """Create a fresh AnalyticsService instance for each test"""
    return AnalyticsService()


def test_AnalyticsService_init_initial_state(analytics_service):
    """Verify initialization sets empty data structures"""
    assert isinstance(analytics_service.sales_data, list)
    assert isinstance(analytics_service.user_data, list)
    assert isinstance(analytics_service.events, list)
    assert len(analytics_service.sales_data) == 0
    assert len(analytics_service.user_data) == 0
    assert len(analytics_service.events) == 0


def test_AnalyticsService_track_sale_valid(analytics_service):
    """track_sale should accept positive amounts and store sale with correct fields"""
    result = analytics_service.track_sale(amount=100.0, order_id="ord_1", user_id="user_1")
    assert result is True
    assert len(analytics_service.sales_data) == 1
    sale = analytics_service.sales_data[0]
    assert sale["amount"] == 100.0
    assert sale["order_id"] == "ord_1"
    assert sale["user_id"] == "user_1"
    assert isinstance(sale["timestamp"], datetime)


def test_AnalyticsService_track_sale_invalid_amount(analytics_service):
    """track_sale should reject non-positive amounts"""
    assert analytics_service.track_sale(amount=0.0, order_id="ord_0", user_id="u") is False
    assert analytics_service.track_sale(amount=-10.0, order_id="ord_neg", user_id="u") is False
    assert len(analytics_service.sales_data) == 0


def test_AnalyticsService_get_sales_metrics_empty(analytics_service):
    """get_sales_metrics should return zeroed metrics when no sales exist"""
    metrics = analytics_service.get_sales_metrics()
    assert hasattr(metrics, "total_revenue")
    assert hasattr(metrics, "total_orders")
    assert hasattr(metrics, "average_order_value")
    assert hasattr(metrics, "period")
    assert metrics.total_revenue == 0.0
    assert metrics.total_orders == 0
    assert metrics.average_order_value == 0.0
    assert metrics.period == "daily"


def test_AnalyticsService_get_sales_metrics_nonempty(analytics_service):
    """get_sales_metrics should compute totals and averages correctly"""
    analytics_service.track_sale(50.0, "ord_1", "user_a")
    analytics_service.track_sale(150.0, "ord_2", "user_b")
    metrics = analytics_service.get_sales_metrics(period="monthly")
    assert metrics.total_revenue == 200.0
    assert metrics.total_orders == 2
    assert metrics.average_order_value == 100.0
    assert metrics.period == "monthly"


def test_AnalyticsService_register_user_valid(analytics_service):
    """register_user should create user with default active=True and timestamp"""
    result = analytics_service.register_user("user_1")
    assert result is True
    assert len(analytics_service.user_data) == 1
    user = analytics_service.user_data[0]
    assert user["user_id"] == "user_1"
    assert user["is_active"] is True
    assert isinstance(user["registered_at"], datetime)


def test_AnalyticsService_register_user_invalid(analytics_service):
    """register_user should reject empty user_id"""
    assert analytics_service.register_user("") is False
    assert analytics_service.register_user(None) is False
    assert len(analytics_service.user_data) == 0


def test_AnalyticsService_get_user_metrics_calculations(analytics_service):
    """get_user_metrics should compute totals, active users, new users, and retention rate"""
    now = datetime.now()
    # Register 3 users: two active, one inactive
    analytics_service.register_user("u1", is_active=True)
    analytics_service.register_user("u2", is_active=True)
    analytics_service.register_user("u3", is_active=False)

    # Adjust registration times: u1 recent, u2 older, u3 recent
    analytics_service.user_data[0]["registered_at"] = now - timedelta(days=2)   # u1 - new
    analytics_service.user_data[1]["registered_at"] = now - timedelta(days=10)  # u2 - old
    analytics_service.user_data[2]["registered_at"] = now - timedelta(days=1)   # u3 - new

    metrics = analytics_service.get_user_metrics()
    assert metrics.total_users == 3
    assert metrics.active_users == 2
    # New users within 7 days: u1 and u3
    assert metrics.new_users == 2
    # Retention rate = active_users / total_users * 100
    assert metrics.retention_rate == pytest.approx((2 / 3) * 100)


def test_AnalyticsService_track_event_valid(analytics_service):
    """track_event should accept valid event object and append to events"""
    event = Mock()
    event.user_id = "u1"
    event.event_type = "click"
    event.timestamp = datetime.now()
    result = analytics_service.track_event(event)
    assert result is True
    assert len(analytics_service.events) == 1
    assert analytics_service.events[0] is event


def test_AnalyticsService_track_event_invalid(analytics_service):
    """track_event should reject event without user_id or event_type"""
    event1 = Mock()
    event1.user_id = ""
    event1.event_type = "click"
    event1.timestamp = datetime.now()

    event2 = Mock()
    event2.user_id = "u1"
    event2.event_type = None
    event2.timestamp = datetime.now()

    assert analytics_service.track_event(event1) is False
    assert analytics_service.track_event(event2) is False
    assert len(analytics_service.events) == 0


def test_AnalyticsService_get_top_events_basic_sort_and_limit(analytics_service):
    """get_top_events should aggregate counts, sort descending, and respect limit"""
    now = datetime.now()
    # Create events: click x3, view x2, purchase x1
    for _ in range(3):
        e = Mock(user_id="u1", event_type="click", timestamp=now)
        assert analytics_service.track_event(e)
    for _ in range(2):
        e = Mock(user_id="u2", event_type="view", timestamp=now)
        assert analytics_service.track_event(e)
    e = Mock(user_id="u3", event_type="purchase", timestamp=now)
    assert analytics_service.track_event(e)

    top2 = analytics_service.get_top_events(limit=2)
    assert top2 == [
        {"event_type": "click", "count": 3},
        {"event_type": "view", "count": 2},
    ]


def test_AnalyticsService_calculate_revenue_growth_invokes_helper_and_sums(analytics_service):
    """calculate_revenue_growth should compute current/previous revenue and call calculate_growth_rate"""
    now = datetime.now()
    days = 30

    # Add sales and then adjust timestamps to control periods
    # One in previous period
    analytics_service.track_sale(100.0, "ord_prev", "u1")
    analytics_service.sales_data[-1]["timestamp"] = now - timedelta(days=days + 1)

    # One before previous period (should not count)
    analytics_service.track_sale(200.0, "ord_before_prev", "u2")
    analytics_service.sales_data[-1]["timestamp"] = now - timedelta(days=(2 * days) + 1)

    # Two in current period
    analytics_service.track_sale(50.0, "ord_cur1", "u1")
    analytics_service.sales_data[-1]["timestamp"] = now - timedelta(days=days - 1)
    analytics_service.track_sale(25.0, "ord_cur2", "u3")
    analytics_service.sales_data[-1]["timestamp"] = now - timedelta(days=1)

    # Expected sums: current=75.0, previous=100.0
    with patch("src.services.analytics.calculate_growth_rate", return_value=123.45) as mock_growth:
        growth = analytics_service.calculate_revenue_growth(days=days)
        assert growth == 123.45
        mock_growth.assert_called_once_with(75.0, 100.0)


def test_AnalyticsService_calculate_revenue_growth_exception_propagates(analytics_service):
    """calculate_revenue_growth should propagate exceptions from calculate_growth_rate"""
    analytics_service.track_sale(10.0, "o1", "u")
    with patch("src.services.analytics.calculate_growth_rate", side_effect=ValueError("boom")):
        with pytest.raises(ValueError):
            analytics_service.calculate_revenue_growth(days=7)


def test_AnalyticsService_get_user_activity_stats_missing_user_id(analytics_service):
    """get_user_activity_stats should return error when user_id is missing"""
    result = analytics_service.get_user_activity_stats("")
    assert result == {"error": "user_id is required"}


def test_AnalyticsService_get_user_activity_stats_no_activity(analytics_service):
    """get_user_activity_stats should return inactive state when no events or sales for user"""
    result = analytics_service.get_user_activity_stats("u1")
    assert result["user_id"] == "u1"
    assert result["total_events"] == 0
    assert result["total_purchases"] == 0
    assert result["total_spent"] == 0.0
    assert result["activity_level"] == "inactive"
    assert result["average_purchase"] == 0.0


def test_AnalyticsService_get_user_activity_stats_with_activity(analytics_service):
    """get_user_activity_stats should aggregate user events and sales and compute averages"""
    now = datetime.now()

    # Add events for user u1
    for _ in range(7):
        e = Mock(user_id="u1", event_type="click", timestamp=now)
        analytics_service.track_event(e)

    # Add sales for user u1
    analytics_service.track_sale(30.0, "ord1", "u1")
    analytics_service.track_sale(50.0, "ord2", "u1")

    stats = analytics_service.get_user_activity_stats("u1")
    assert stats["user_id"] == "u1"
    assert stats["total_events"] == 7
    assert stats["total_purchases"] == 2
    assert stats["total_spent"] == 80.0
    assert stats["average_purchase"] == 40.0
    # Activity level score = events + purchases*5 = 7 + 10 = 17 -> "moderate"
    assert stats["activity_level"] == "moderate"


def test_AnalyticsService__calculate_activity_level_thresholds(analytics_service):
    """_calculate_activity_level should map scores to correct labels at boundaries"""
    # Score 50 -> highly_active
    assert analytics_service._calculate_activity_level(events=0, purchases=10) == "highly_active"
    # Score 20 -> active
    assert analytics_service._calculate_activity_level(events=0, purchases=4) == "active"
    # Score 5 -> moderate
    assert analytics_service._calculate_activity_level(events=5, purchases=0) == "moderate"
    # Score 4 -> low
    assert analytics_service._calculate_activity_level(events=4, purchases=0) == "low"


def test_AnalyticsService_get_inactive_users_days_le_0(analytics_service):
    """get_inactive_users should return empty list for non-positive days"""
    assert analytics_service.get_inactive_users(0) == []
    assert analytics_service.get_inactive_users(-5) == []


def test_AnalyticsService_get_inactive_users_basic(analytics_service):
    """get_inactive_users should return sorted user_ids with no recent activity within cutoff"""
    now = datetime.now()
    cutoff_days = 10

    # Register users
    analytics_service.register_user("u1")
    analytics_service.register_user("u2")
    analytics_service.register_user("u3")
    analytics_service.register_user("u4")

    # Recent activity for u1 via event
    e1 = Mock(user_id="u1", event_type="login", timestamp=now - timedelta(days=1))
    analytics_service.track_event(e1)

    # Recent activity for u2 via sale
    analytics_service.track_sale(20.0, "s1", "u2")
    analytics_service.sales_data[-1]["timestamp"] = now - timedelta(days=2)

    # Old activity for u4 (outside cutoff)
    e4 = Mock(user_id="u4", event_type="view", timestamp=now - timedelta(days=30))
    analytics_service.track_event(e4)
    analytics_service.track_sale(10.0, "s_old", "u4")
    analytics_service.sales_data[-1]["timestamp"] = now - timedelta(days=30)

    inactive = analytics_service.get_inactive_users(days=cutoff_days)
    # u3 has no activity; u4 only had old activity -> both inactive
    assert inactive == ["u3", "u4"]


def test_AnalyticsService_calculate_engagement_rate_no_users(analytics_service):
    """calculate_engagement_rate should return 0.0 when there are no users"""
    assert analytics_service.calculate_engagement_rate() == 0.0


def test_AnalyticsService_calculate_engagement_rate_with_users_and_events(analytics_service):
    """calculate_engagement_rate should compute percentage of users with events in last 7 days"""
    now = datetime.now()
    # Register users
    analytics_service.register_user("u1")
    analytics_service.register_user("u2")
    analytics_service.register_user("u3")

    # Events: u1 and u2 in last 7 days; u3 older than 7 days
    e1 = Mock(user_id="u1", event_type="click", timestamp=now - timedelta(days=1))
    e2 = Mock(user_id="u2", event_type="click", timestamp=now - timedelta(days=3))
    e3 = Mock(user_id="u3", event_type="click", timestamp=now - timedelta(days=10))
    analytics_service.track_event(e1)
    analytics_service.track_event(e2)
    analytics_service.track_event(e3)

    rate = analytics_service.calculate_engagement_rate()
    assert rate == 66.67