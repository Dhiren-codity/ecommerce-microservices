import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.services.analytics import AnalyticsService


class DummyEvent:
    def __init__(self, user_id: str, event_type: str, timestamp: datetime):
        self.user_id = user_id
        self.event_type = event_type
        self.timestamp = timestamp


@pytest.fixture
def analytics_service():
    """Create a fresh AnalyticsService instance for each test"""
    return AnalyticsService()


def test_AnalyticsService___init___initial_state(analytics_service):
    """Ensure initialization creates empty data stores"""
    assert analytics_service.sales_data == []
    assert analytics_service.user_data == []
    assert analytics_service.events == []


def test_AnalyticsService_track_sale_valid(analytics_service):
    """track_sale should append sale with valid amount and return True"""
    fixed_now = datetime(2023, 1, 10, 12, 0, 0)
    with patch('src.services.analytics.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        result = analytics_service.track_sale(50.0, "order1", "user1")

    assert result is True
    assert len(analytics_service.sales_data) == 1
    sale = analytics_service.sales_data[0]
    assert sale["amount"] == 50.0
    assert sale["order_id"] == "order1"
    assert sale["user_id"] == "user1"
    assert sale["timestamp"] == fixed_now


@pytest.mark.parametrize("amount", [0, -1.0, -100.5])
def test_AnalyticsService_track_sale_invalid_amount(analytics_service, amount):
    """track_sale should not append sale for non-positive amounts and return False"""
    result = analytics_service.track_sale(amount, "orderX", "userX")
    assert result is False
    assert len(analytics_service.sales_data) == 0


def test_AnalyticsService_get_sales_metrics_empty(analytics_service):
    """get_sales_metrics should return zeroed SalesMetric when no sales"""
    metrics = analytics_service.get_sales_metrics(period="weekly")
    assert getattr(metrics, "total_revenue") == 0.0
    assert getattr(metrics, "total_orders") == 0
    assert getattr(metrics, "average_order_value") == 0.0
    assert getattr(metrics, "period") == "weekly"


def test_AnalyticsService_get_sales_metrics_non_empty(analytics_service):
    """get_sales_metrics should compute totals and averages correctly"""
    analytics_service.track_sale(100.0, "o1", "u1")
    analytics_service.track_sale(50.0, "o2", "u2")
    analytics_service.track_sale(150.0, "o3", "u1")

    metrics = analytics_service.get_sales_metrics()
    assert getattr(metrics, "total_revenue") == 300.0
    assert getattr(metrics, "total_orders") == 3
    assert getattr(metrics, "average_order_value") == 100.0
    assert getattr(metrics, "period") == "daily"


def test_AnalyticsService_register_user_valid_and_invalid(analytics_service):
    """register_user should append valid users and reject empty ids"""
    fixed_now = datetime(2023, 1, 10, 12, 0, 0)
    with patch('src.services.analytics.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        assert analytics_service.register_user("user1") is True

    assert len(analytics_service.user_data) == 1
    user = analytics_service.user_data[0]
    assert user["user_id"] == "user1"
    assert user["is_active"] is True
    assert user["registered_at"] == fixed_now

    # invalid
    assert analytics_service.register_user("") is False
    assert len(analytics_service.user_data) == 1


def test_AnalyticsService_get_user_metrics_no_users(analytics_service):
    """get_user_metrics should return zeros when no users are registered"""
    metrics = analytics_service.get_user_metrics()
    assert getattr(metrics, "total_users") == 0
    assert getattr(metrics, "active_users") == 0
    assert getattr(metrics, "new_users") == 0
    assert getattr(metrics, "retention_rate") == 0.0


def test_AnalyticsService_get_user_metrics_mixed_active_new(analytics_service):
    """get_user_metrics should count active and new users within 7 days and compute retention rate"""
    fixed_now = datetime(2023, 2, 1, 12, 0, 0)
    with patch('src.services.analytics.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        # Register 4 users initially
        analytics_service.register_user("u1", is_active=True)
        analytics_service.register_user("u2", is_active=True)
        analytics_service.register_user("u3", is_active=False)
        analytics_service.register_user("u4", is_active=True)

    # Adjust registered_at to create "new" and "old" users relative to fixed_now
    # u1: new (within 7 days)
    analytics_service.user_data[0]["registered_at"] = fixed_now - timedelta(days=3)
    # u2: old (8 days ago)
    analytics_service.user_data[1]["registered_at"] = fixed_now - timedelta(days=8)
    # u3: new (today) but inactive
    analytics_service.user_data[2]["registered_at"] = fixed_now
    # u4: old and active
    analytics_service.user_data[3]["registered_at"] = fixed_now - timedelta(days=30)

    # Compute expected
    total_users = 4
    active_users = 3
    new_users = 2  # u1 and u3
    expected_retention = (active_users / total_users) * 100

    with patch('src.services.analytics.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        metrics = analytics_service.get_user_metrics()

    assert getattr(metrics, "total_users") == total_users
    assert getattr(metrics, "active_users") == active_users
    assert getattr(metrics, "new_users") == new_users
    assert getattr(metrics, "retention_rate") == expected_retention


def test_AnalyticsService_track_event_valid_and_invalid(analytics_service):
    """track_event should validate event fields and append only valid events"""
    # Invalid: missing user_id
    invalid_event1 = DummyEvent(user_id="", event_type="click", timestamp=datetime.now())
    assert analytics_service.track_event(invalid_event1) is False
    assert len(analytics_service.events) == 0

    # Invalid: missing event_type
    invalid_event2 = DummyEvent(user_id="user1", event_type="", timestamp=datetime.now())
    assert analytics_service.track_event(invalid_event2) is False
    assert len(analytics_service.events) == 0

    # Valid
    valid_event = DummyEvent(user_id="user1", event_type="click", timestamp=datetime.now())
    assert analytics_service.track_event(valid_event) is True
    assert len(analytics_service.events) == 1
    assert analytics_service.events[0].event_type == "click"
    assert analytics_service.events[0].user_id == "user1"


def test_AnalyticsService_get_top_events_counts_and_limit(analytics_service):
    """get_top_events should return event counts sorted by frequency honoring the limit"""
    now = datetime(2023, 1, 10, 12, 0, 0)
    events = [
        DummyEvent("u1", "click", now),
        DummyEvent("u2", "click", now),
        DummyEvent("u3", "click", now),
        DummyEvent("u1", "view", now),
        DummyEvent("u2", "view", now),
        DummyEvent("u4", "purchase", now),
    ]
    for e in events:
        analytics_service.track_event(e)

    top2 = analytics_service.get_top_events(limit=2)
    assert top2 == [
        {"event_type": "click", "count": 3},
        {"event_type": "view", "count": 2},
    ]

    top10 = analytics_service.get_top_events(limit=10)
    assert top10 == [
        {"event_type": "click", "count": 3},
        {"event_type": "view", "count": 2},
        {"event_type": "purchase", "count": 1},
    ]


def test_AnalyticsService_calculate_revenue_growth_calls_dependency_and_correct_args(analytics_service):
    """calculate_revenue_growth should compute current and previous revenue and delegate to calculate_growth_rate"""
    fixed_now = datetime(2023, 2, 1, 12, 0, 0)
    days = 30
    current_start = fixed_now - timedelta(days=days)             # 2023-01-02
    previous_start = current_start - timedelta(days=days)        # 2022-12-03

    # Sales: current period: 100 + 50; previous period: 75; outside periods: 999 (ignored)
    s_current_1 = {"amount": 100.0, "order_id": "c1", "user_id": "u1", "timestamp": current_start + timedelta(days=1)}
    s_current_2 = {"amount": 50.0, "order_id": "c2", "user_id": "u2", "timestamp": fixed_now - timedelta(days=1)}
    s_previous = {"amount": 75.0, "order_id": "p1", "user_id": "u3", "timestamp": previous_start + timedelta(days=1)}
    s_outside = {"amount": 999.0, "order_id": "x1", "user_id": "u4", "timestamp": previous_start - timedelta(days=1)}

    analytics_service.sales_data.extend([s_current_1, s_current_2, s_previous, s_outside])

    with patch('src.services.analytics.datetime') as mock_datetime, \
         patch('src.services.analytics.calculate_growth_rate') as mock_growth:
        mock_datetime.now.return_value = fixed_now
        mock_growth.return_value = 42.0

        result = analytics_service.calculate_revenue_growth(days=days)

    # current revenue = 150, previous revenue = 75
    mock_growth.assert_called_once_with(150.0, 75.0)
    assert result == 42.0


def test_AnalyticsService_calculate_revenue_growth_raises_from_dependency(analytics_service):
    """calculate_revenue_growth should propagate exceptions from calculate_growth_rate"""
    fixed_now = datetime(2023, 2, 1, 12, 0, 0)
    analytics_service.sales_data.append(
        {"amount": 10.0, "order_id": "c1", "user_id": "u1", "timestamp": fixed_now}
    )

    with patch('src.services.analytics.datetime') as mock_datetime, \
         patch('src.services.analytics.calculate_growth_rate', side_effect=ZeroDivisionError("boom")):
        mock_datetime.now.return_value = fixed_now
        with pytest.raises(ZeroDivisionError):
            analytics_service.calculate_revenue_growth(days=30)


def test_AnalyticsService_get_user_activity_stats_missing_user_id(analytics_service):
    """get_user_activity_stats should return an error dict when user_id is missing"""
    result = analytics_service.get_user_activity_stats(user_id="")
    assert result == {"error": "user_id is required"}


def test_AnalyticsService_get_user_activity_stats_inactive_user(analytics_service):
    """get_user_activity_stats should return inactive stats for users with no activity"""
    result = analytics_service.get_user_activity_stats(user_id="uX")
    assert result["user_id"] == "uX"
    assert result["total_events"] == 0
    assert result["total_purchases"] == 0
    assert result["total_spent"] == 0.0
    assert result["activity_level"] == "inactive"


def test_AnalyticsService_get_user_activity_stats_with_activity(analytics_service):
    """get_user_activity_stats should compute totals, average purchase, and activity level"""
    fixed_now = datetime(2023, 1, 10, 12, 0, 0)
    # Add events and sales for u1 and some for others
    events = [DummyEvent("u1", "click", fixed_now) for _ in range(12)] + [
        DummyEvent("u2", "click", fixed_now)
    ]
    for e in events:
        analytics_service.track_event(e)

    analytics_service.sales_data.extend([
        {"amount": 100.0, "order_id": "o1", "user_id": "u1", "timestamp": fixed_now},
        {"amount": 50.0, "order_id": "o2", "user_id": "u1", "timestamp": fixed_now - timedelta(days=1)},
        {"amount": 999.0, "order_id": "o3", "user_id": "u2", "timestamp": fixed_now},
    ])

    stats = analytics_service.get_user_activity_stats("u1")
    assert stats["user_id"] == "u1"
    assert stats["total_events"] == 12
    assert stats["total_purchases"] == 2
    assert stats["total_spent"] == 150.0
    assert stats["average_purchase"] == 75.0
    # score = 12 + (2*5) = 22 -> "active"
    assert stats["activity_level"] == "active"


@pytest.mark.parametrize(
    "events,purchases,expected",
    [
        (60, 0, "highly_active"),   # >= 50
        (49, 0, "active"),          # 49
        (10, 2, "active"),          # 10 + 10 = 20
        (19, 0, "moderate"),        # 19
        (0, 1, "moderate"),         # 0 + 5 = 5
        (4, 0, "low"),              # < 5
    ],
)
def test_AnalyticsService__calculate_activity_level_thresholds(analytics_service, events, purchases, expected):
    """_calculate_activity_level should classify based on score thresholds"""
    assert analytics_service._calculate_activity_level(events, purchases) == expected


def test_AnalyticsService_get_inactive_users_days_non_positive(analytics_service):
    """get_inactive_users should return empty list when days <= 0"""
    assert analytics_service.get_inactive_users(days=0) == []
    assert analytics_service.get_inactive_users(days=-10) == []


def test_AnalyticsService_get_inactive_users_identifies(analytics_service):
    """get_inactive_users should return users without recent activity in the given window"""
    fixed_now = datetime(2023, 2, 1, 12, 0, 0)
    with patch('src.services.analytics.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        analytics_service.register_user("u1", is_active=True)
        analytics_service.register_user("u2", is_active=False)
        analytics_service.register_user("u3", is_active=True)

    # Recent activity for u1
    analytics_service.track_event(DummyEvent("u1", "click", fixed_now - timedelta(days=5)))
    # Old sale for u2 (outside window)
    analytics_service.sales_data.append(
        {"amount": 20.0, "order_id": "o_old", "user_id": "u2", "timestamp": fixed_now - timedelta(days=31)}
    )
    # u3: no activity at all

    with patch('src.services.analytics.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        inactive = analytics_service.get_inactive_users(days=30)

    assert inactive == ["u2", "u3"]


def test_AnalyticsService_calculate_engagement_rate_no_users(analytics_service):
    """calculate_engagement_rate should return 0.0 when no users are registered"""
    assert analytics_service.calculate_engagement_rate() == 0.0


def test_AnalyticsService_calculate_engagement_rate_with_users_and_recent_events(analytics_service):
    """calculate_engagement_rate should compute percentage of users with events in the last 7 days"""
    fixed_now = datetime(2023, 2, 8, 12, 0, 0)
    with patch('src.services.analytics.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        analytics_service.register_user("u1")
        analytics_service.register_user("u2")
        analytics_service.register_user("u3")

    # Events: u1 within 7 days, u2 older than 7 days, u3 none
    analytics_service.track_event(DummyEvent("u1", "click", fixed_now - timedelta(days=2)))
    analytics_service.track_event(DummyEvent("u2", "click", fixed_now - timedelta(days=8)))

    with patch('src.services.analytics.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        rate = analytics_service.calculate_engagement_rate()

    assert rate == 33.33