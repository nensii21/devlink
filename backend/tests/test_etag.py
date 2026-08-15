"""
Tests for ETag generation and conditional request handling.

A throwaway FastAPI app is used instead of the real one so the assertions stay
about the middleware rather than about whichever router happens to be mounted.
"""

import pytest
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response, StreamingResponse
from fastapi.testclient import TestClient

from app.core.http_cache import (
    etag_matches,
    generate_etag,
    is_etaggable_content_type,
    merge_vary,
    parse_if_none_match,
)
from app.middleware.etag import ETagMiddleware


@pytest.fixture
def client():
    app = FastAPI()
    app.add_middleware(ETagMiddleware)

    @app.get("/items")
    def list_items():
        return {"items": [{"id": 1, "name": "devlink"}]}

    @app.get("/empty")
    def empty_body():
        return Response(status_code=200)

    @app.get("/text")
    def plain_text():
        return PlainTextResponse("hello")

    @app.get("/download")
    def binary_download():
        return Response(
            content=b"\x00\x01\x02",
            media_type="application/octet-stream",
        )

    @app.get("/stream")
    def stream():
        def chunks():
            for index in range(3):
                yield f"chunk-{index}\n"

        return StreamingResponse(chunks(), media_type="text/event-stream")

    @app.get("/preset-etag")
    def preset_etag():
        return Response(
            content='{"ok":true}',
            media_type="application/json",
            headers={"ETag": '"handler-owned"'},
        )

    @app.get("/no-store")
    def no_store():
        return Response(
            content='{"secret":true}',
            media_type="application/json",
            headers={"Cache-Control": "no-store"},
        )

    @app.get("/missing")
    def missing():
        return Response(
            content='{"detail":"not found"}',
            media_type="application/json",
            status_code=404,
        )

    @app.post("/items")
    def create_item():
        return {"created": True}

    with TestClient(app) as test_client:
        yield test_client


# ----------------------------------------------------------------------
# Pure helpers
# ----------------------------------------------------------------------


def test_generate_etag_is_stable_and_quoted():
    first = generate_etag(b'{"a":1}')
    second = generate_etag(b'{"a":1}')

    assert first == second
    assert first.startswith('"') and first.endswith('"')


def test_generate_etag_differs_for_different_bodies():
    assert generate_etag(b'{"a":1}') != generate_etag(b'{"a":2}')


def test_generate_etag_weak_variant():
    assert generate_etag(b"body", weak=True).startswith('W/"')


@pytest.mark.parametrize(
    "header,expected",
    [
        (None, []),
        ("", []),
        ('"abc"', ['"abc"']),
        ('"abc", "def"', ['"abc"', '"def"']),
        ('W/"abc" , "def"', ['W/"abc"', '"def"']),
        ("*", ["*"]),
    ],
)
def test_parse_if_none_match(header, expected):
    assert parse_if_none_match(header) == expected


def test_etag_matches_uses_weak_comparison():
    assert etag_matches('"abc"', ['W/"abc"'])
    assert etag_matches('W/"abc"', ['"abc"'])
    assert etag_matches('"abc"', ['"zzz"', '"abc"'])


def test_etag_matches_wildcard():
    assert etag_matches('"anything"', ["*"])


def test_etag_does_not_match_unrelated_tag():
    assert not etag_matches('"abc"', ['"def"'])
    assert not etag_matches('"abc"', [])


@pytest.mark.parametrize(
    "content_type,expected",
    [
        ("application/json", True),
        ("application/json; charset=utf-8", True),
        ("APPLICATION/JSON", True),
        ("text/plain", True),
        ("image/png", False),
        ("application/octet-stream", False),
        (None, False),
    ],
)
def test_is_etaggable_content_type(content_type, expected):
    assert is_etaggable_content_type(content_type) is expected


def test_merge_vary_appends_without_duplicating():
    assert merge_vary(None, ["Authorization"]) == "Authorization"
    assert (
        merge_vary("Accept-Encoding", ["Authorization"])
        == "Accept-Encoding, Authorization"
    )
    assert merge_vary("authorization", ["Authorization"]) == "authorization"


def test_merge_vary_preserves_wildcard():
    assert merge_vary("*", ["Authorization"]) == "*"


# ----------------------------------------------------------------------
# Middleware behaviour
# ----------------------------------------------------------------------


def test_get_response_carries_an_etag(client):
    response = client.get("/items")

    assert response.status_code == 200
    assert response.headers["etag"]
    assert response.headers["cache-control"] == "private, no-cache"
    assert "Authorization" in response.headers["vary"]


def test_matching_if_none_match_returns_304_with_no_body(client):
    first = client.get("/items")
    etag = first.headers["etag"]

    second = client.get("/items", headers={"If-None-Match": etag})

    assert second.status_code == 304
    assert second.content == b""
    assert second.headers["etag"] == etag
    # A 304 must not describe a payload it is not sending.
    assert "content-type" not in second.headers


def test_weak_if_none_match_still_matches(client):
    etag = client.get("/items").headers["etag"]

    response = client.get("/items", headers={"If-None-Match": f"W/{etag}"})

    assert response.status_code == 304


def test_wildcard_if_none_match_returns_304(client):
    response = client.get("/items", headers={"If-None-Match": "*"})

    assert response.status_code == 304


def test_non_matching_if_none_match_returns_full_body(client):
    response = client.get("/items", headers={"If-None-Match": '"stale"'})

    assert response.status_code == 200
    assert response.json() == {"items": [{"id": 1, "name": "devlink"}]}


def test_if_none_match_list_matches_any_member(client):
    etag = client.get("/items").headers["etag"]

    response = client.get("/items", headers={"If-None-Match": f'"other", {etag}'})

    assert response.status_code == 304


def test_post_responses_are_untouched(client):
    response = client.post("/items")

    assert response.status_code == 200
    assert "etag" not in response.headers


def test_error_responses_are_untouched(client):
    response = client.get("/missing")

    assert response.status_code == 404
    assert "etag" not in response.headers


def test_handler_supplied_etag_is_preserved(client):
    response = client.get("/preset-etag")

    assert response.headers["etag"] == '"handler-owned"'


def test_no_store_responses_are_skipped(client):
    response = client.get("/no-store")

    assert "etag" not in response.headers
    assert response.headers["cache-control"] == "no-store"


def test_binary_responses_are_skipped(client):
    response = client.get("/download")

    assert response.status_code == 200
    assert response.content == b"\x00\x01\x02"
    assert "etag" not in response.headers


def test_streaming_responses_pass_through(client):
    response = client.get("/stream")

    assert response.status_code == 200
    assert response.text == "chunk-0\nchunk-1\nchunk-2\n"
    assert "etag" not in response.headers


def test_empty_body_gets_no_etag(client):
    response = client.get("/empty")

    assert response.status_code == 200
    assert response.content == b""
    assert "etag" not in response.headers


def test_plain_text_is_tagged(client):
    response = client.get("/text")

    assert response.text == "hello"
    assert response.headers["etag"] == generate_etag(b"hello")


def test_oversized_body_streams_through_untagged():
    app = FastAPI()
    app.add_middleware(ETagMiddleware, max_body_size=16)

    @app.get("/big")
    def big():
        return {"payload": "x" * 512}

    with TestClient(app) as local_client:
        response = local_client.get("/big")

    assert response.status_code == 200
    assert response.json()["payload"] == "x" * 512
    assert "etag" not in response.headers


def test_etag_changes_when_the_representation_changes():
    app = FastAPI()
    app.add_middleware(ETagMiddleware)
    counter = {"value": 0}

    @app.get("/counter")
    def counter_endpoint():
        counter["value"] += 1
        return {"count": counter["value"]}

    with TestClient(app) as local_client:
        first = local_client.get("/counter").headers["etag"]
        second = local_client.get("/counter", headers={"If-None-Match": first})

    assert second.status_code == 200
    assert second.headers["etag"] != first


def test_middleware_can_be_disabled(monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "ENABLE_ETAG", False)

    app = FastAPI()
    app.add_middleware(ETagMiddleware)

    @app.get("/items")
    def list_items():
        return {"ok": True}

    with TestClient(app) as local_client:
        response = local_client.get("/items")

    assert response.status_code == 200
    assert "etag" not in response.headers
