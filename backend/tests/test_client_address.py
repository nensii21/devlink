"""
Client address resolution behind a proxy.

The header these tests are about, ``X-Forwarded-For``, is an ordinary request
header. Any client can send one and claim any address it likes. So the
interesting assertions here are not "the header is read correctly" but "the
header is ignored when it should be" -- an address that can be forged is
worse than no address at all, because everything downstream (rate limits,
audit records, abuse tracking) then keys on a value the attacker chooses.
"""

import pytest

from app.core import client_address as ca
from app.core.client_address import (
    UNKNOWN_ADDRESS,
    is_trusted_proxy,
    resolve_client_address,
)

# A proxy sits at 10.0.0.0/8; everything else is the open internet.
PROXY_CIDRS = "10.0.0.0/8"

PROXY = "10.0.0.7"
SECOND_PROXY = "10.0.0.8"
CLIENT = "203.0.113.45"
OTHER_CLIENT = "198.51.100.22"


@pytest.fixture
def trusted(monkeypatch):
    """Configure a trusted proxy range for the duration of a test."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "TRUSTED_PROXY_CIDRS", PROXY_CIDRS, raising=False)
    ca.reset_caches()
    yield
    ca.reset_caches()


@pytest.fixture
def trusts_nothing(monkeypatch):
    """The default configuration: no proxy is trusted."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "TRUSTED_PROXY_CIDRS", "", raising=False)
    ca.reset_caches()
    yield
    ca.reset_caches()


# ---------------------------------------------------------------------------
# Forged headers
# ---------------------------------------------------------------------------


def test_header_from_an_untrusted_peer_is_ignored(trusted):
    """
    The whole point. A client connecting directly and sending its own
    ``X-Forwarded-For`` must not get to pick its own rate-limit bucket.
    """
    resolved = resolve_client_address(peer=CLIENT, forwarded_for="1.2.3.4")

    assert resolved == CLIENT


def test_forged_header_cannot_rotate_the_bucket(trusted):
    """
    Ten different forged values from the same untrusted peer all resolve to
    the same address, so they all count against the same limit.
    """
    resolved = {
        resolve_client_address(peer=CLIENT, forwarded_for=f"1.2.3.{n}")
        for n in range(10)
    }

    assert resolved == {CLIENT}


def test_header_is_ignored_entirely_when_nothing_is_trusted(trusts_nothing):
    """The default configuration behaves as though the header did not exist."""
    assert resolve_client_address(peer=PROXY, forwarded_for=CLIENT) == PROXY
    assert resolve_client_address(peer=CLIENT, forwarded_for=OTHER_CLIENT) == CLIENT


# ---------------------------------------------------------------------------
# Genuine proxies
# ---------------------------------------------------------------------------


def test_header_from_a_trusted_peer_is_honoured(trusted):
    assert resolve_client_address(peer=PROXY, forwarded_for=CLIENT) == CLIENT


def test_multi_hop_chain_takes_the_rightmost_untrusted_hop(trusted):
    """
    ``client, proxy_a, proxy_b`` -- walking from the right skips our own two
    hops and lands on the client.
    """
    chain = f"{CLIENT}, {PROXY}, {SECOND_PROXY}"

    assert resolve_client_address(peer=PROXY, forwarded_for=chain) == CLIENT


def test_client_supplied_prefix_is_discarded(trusted):
    """
    A client that sends ``X-Forwarded-For: 1.2.3.4`` has its real address
    appended by the proxy. Walking from the right finds the appended one and
    never reaches the fabricated prefix.
    """
    chain = f"1.2.3.4, {CLIENT}"

    assert resolve_client_address(peer=PROXY, forwarded_for=chain) == CLIENT


def test_chain_of_only_trusted_hops_falls_back_to_the_peer(trusted):
    """A request that originated inside the perimeter."""
    chain = f"{PROXY}, {SECOND_PROXY}"

    assert resolve_client_address(peer=PROXY, forwarded_for=chain) == PROXY


def test_junk_in_the_chain_stops_the_walk(trusted):
    """
    An unparseable hop is not something we can vouch for, and walking past it
    would let a client hide a real hop behind junk.
    """
    chain = f"{CLIENT}, _hidden, {PROXY}"

    assert resolve_client_address(peer=PROXY, forwarded_for=chain) == PROXY


# ---------------------------------------------------------------------------
# Address shapes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entry,expected",
    [
        (CLIENT, CLIENT),
        (f"{CLIENT}:44321", CLIENT),
        ("2001:db8::1", "2001:db8::1"),
        ("[2001:db8::1]", "2001:db8::1"),
        ("[2001:db8::1]:44321", "2001:db8::1"),
        (f"  {CLIENT}  ", CLIENT),
    ],
)
def test_address_shapes_are_parsed(trusted, entry, expected):
    """Ports and IPv6 brackets both turn up in real forwarded chains."""
    assert resolve_client_address(peer=PROXY, forwarded_for=entry) == expected


def test_bare_ipv6_is_not_split_on_its_colons(trusted):
    """
    A naive ``split(":")[0]`` turns ``2001:db8::1`` into ``2001``. Only a
    single colon means "address with port".
    """
    assert (
        resolve_client_address(peer=PROXY, forwarded_for="2001:db8::1") == "2001:db8::1"
    )


# ---------------------------------------------------------------------------
# X-Real-IP
# ---------------------------------------------------------------------------


def test_real_ip_is_used_when_forwarded_for_is_absent(trusted):
    assert resolve_client_address(peer=PROXY, real_ip=CLIENT) == CLIENT


def test_forwarded_for_wins_over_real_ip(trusted):
    """``X-Forwarded-For`` carries the chain; ``X-Real-IP`` carries one hop."""
    resolved = resolve_client_address(
        peer=PROXY, forwarded_for=CLIENT, real_ip=OTHER_CLIENT
    )

    assert resolved == CLIENT


def test_real_ip_from_an_untrusted_peer_is_ignored(trusted):
    assert resolve_client_address(peer=CLIENT, real_ip="1.2.3.4") == CLIENT


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------


def test_missing_peer_reports_a_constant_not_none(trusts_nothing):
    """
    ``None`` would collapse every peer-less request into one key, which is
    the failure this module exists to prevent.
    """
    assert resolve_client_address(peer=None) == UNKNOWN_ADDRESS
    assert resolve_client_address(peer="") == UNKNOWN_ADDRESS


def test_empty_header_is_treated_as_absent(trusted):
    assert resolve_client_address(peer=PROXY, forwarded_for="") == PROXY
    assert resolve_client_address(peer=PROXY, forwarded_for="  ,  ") == PROXY


def test_malformed_cidr_entries_are_skipped_not_fatal(monkeypatch):
    """
    A fat-fingered environment variable should cost one trusted proxy, not
    the whole application. Dropping the entry fails closed.
    """
    from app.core.config import settings

    monkeypatch.setattr(
        settings, "TRUSTED_PROXY_CIDRS", "not-a-cidr, 10.0.0.0/8, 999.999.999.999/8"
    )
    ca.reset_caches()

    try:
        assert is_trusted_proxy(PROXY) is True
        assert is_trusted_proxy(CLIENT) is False
    finally:
        ca.reset_caches()


def test_single_host_is_accepted_as_a_cidr(monkeypatch):
    """People write a lone proxy as ``10.0.0.7``, not ``10.0.0.7/32``."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "TRUSTED_PROXY_CIDRS", PROXY)
    ca.reset_caches()

    try:
        assert is_trusted_proxy(PROXY) is True
        assert is_trusted_proxy(SECOND_PROXY) is False
    finally:
        ca.reset_caches()


def test_settings_list_property_splits_and_strips():
    from app.core.config import Settings

    settings = Settings(TRUSTED_PROXY_CIDRS=" 10.0.0.0/8 , 172.16.0.0/12 ,, ")

    assert settings.trusted_proxy_cidr_list == ["10.0.0.0/8", "172.16.0.0/12"]


# ---------------------------------------------------------------------------
# Rate limit keys
# ---------------------------------------------------------------------------


class _FakeRequest:
    """Enough of a Starlette request for the key function."""

    class _Client:
        def __init__(self, host):
            self.host = host

    def __init__(self, host, headers=None):
        self.client = self._Client(host) if host else None
        self.headers = headers or {}


def test_anonymous_requests_are_keyed_by_address(trusted):
    from app.core.client_address import rate_limit_key

    request = _FakeRequest(PROXY, {"x-forwarded-for": CLIENT})

    assert rate_limit_key(request) == f"ip:{CLIENT}"


def test_authenticated_requests_are_keyed_by_user(trusted):
    """
    Two users behind one NAT egress must not share a bucket, or the heavier
    one throttles the other.
    """
    from app.core.client_address import rate_limit_key
    from app.core.security import create_access_token

    user_a = "11111111-1111-1111-1111-111111111111"
    user_b = "22222222-2222-2222-2222-222222222222"

    def key_for(user_id):
        return rate_limit_key(
            _FakeRequest(
                PROXY,
                {
                    "x-forwarded-for": CLIENT,
                    "authorization": f"Bearer {create_access_token(user_id)}",
                },
            )
        )

    assert key_for(user_a) == f"user:{user_a}"
    assert key_for(user_a) != key_for(user_b)


def test_junk_credentials_fall_back_to_the_address(trusted):
    """
    Otherwise sending a garbage ``Authorization`` header on every request
    would be a way to dodge the limit entirely.
    """
    from app.core.client_address import rate_limit_key

    request = _FakeRequest(
        PROXY, {"x-forwarded-for": CLIENT, "authorization": "Bearer not-a-jwt"}
    )

    assert rate_limit_key(request) == f"ip:{CLIENT}"


def test_two_untrusted_clients_get_distinct_keys(trusts_nothing):
    """The regression: these used to be the same key behind a proxy."""
    from app.core.client_address import rate_limit_key

    first = rate_limit_key(_FakeRequest(CLIENT))
    second = rate_limit_key(_FakeRequest(OTHER_CLIENT))

    assert first != second
