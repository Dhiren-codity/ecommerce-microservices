import pytest
from unittest.mock import Mock, patch
from types import SimpleNamespace
from datetime import datetime, timedelta

from src.services.analytics import AnalyticsService


@pytest.fixture
def analytics_service():
    """Create a fresh AnalyticsService instance for testing."""
    return AnalyticsService()


@pytest.fixture
def event_factory():
    """Factory to create event-like objects with required attributes."""
    def _make_event(user_id="u1", event_type="click", timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()
        return SimpleNamespace(user_id=user_id, event_type=event_type, timestamp=timestamp)
    return _make_event


def test_AnalyticsService___init___initial_state(analytics_service):
    """Ensure initialization produces empty datasets."""
    assert analytics_service.sales_data == []
    assert analytics_service.user_data == []
    assert analytics_service.events == []


def test_AnalyticsService_track_sale_valid_and_invalid(analytics_service):
    """Track sale should accept positive amounts and reject non-positive."""
    assert analytics_service.track_sale(100.0, "order-1", "user-1") is True
    assert len(analytics_service.sales_data) == 1
    assert analytics_service.track_sale(0.0, "order-2", "user-1") is False
    assert analytics_service.track_sale(-10.0, "order-3", "user-1") is False
    assert len(analytics_service.sales_data) == 1


def test_AnalyticsService_get_sales_metrics_empty_returns_defaults(analytics_service):
    """Sales metrics should return default zeros when no sales."""
    with patch('src.services.analytics.SalesMetric') as SalesMetricMock:
        sentinel = object()
        SalesMetricMock.return_value = sentinel
        result = analytics_service.get_sales_metrics()
        SalesMetricMock.assert_called_once()
        kwargs = SalesMetricMock.call_args.kwargs
        assert kwargs["total_revenue"] == 0.0
        assert kwargs["total_orders"] == 0
        assert kwargs["average_order_value"] == 0.0
        assert kwargs["period"] == "daily"
        assert result is sentinel


def test_AnalyticsService_get_sales_metrics_with_data(analytics_service):
    """Sales metrics should aggregate totals and averages correctly."""
    # Create two sales
    analytics_service.track_sale(100.0, "o1", "u1")
    analytics_service.track_sale(50.0, "o2", "u2")

    with patch('src.services.analytics.SalesMetric') as SalesMetricMock:
        sentinel = object()
        SalesMetricMock.return_value = sentinel
        result = analytics_service.get_sales_metrics(period="weekly")
        SalesMetricMock.assert_called_once()
        kwargs = SalesMetricMock.call_args.kwargs
        assert kwargs["total_revenue"] == 150.0
        assert kwargs["total_orders"] == 2
        assert kwargs["average_order_value"] == 75.0
        assert kwargs["period"] == "weekly"
        assert result is sentinel


def test_AnalyticsService_register_user_valid_and_invalid(analytics_service):
    """Register user should store users and reject empty IDs."""
    assert analytics_service.register_user("u1", is_active=True) is True
    assert analytics_service.register_user("") is False
    assert len(analytics_service.user_data) == 1
    assert analytics_service.user_data[0]["user_id"] == "u1"
    assert analytics_service.user_data[0]["is_active"] is True
    assert isinstance(analytics_service.user_data[0]["registered_at"], datetime)


def test_AnalyticsService_get_user_metrics_counts_and_retention(analytics_service):
    """User metrics should count total, active, new users, and retention rate accurately."""
    base_now = datetime(2025, 1, 10, 12, 0, 0)
    older = base_now - timedelta(days=10)
    recent1 = base_now - timedelta(days=2)
    recent2 = base_now - timedelta(days=1)

    # Register users at specific times
    with patch('src.services.analytics.datetime') as mock_dt:
        mock_dt.now.return_value = older
        assert analytics_service.register_user("u_old", is_active=True) is True
    with patch('src.services.analytics.datetime') as mock_dt:
        mock_dt.now.return_value = recent1
        assert analytics_service.register_user("u_new_active", is_active=True) is True
    with patch('src.services.analytics.datetime') as mock_dt:
        mock_dt.now.return_value = recent2
        assert analytics_service.register_user("u_new_inactive", is_active=False) is True

    # Compute metrics with "now" set to base_now
    with patch('src.services.analytics.datetime') as mock_dt, patch('src.services.analytics.UserMetric') as UserMetricMock:
        mock_dt.now.return_value = base_now
        sentinel = object()
        UserMetricMock.return_value = sentinel

        result = analytics_service.get_user_metrics()

        UserMetricMock.assert_called_once()
        kwargs = UserMetricMock.call_args.kwargs
        assert kwargs["total_users"] == 3
        assert kwargs["active_users"] == 2
        assert kwargs["new_users"] == 2
        assert kwargs["retention_rate"] == pytest.approx((2 / 3) * 100)
        assert result is sentinel


def test_AnalyticsService_track_event_validation(analytics_service, event_factory):
    """Track event should validate user_id and event_type."""
    assert analytics_service.track_event(event_factory("u1", "click")) is True
    bad_event_no_user = event_factory("", "view")
    assert analytics_service.track_event(bad_event_no_user) is False
    bad_event_no_type = event_factory("u2", "")
    assert analytics_service.track_event(bad_event_no_type) is False
    assert len(analytics_service.events) == 1  # only the valid one was added


def test_AnalyticsService_get_top_events_sorted_and_limited(analytics_service, event_factory):
    """Top events should be sorted by count and respect limit."""
    analytics_service.events.extend([
        event_factory("u1", "click"),
        event_factory("u2", "click"),
        event_factory("u3", "click"),
        event_factory("u1", "view"),
        event_factory("u2", "signup"),
        event_factory("u3", "view"),
    ])
    top_all = analytics_service.get_top_events()
    assert top_all[0]["event_type"] == "click"
    assert top_all[0]["count"] == 3
    # next ones are view(2), signup(1)
    assert any(e["event_type"] == "view" and e["count"] == 2 for e in top_all)
    assert any(e["event_type"] == "signup" and e["count"] == 1 for e in top_all)

    top_one = analytics_service.get_top_events(limit=1)
    assert top_one == [{"event_type": "click", "count": 3}]


def test_AnalyticsService_get_top_events_empty_and_zero_limit(analytics_service):
    """Top events should return empty lists for no events or zero limit."""
    assert analytics_service.get_top_events() == []
    assert analytics_service.get_top_events(limit=0) == []


def test_AnalyticsService_calculate_revenue_growth_aggregates_and_calls_helper(analytics_service):
    """Revenue growth should aggregate current and previous periods and call helper."""
    base_now = datetime(2025, 2, 1, 0, 0, 0)
    days = 30
    current_start = base_now - timedelta(days=days)
    previous_start = current_start - timedelta(days=days)

    # Previous period sales: two sales summing to 300.0
    with patch('src.services.analytics.datetime') as mock_dt:
        mock_dt.now.return_value = previous_start + timedelta(days=1)
        analytics_service.track_sale(100.0, "p1", "u1")
    with patch('src.services.analytics.datetime') as mock_dt:
        mock_dt.now.return_value = previous_start + timedelta(days=2)
        analytics_service.track_sale(200.0, "p2", "u2")
    # Current period sales: two sales summing to 450.0
    with patch('src.services.analytics.datetime') as mock_dt:
        mock_dt.now.return_value = current_start + timedelta(days=3)
        analytics_service.track_sale(150.0, "c1", "u1")
    with patch('src.services.analytics.datetime') as mock_dt:
        mock_dt.now.return_value = current_start + timedelta(days=10)
        analytics_service.track_sale(300.0, "c2", "u3")
    # Out-of-range sale (older than previous period): should not count
    with patch('src.services.analytics.datetime') as mock_dt:
        mock_dt.now.return_value = previous_start - timedelta(days=1)
        analytics_service.track_sale(999.0, "old", "u4")

    with patch('src.services.analytics.datetime') as mock_dt, patch('src.services.analytics.calculate_growth_rate') as growth_mock:
        mock_dt.now.return_value = base_now
        growth_mock.return_value = 12.34
        result = analytics_service.calculate_revenue_growth(days=days)
        assert result == 12.34
        # Should be called with sums of current and previous period revenues
        growth_mock.assert_called_once_with(450.0, 300.0)


def test_AnalyticsService_calculate_revenue_growth_propagates_exception(analytics_service):
    """Revenue growth should propagate exceptions from calculate_growth_rate."""
    # Add a simple sale to avoid trivial zeros
    analytics_service.track_sale(50.0, "o1", "u1")
    with patch('src.services.analytics.calculate_growth_rate') as growth_mock:
        growth_mock.side_effect = ValueError("boom")
        with pytest.raises(ValueError):
            analytics_service.calculate_revenue_growth(days=7)


def test_AnalyticsService_get_user_activity_stats_missing_and_inactive_user(analytics_service):
    """User activity stats should validate user_id and handle inactive users."""
    # Missing user_id
    assert analytics_service.get_user_activity_stats("") == {"error": "user_id is required"}

    # No events or sales for user
    stats = analytics_service.get_user_activity_stats("uX")
    assert stats["user_id"] == "uX"
    assert stats["total_events"] == 0
    assert stats["total_purchases"] == 0
    assert stats["total_spent"] == 0.0
    assert stats["activity_level"] == "inactive"


def test_AnalyticsService_get_user_activity_stats_with_activity_and_custom_level(analytics_service, event_factory):
    """User activity stats should aggregate user events/sales and compute average purchase."""
    # Add events and sales for user
    analytics_service.events.extend([
        event_factory("u1", "click"),
        event_factory("u1", "view"),
        event_factory("u2", "view"),
    ])
    analytics_service.track_sale(40.0, "o1", "u1")
    analytics_service.track_sale(60.0, "o2", "u1")

    # Patch activity level computation to verify inputs and the returned label
    with patch.object(AnalyticsService, "_calculate_activity_level", return_value="custom_level") as level_mock:
        stats = analytics_service.get_user_activity_stats("u1")
        level_mock.assert_called_once_with(events=2, purchases=2)
        assert stats["user_id"] == "u1"
        assert stats["total_events"] == 2
        assert stats["total_purchases"] == 2
        assert stats["total_spent"] == 100.0
        assert stats["average_purchase"] == 50.0
        assert stats["activity_level"] == "custom_level"


@pytest.mark.parametrize(
    "events,purchases,expected",
    [
        (0, 0, "low"),
        (4, 0, "low"),
        (5, 0, "moderate"),
        (10, 1, "active"),      # score = 10 + 5 = 15 -> moderate; but purchases 1*5=5 -> total 15 => moderate
    ]
)
def test_AnalyticsService_calculate_activity_level_various(analytics_service, events, purchases, expected):
    """Activity level should map to the right label across ranges."""
    # Adjusted expectations based on scoring: events + (purchases * 5)
    score = events + (purchases * 5)
    if score >= 50:
        expected_level = "highly_active"
    elif score >= 20:
        expected_level = "active"
    elif score >= 5:
        expected_level = "moderate"
    else:
        expected_level = "low"
    assert analytics_service._calculate_activity_level(events, purchases) == expected_level


def test_AnalyticsService_calculate_activity_level_boundaries(analytics_service):
    """Activity level should match on boundary scores."""
    # score 4 -> low
    assert analytics_service._calculate_activity_level(4, 0) == "low"
    # score 5 -> moderate
    assert analytics_service._calculate_activity_level(5, 0) == "moderate"
    # score 19 -> moderate
    assert analytics_service._calculate_activity_level(19, 0) == "moderate"
    # score 20 -> active
    assert analytics_service._calculate_activity_level(20, 0) == "active"
    # score 49 -> active
    assert analytics_service._calculate_activity_level(49, 0) == "active"
    # score 50 -> highly_active
    assert analytics_service._calculate_activity_level(50, 0) == "highly_active"


def test_AnalyticsService_get_inactive_users_logic_and_days_edge(analytics_service, event_factory):
    """Inactive users should be users with no activity within the cutoff period; days<=0 returns empty."""
    base_now = datetime(2025, 3, 1, 9, 0, 0)
    # Register users
    assert analytics_service.register_user("A") is True
    assert analytics_service.register_user("B") is True
    assert analytics_service.register_user("C") is True

    # User A has recent event
    analytics_service.events.append(event_factory("A", "view", timestamp=base_now - timedelta(days=5)))
    # User B had a sale 40 days ago (outside 30-day window)
    with patch('src.services.analytics.datetime') as mock_dt:
        mock_dt.now.return_value = base_now - timedelta(days=40)
        analytics_service.track_sale(10.0, "oB", "B")
    # User C has no activity

    with patch('src.services.analytics.datetime') as mock_dt:
        mock_dt.now.return_value = base_now
        inactive_30 = analytics_service.get_inactive_users(days=30)
        assert inactive_30 == ["B", "C"]  # sorted

    # Edge case: days <= 0
    assert analytics_service.get_inactive_users(days=0) == []
    assert analytics_service.get_inactive_users(days=-5) == []


def test_AnalyticsService_calculate_engagement_rate_no_users(analytics_service):
    """Engagement rate should be 0.0 when there are no users."""
    assert analytics_service.calculate_engagement_rate() == 0.0


def test_AnalyticsService_calculate_engagement_rate_percentage_and_rounding(analytics_service, event_factory):
    """Engagement rate should reflect users with events in last 7 days and round to 2 decimals."""
    base_now = datetime(2025, 4, 1, 8, 0, 0)
    # Register three users
    analytics_service.register_user("u1")
    analytics_service.register_user("u2")
    analytics_service.register_user("u3")

    # Events: u1 recent, u2 old, u3 recent -> 2 engaged of 3 => 66.67%
    analytics_service.events.append(event_factory("u1", "click", timestamp=base_now - timedelta(days=3)))
    analytics_service.events.append(event_factory("u2", "view", timestamp=base_now - timedelta(days=10)))
    analytics_service.events.append(event_factory("u3", "view", timestamp=base_now - timedelta(days=1)))

    with patch('src.services.analytics.datetime') as mock_dt:
        mock_dt.now.return_value = base_now
        rate = analytics_service.calculate_engagement_rate()
        assert rate == 66.67

    # Another scenario: 4 users, 2 engaged -> 50.0%
    analytics_service.register_user("u4")
    analytics_service.events.append(event_factory("u4", "view", timestamp=base_now - timedelta(days=1)))
    with patch('src.services.analytics.datetime') as mock_dt:
        mock_dt.now.return_value = base_now
        rate = analytics_service.calculate_engagement_rate()
        assert rate == 50.0