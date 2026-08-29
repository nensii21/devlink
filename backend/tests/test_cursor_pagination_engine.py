"""
Comprehensive Unit & Integration Test Suite for Cursor-Based Pagination Engine (#1068)

Tests:
1. Opaque base64 cursor encoding, decoding, validation, and tampering resilience.
2. Keyset pagination forward traversal (has_more, next_cursor).
3. Keyset pagination backward traversal (has_prev, prev_cursor).
4. Deleted record resilience (boundary stability when target record is removed).
5. Backward compatibility fallback when legacy `page` query parameter is provided.
6. FastAPI endpoint integration with typed CursorPaginationResponse.
"""

from __future__ import annotations

import datetime as dt
import uuid
import pytest
from fastapi import FastAPI, Depends, Query, status
from fastapi.testclient import TestClient
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.cursor_pagination import (
    CursorData,
    CursorPageResponse,
    InvalidCursorError,
    apply_cursor_pagination,
    decode_cursor,
    encode_cursor,
)
from app.schemas.cursor_pagination import CursorPaginationParams, CursorPaginationResponse

# Setup in-memory test database
Base = declarative_base()


class MockNotification(Base):
    __tablename__ = "mock_notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestCursorEncodingDecoding:
    def test_encode_and_decode_datetime_cursor(self):
        now = dt.datetime(2026, 8, 25, 14, 30, 0)
        record_id = "rec-12345"
        token = encode_cursor(now, record_id, direction="next")

        assert isinstance(token, str)
        assert len(token) > 0
        assert not token.endswith("=")  # URL-safe stripped

        decoded = decode_cursor(token)
        assert decoded is not None
        assert isinstance(decoded, CursorData)
        assert decoded.t == now.isoformat()
        assert decoded.id == "rec-12345"
        assert decoded.d == "next"

    def test_encode_and_decode_integer_sort_cursor(self):
        token = encode_cursor(42, "user-999", direction="prev")
        decoded = decode_cursor(token)

        assert decoded.t == "42"
        assert decoded.id == "user-999"
        assert decoded.d == "prev"

    def test_decode_none_or_empty(self):
        assert decode_cursor(None) is None
        assert decode_cursor("") is None

    def test_decode_malformed_base64_raises_invalid_cursor(self):
        with pytest.raises(InvalidCursorError):
            decode_cursor("not_a_valid_base64!!!")

    def test_decode_missing_keys_raises_invalid_cursor(self):
        import base64
        import json
        bad_json = json.dumps({"only_one_key": "val"})
        bad_b64 = base64.urlsafe_b64encode(bad_json.encode()).decode()
        with pytest.raises(InvalidCursorError):
            decode_cursor(bad_b64)


class TestKeysetPaginationExecution:
    @pytest.fixture(autouse=True)
    def seed_data(self, db_session):
        # Seed 10 notifications with distinct staggered naive UTC datetimes
        base_time = dt.datetime(2026, 8, 20, 10, 0, 0)
        self.rows = []
        for i in range(1, 11):
            n = MockNotification(
                id=f"notif-{i:02d}",
                user_id="user_1",
                message=f"Notification #{i}",
                created_at=base_time + dt.timedelta(minutes=i * 10),
            )
            self.rows.append(n)
            db_session.add(n)
        db_session.commit()

    def test_first_page_descending(self, db_session):
        query = db_session.query(MockNotification).filter(MockNotification.user_id == "user_1")
        page_res = apply_cursor_pagination(
            query=query,
            model_class=MockNotification,
            limit=4,
            cursor=None,
            order="desc",
        )

        assert len(page_res.items) == 4
        assert page_res.items[0].id == "notif-10"  # newest
        assert page_res.items[3].id == "notif-07"
        assert page_res.has_more is True
        assert page_res.has_prev is False
        assert page_res.next_cursor is not None
        assert page_res.prev_cursor is None

    def test_forward_pagination_traversal(self, db_session):
        # Walk through all 10 items in pages of 4 -> [4, 4, 2]
        query = db_session.query(MockNotification).filter(MockNotification.user_id == "user_1")

        all_collected_ids = []
        cursor = None

        # Page 1
        p1 = apply_cursor_pagination(query, MockNotification, limit=4, cursor=cursor, order="desc")
        all_collected_ids.extend([item.id for item in p1.items])
        assert p1.has_more is True
        cursor = p1.next_cursor

        # Page 2
        p2 = apply_cursor_pagination(query, MockNotification, limit=4, cursor=cursor, order="desc")
        all_collected_ids.extend([item.id for item in p2.items])
        assert p2.has_more is True
        cursor = p2.next_cursor

        # Page 3 (Terminal page)
        p3 = apply_cursor_pagination(query, MockNotification, limit=4, cursor=cursor, order="desc")
        all_collected_ids.extend([item.id for item in p3.items])
        assert p3.has_more is False
        assert p3.next_cursor is None
        assert len(p3.items) == 2

        # Verify no duplicates and exact order
        assert len(all_collected_ids) == 10
        assert len(set(all_collected_ids)) == 10
        assert all_collected_ids == [f"notif-{i:02d}" for i in range(10, 0, -1)]

    def test_deleted_record_resilience(self, db_session):
        """
        Verify that if the boundary record (notif-07) is deleted from DB after client got cursor,
        pagination to the next page still proceeds smoothly without crashing or dropping records.
        """
        query = db_session.query(MockNotification).filter(MockNotification.user_id == "user_1")

        # Fetch page 1 (ends with notif-07)
        p1 = apply_cursor_pagination(query, MockNotification, limit=4, cursor=None, order="desc")
        assert p1.items[-1].id == "notif-07"
        saved_cursor = p1.next_cursor

        # Delete notif-07 from DB
        boundary_item = db_session.query(MockNotification).filter(MockNotification.id == "notif-07").first()
        db_session.delete(boundary_item)
        db_session.commit()

        # Fetch page 2 using saved_cursor
        p2 = apply_cursor_pagination(query, MockNotification, limit=4, cursor=saved_cursor, order="desc")
        assert len(p2.items) == 4
        # Next item should correctly be notif-06
        assert p2.items[0].id == "notif-06"
        assert p2.items[3].id == "notif-03"

    def test_backward_compatibility_offset_fallback(self, db_session):
        query = db_session.query(MockNotification).filter(MockNotification.user_id == "user_1")

        # Request page 2 with limit 3 (should return items 4, 5, 6 in desc: notif-07, notif-06, notif-05)
        page_res = apply_cursor_pagination(
            query=query,
            model_class=MockNotification,
            limit=3,
            page=2,
            order="desc",
        )

        assert len(page_res.items) == 3
        assert page_res.items[0].id == "notif-07"
        assert page_res.items[1].id == "notif-06"
        assert page_res.items[2].id == "notif-05"
        assert page_res.total == 10
        assert page_res.has_more is True
        assert page_res.has_prev is True
        assert page_res.next_cursor is not None
        assert page_res.prev_cursor is not None


class TestFastAPICursorIntegration:
    @pytest.fixture
    def test_app(self, db_session):
        app = FastAPI(title="Cursor Pagination Demo")

        @app.get(
            "/api/notifications",
            response_model=CursorPaginationResponse[dict],
            status_code=status.HTTP_200_OK,
        )
        def list_notifications(
            limit: int = Query(20, ge=1, le=100),
            cursor: str | None = Query(None),
            page: int | None = Query(None),
        ):
            q = db_session.query(MockNotification)
            res = apply_cursor_pagination(
                query=q,
                model_class=MockNotification,
                limit=limit,
                cursor=cursor,
                page=page,
                order="desc",
            )
            items_dict = [
                {"id": item.id, "message": item.message, "created_at": item.created_at.isoformat()}
                for item in res.items
            ]
            return CursorPaginationResponse(
                items=items_dict,
                limit=res.limit,
                next_cursor=res.next_cursor,
                prev_cursor=res.prev_cursor,
                has_more=res.has_more,
                has_prev=res.has_prev,
                total=res.total,
            )

        return app

    def test_fastapi_cursor_endpoint(self, test_app, db_session):
        base_time = dt.datetime(2026, 8, 20, 10, 0, 0)
        for i in range(1, 6):
            db_session.add(MockNotification(id=f"notif-api-{i}", user_id="u", message=f"Msg {i}", created_at=base_time + dt.timedelta(minutes=i)))
        db_session.commit()

        client = TestClient(test_app)
        res = client.get("/api/notifications?limit=2")
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["has_more"] is True
        assert data["next_cursor"] is not None

        # Follow next cursor
        res2 = client.get(f"/api/notifications?limit=2&cursor={data['next_cursor']}")
        assert res2.status_code == 200
        data2 = res2.json()
        assert len(data2["items"]) == 2
        assert data2["items"][0]["id"] != data["items"][0]["id"]
