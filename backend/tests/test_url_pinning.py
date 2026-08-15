"""
Tests for address pinning, and for the URL normalisation the cache key uses.

The SSRF guard already resolved a hostname and checked every address it got
back. What it did not do was make the *connection* go to one of those
addresses -- it handed the hostname to ``httpx``, which resolved it again. That
second lookup is a second chance for DNS to answer differently, which is the
whole of the rebinding attack.

These tests do not do DNS. They inject a resolver and a transport, and assert
on what the HTTP client was actually asked to connect to.
"""

from __future__ import annotations

import httpx
import pytest

from app.services import link_preview_service as lps
from app.utils import url_safety
from app.utils.url_safety import (
    UnsafeURL,
    format_host_for_url,
    normalise_url,
    pin_target,
    validate_outbound_url,
)

PUBLIC_V4 = "93.184.216.34"
OTHER_V4 = "93.184.216.35"
PUBLIC_V6 = "2606:2800:220:1:248:1893:25c8:1946"


def resolver_for(mapping):
    """A fake DNS resolver backed by a dict of host -> addresses."""

    def _resolve(host):
        if host not in mapping:
            raise UnsafeURL(f"Could not resolve host: {host}")
        return tuple(mapping[host])

    return _resolve


PUBLIC = resolver_for({"example.com": [PUBLIC_V4]})


# ----------------------------------------------------------------------
# format_host_for_url
# ----------------------------------------------------------------------


class TestFormatHost:
    def test_leaves_a_hostname_alone(self):
        assert format_host_for_url("example.com") == "example.com"

    def test_leaves_ipv4_alone(self):
        assert format_host_for_url(PUBLIC_V4) == PUBLIC_V4

    def test_brackets_ipv6(self):
        assert format_host_for_url("::1") == "[::1]"
        assert format_host_for_url(PUBLIC_V6) == f"[{PUBLIC_V6}]"

    def test_does_not_double_bracket(self):
        # Already-bracketed input is not a valid IP literal, so it falls
        # through the hostname path unchanged rather than becoming [[::1]].
        assert format_host_for_url("[::1]") == "[::1]"


# ----------------------------------------------------------------------
# pin_target
# ----------------------------------------------------------------------


class TestPinTarget:
    def test_url_carries_the_address_not_the_hostname(self):
        target = validate_outbound_url("https://example.com/post", resolver=PUBLIC)
        pinned = pin_target(target)

        assert pinned.address == PUBLIC_V4
        assert f"//{PUBLIC_V4}:443/" in pinned.url
        assert "example.com" not in pinned.url

    def test_host_header_preserves_virtual_hosting(self):
        target = validate_outbound_url("https://example.com/post", resolver=PUBLIC)
        pinned = pin_target(target)

        # Without this, name-based virtual hosts serve the wrong site (or a 421).
        assert pinned.headers["Host"] == "example.com"

    def test_sni_hostname_preserves_certificate_validation(self):
        target = validate_outbound_url("https://example.com/post", resolver=PUBLIC)
        pinned = pin_target(target)

        # Without this, TLS uses the IP as the server name and every
        # certificate on the internet fails to verify.
        assert pinned.extensions["sni_hostname"] == "example.com"

    def test_path_and_query_survive(self):
        target = validate_outbound_url(
            "https://example.com/a/b?x=1&y=2", resolver=PUBLIC
        )
        pinned = pin_target(target)

        assert "/a/b" in pinned.url
        assert "x=1" in pinned.url
        assert "y=2" in pinned.url

    def test_a_pathless_url_pins_to_root(self):
        target = validate_outbound_url("https://example.com", resolver=PUBLIC)
        pinned = pin_target(target)

        assert pinned.url == f"https://{PUBLIC_V4}:443/"

    def test_non_default_port_appears_in_the_host_header(self):
        resolver = resolver_for({"example.com": [PUBLIC_V4]})
        target = validate_outbound_url("http://example.com:8080/x", resolver=resolver)
        pinned = pin_target(target)

        assert pinned.headers["Host"] == "example.com:8080"
        assert f"//{PUBLIC_V4}:8080/" in pinned.url

    def test_default_port_is_left_out_of_the_host_header(self):
        target = validate_outbound_url("https://example.com/x", resolver=PUBLIC)

        assert pin_target(target).headers["Host"] == "example.com"

    def test_ipv6_address_is_bracketed_in_the_pinned_url(self):
        resolver = resolver_for({"example.com": [PUBLIC_V6]})
        target = validate_outbound_url("https://example.com/x", resolver=resolver)
        pinned = pin_target(target)

        assert f"[{PUBLIC_V6}]:443" in pinned.url
        # And the result has to be a URL httpx can actually parse.
        assert httpx.URL(pinned.url).host == PUBLIC_V6

    def test_a_specific_verified_address_can_be_chosen(self):
        resolver = resolver_for({"example.com": [PUBLIC_V4, OTHER_V4]})
        target = validate_outbound_url("https://example.com/x", resolver=resolver)

        assert pin_target(target, OTHER_V4).address == OTHER_V4

    def test_an_unverified_address_is_refused(self):
        target = validate_outbound_url("https://example.com/x", resolver=PUBLIC)

        # Pinning to an address that was never checked would defeat the point.
        with pytest.raises(UnsafeURL):
            pin_target(target, "169.254.169.254")

    def test_choosing_is_deterministic(self):
        resolver = resolver_for({"example.com": [OTHER_V4, PUBLIC_V4]})
        target = validate_outbound_url("https://example.com/x", resolver=resolver)

        assert pin_target(target).address == pin_target(target).address


# ----------------------------------------------------------------------
# The fetch path
# ----------------------------------------------------------------------


@pytest.fixture
def pinned_fetch(monkeypatch):
    """
    Drive `_fetch_html` with an injected resolver and transport.

    Returns a callable `(url, mapping, handler) -> (result, requests)` where
    `requests` is every request the transport saw, so a test can assert on
    where the client was actually pointed.
    """

    def run(url, mapping, handler):
        resolver = resolver_for(mapping)
        monkeypatch.setattr(
            lps,
            "validate_outbound_url",
            lambda u: url_safety.validate_outbound_url(u, resolver=resolver),
        )

        seen: list[httpx.Request] = []

        def recording_handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return handler(request)

        real_client = httpx.Client

        def factory(**kwargs):
            kwargs.pop("transport", None)
            return real_client(
                transport=httpx.MockTransport(recording_handler), **kwargs
            )

        monkeypatch.setattr(httpx, "Client", factory)

        service = lps.LinkPreviewService(
            timeout=1.0, max_bytes=100_000, max_redirects=3
        )
        target = url_safety.validate_outbound_url(url, resolver=resolver)
        return service._fetch_html(target), seen

    return run


def html_response(body: str = "<html><head><title>Hi</title></head></html>"):
    return httpx.Response(200, text=body, headers={"content-type": "text/html"})


class TestFetchPinning:
    def test_the_client_connects_to_the_verified_address(self, pinned_fetch):
        result, seen = pinned_fetch(
            "https://example.com/post",
            {"example.com": [PUBLIC_V4]},
            lambda _r: html_response(),
        )

        assert result is not None
        assert len(seen) == 1
        # This is the fix: httpx was previously given "example.com" and got to
        # resolve it a second time.
        assert seen[0].url.host == PUBLIC_V4
        assert seen[0].headers["Host"] == "example.com"

    def test_tls_still_gets_the_right_server_name(self, pinned_fetch):
        _result, seen = pinned_fetch(
            "https://example.com/post",
            {"example.com": [PUBLIC_V4]},
            lambda _r: html_response(),
        )

        assert seen[0].extensions["sni_hostname"] == "example.com"

    def test_rebinding_between_check_and_connect_cannot_reach_metadata(self):
        """
        A record whose answer changes between lookups.

        This is the attack the pinning exists for. The resolver hands out a
        public address the first time it is asked and the cloud metadata
        address every time after, which is what a hostile record with a 0-second
        TTL does. Validation sees the public answer and passes.

        Before, the hostname went to httpx, httpx resolved it again, got
        169.254.169.254, and fetched it. Now the address validation approved is
        baked into the request, so there is no second lookup to poison.
        """
        lookups = []

        def rebinding_resolver(host):
            lookups.append(host)
            return (PUBLIC_V4,) if len(lookups) == 1 else ("169.254.169.254",)

        target = validate_outbound_url(
            "https://example.com/post", resolver=rebinding_resolver
        )
        pinned = pin_target(target)

        assert len(lookups) == 1
        assert pinned.address == PUBLIC_V4
        assert "169.254.169.254" not in pinned.url
        # And the second answer, had anyone asked for it, would have been
        # refused outright.
        assert rebinding_resolver("example.com") == ("169.254.169.254",)
        with pytest.raises(UnsafeURL):
            validate_outbound_url(
                "https://example.com/post", resolver=lambda _h: ("169.254.169.254",)
            )

    def test_each_redirect_hop_is_pinned_to_its_own_address(self, pinned_fetch):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.host == PUBLIC_V4:
                return httpx.Response(
                    302, headers={"location": "https://other.test/final"}
                )
            return html_response()

        result, seen = pinned_fetch(
            "https://example.com/start",
            {"example.com": [PUBLIC_V4], "other.test": [OTHER_V4]},
            handler,
        )

        assert result is not None
        assert [r.url.host for r in seen] == [PUBLIC_V4, OTHER_V4]
        assert [r.headers["Host"] for r in seen] == ["example.com", "other.test"]

    def test_a_redirect_to_a_private_address_is_still_refused(self, pinned_fetch):
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                302, headers={"location": "http://metadata.test/latest/meta-data/"}
            )

        result, seen = pinned_fetch(
            "https://example.com/start",
            {"example.com": [PUBLIC_V4], "metadata.test": ["169.254.169.254"]},
            handler,
        )

        assert result is None
        # We connected once, saw the redirect, and refused to take it.
        assert len(seen) == 1

    def test_relative_redirects_resolve_against_the_logical_url(self, pinned_fetch):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/start":
                return httpx.Response(302, headers={"location": "/moved"})
            return html_response()

        result, seen = pinned_fetch(
            "https://example.com/start",
            {"example.com": [PUBLIC_V4]},
            handler,
        )

        assert result is not None
        assert [r.url.path for r in seen] == ["/start", "/moved"]

    def test_final_url_is_the_logical_url_not_the_pinned_one(self, pinned_fetch):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/start":
                return httpx.Response(
                    302, headers={"location": "https://other.test/end"}
                )
            return html_response()

        result, _seen = pinned_fetch(
            "https://example.com/start",
            {"example.com": [PUBLIC_V4], "other.test": [OTHER_V4]},
            handler,
        )

        assert result is not None
        _body, final_url = result
        # An IP has no business showing up in a preview card.
        assert final_url == "https://other.test/end"
        assert OTHER_V4 not in final_url

    def test_a_non_html_content_type_is_not_parsed(self, pinned_fetch):
        result, _seen = pinned_fetch(
            "https://example.com/file.zip",
            {"example.com": [PUBLIC_V4]},
            lambda _r: httpx.Response(
                200, content=b"PK\x03\x04", headers={"content-type": "application/zip"}
            ),
        )

        assert result is None

    def test_the_redirect_budget_is_bounded(self, pinned_fetch):
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                302, headers={"location": "https://example.com/again"}
            )

        result, seen = pinned_fetch(
            "https://example.com/start",
            {"example.com": [PUBLIC_V4]},
            handler,
        )

        assert result is None
        assert len(seen) == 4  # max_redirects=3, so four attempts


# ----------------------------------------------------------------------
# normalise_url
# ----------------------------------------------------------------------


class TestNormaliseUrl:
    def test_lowercases_scheme_and_host(self):
        assert normalise_url("HTTPS://Example.COM/Path") == "https://example.com/Path"

    def test_drops_a_redundant_default_port(self):
        assert normalise_url("https://example.com:443/x") == "https://example.com/x"

    def test_keeps_a_meaningful_port(self):
        assert normalise_url("http://example.com:8080/x") == "http://example.com:8080/x"

    def test_drops_the_fragment(self):
        assert normalise_url("https://example.com/x#section") == "https://example.com/x"

    def test_supplies_a_root_path(self):
        assert normalise_url("https://example.com") == "https://example.com/"

    def test_ipv6_host_keeps_its_brackets(self):
        # Previously this produced "http://::1:8080/x", which does not parse --
        # urlparse reports no hostname at all for it.
        result = normalise_url("http://[::1]:8080/x")

        assert result == "http://[::1]:8080/x"
        assert httpx.URL(result).host == "::1"

    def test_ipv6_host_on_the_default_port(self):
        result = normalise_url(f"https://[{PUBLIC_V6}]/x")

        assert result == f"https://[{PUBLIC_V6}]/x"
        assert httpx.URL(result).host == PUBLIC_V6

    def test_query_order_does_not_change_the_key(self):
        # Two spellings of the same request should not be two cache entries,
        # two outbound fetches and two rate-limit slots.
        assert normalise_url("https://example.com/x?b=2&a=1") == normalise_url(
            "https://example.com/x?a=1&b=2"
        )

    def test_repeated_keys_keep_their_relative_order(self):
        # ?tag=a&tag=b is not necessarily the same request as ?tag=b&tag=a.
        assert normalise_url("https://example.com/x?tag=a&tag=b") != normalise_url(
            "https://example.com/x?tag=b&tag=a"
        )

    def test_blank_values_are_preserved(self):
        assert (
            normalise_url("https://example.com/x?flag=")
            == "https://example.com/x?flag="
        )

    def test_an_empty_query_leaves_no_question_mark(self):
        assert normalise_url("https://example.com/x?") == "https://example.com/x"

    def test_is_idempotent(self):
        once = normalise_url("HTTPS://Example.com:443/x?b=2&a=1#frag")

        assert normalise_url(once) == once
