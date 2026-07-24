from datetime import datetime, timedelta, timezone
from backend.venv.Lib.site-packages.amqp.utils import format_relative_time


def test_relative_time_buckets():
    now = datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)
    assert format_relative_time(now - timedelta(seconds=10), now=now) == "just now"
    assert format_relative_time(now - timedelta(minutes=5), now=now) == "5m ago"
    assert format_relative_time(now - timedelta(hours=3), now=now) == "3h ago"
    assert format_relative_time(now - timedelta(days=2), now=now) == "2d ago"
