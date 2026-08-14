"""
Working out which address a request actually came from.

Behind a reverse proxy the peer on the socket is the proxy, so every request
looks like it came from the same place. Anything that keys on the peer address
-- rate limiting, abuse tracking, audit logs -- collapses into a single bucket
shared by the entire internet.

The obvious fix, reading ``X-Forwarded-For``, is worse than the problem. That
header is a plain request header: a client can send one directly and claim any
address it likes. Trusting it unconditionally turns a per-IP rate limit into
no rate limit at all, because the attacker just varies the header.

So the header is only meaningful when the request genuinely arrived *from a
proxy we put there*. That is what this module establishes:

1. Is the immediate peer one of our trusted proxies? If not, the header is
   ignored entirely and the peer address is used.
2. If it is, walk the forwarded chain from the right, skipping the hops that
   are themselves trusted proxies, and take the first address that is not.
   That is the closest hop our infrastructure vouches for.

The chain is walked from the right because the left-hand entries are the ones
the client controls. A client sending ``X-Forwarded-For: 1.2.3.4`` gets its
real address appended by the proxy, so the rightmost untrusted entry is the
real one and everything to its left is unverified.

Configuration is fail-closed: ``TRUSTED_PROXY_CIDRS`` is empty by default,
which means no header is trusted and the behaviour matches what the code did
before this module existed.
"""

from __future__ import annotations

import ipaddress
from functools import lru_cache
from typing import Iterable, List, Optional, Sequence, Tuple

from starlette.requests import Request

from app.core.config import settings

#: Header carrying the forwarded chain, most-distant client first.
FORWARDED_FOR_HEADER = "x-forwarded-for"

#: Single-value header some proxies send instead. Only consulted when
#: ``X-Forwarded-For`` is absent, since it carries no chain.
REAL_IP_HEADER = "x-real-ip"

#: What to report when there is no peer address at all. This happens under
#: TestClient and for lifespan-scoped calls. A constant beats ``None`` here:
#: every caller keys on the result, and ``None`` keys collapse together in
#: exactly the way this module exists to prevent.
UNKNOWN_ADDRESS = "unknown"


def _parse_networks(values: Iterable[str]) -> Tuple[ipaddress._BaseNetwork, ...]:
    """
    Parse CIDR strings, skipping anything unparseable.

    A malformed entry is dropped rather than raising. This is read at import
    time from configuration, and taking the whole application down because
    somebody fat-fingered an environment variable is a worse outcome than
    running with one fewer trusted proxy -- which fails closed, since an
    untrusted proxy means the header is ignored.
    """
    networks: List[ipaddress._BaseNetwork] = []

    for value in values:
        entry = value.strip()
        if not entry:
            continue
        try:
            # strict=False so a host address ("10.0.0.7") is accepted as the
            # /32 or /128 it implies, which is how people write single proxies.
            networks.append(ipaddress.ip_network(entry, strict=False))
        except ValueError:
            continue

    return tuple(networks)


@lru_cache(maxsize=1)
def trusted_networks() -> Tuple[ipaddress._BaseNetwork, ...]:
    """The configured trusted-proxy networks, parsed once."""
    return _parse_networks(settings.trusted_proxy_cidr_list)


def _as_ip(value: str) -> Optional[ipaddress._BaseAddress]:
    """
    Parse an address from a forwarded-chain entry.

    Handles the shapes that turn up in the wild: a bare address, an IPv6
    literal in brackets, and either with a port appended. Returns ``None`` for
    anything else, including the obfuscated identifiers RFC 7239 permits
    (``_hidden``) and the literal ``unknown``.
    """
    entry = value.strip()
    if not entry:
        return None

    # "[::1]:8080" or "[::1]"
    if entry.startswith("["):
        closing = entry.find("]")
        if closing == -1:
            return None
        entry = entry[1:closing]
    elif entry.count(":") == 1:
        # "1.2.3.4:5678" -- exactly one colon means IPv4 with a port. A bare
        # IPv6 address has several, and must not be split here.
        entry = entry.split(":", 1)[0]

    try:
        return ipaddress.ip_address(entry)
    except ValueError:
        return None


def is_trusted_proxy(address: str) -> bool:
    """Whether ``address`` is one of our configured proxies."""
    parsed = _as_ip(address)
    if parsed is None:
        return False

    return any(parsed in network for network in trusted_networks())


def _forwarded_chain(header_value: str) -> List[str]:
    """The addresses in an ``X-Forwarded-For`` value, left to right."""
    return [part.strip() for part in header_value.split(",") if part.strip()]


def resolve_client_address(
    peer: Optional[str],
    forwarded_for: Optional[str] = None,
    real_ip: Optional[str] = None,
) -> str:
    """
    The address to attribute a request to.

    ``peer`` is the socket address (``request.client.host``). The other two
    are the raw header values, or ``None`` when absent.

    Pure, so the trust logic can be tested without building a request.
    """
    if not peer:
        return UNKNOWN_ADDRESS

    # The header is only evidence if it came through a proxy we control.
    if not is_trusted_proxy(peer):
        return peer

    if forwarded_for:
        chain = _forwarded_chain(forwarded_for)

        # Right to left: skip hops that are our own proxies, and stop at the
        # first that is not. Everything further left is client-supplied and
        # unverifiable.
        for entry in reversed(chain):
            parsed = _as_ip(entry)
            if parsed is None:
                # Unparseable or obfuscated. It is not a proxy we can vouch
                # for, so we cannot keep walking past it either -- doing so
                # would let a client hide a real hop behind junk.
                break
            if is_trusted_proxy(str(parsed)):
                continue
            return str(parsed)

        # Every hop in the chain was one of ours. The request originated
        # inside the perimeter; the nearest proxy is the best answer.
        return peer

    if real_ip:
        parsed = _as_ip(real_ip)
        if parsed is not None:
            return str(parsed)

    return peer


def client_address(request: Request) -> str:
    """:func:`resolve_client_address` for a Starlette request."""
    return resolve_client_address(
        peer=request.client.host if request.client else None,
        forwarded_for=request.headers.get(FORWARDED_FOR_HEADER),
        real_ip=request.headers.get(REAL_IP_HEADER),
    )


def rate_limit_key(request: Request) -> str:
    """
    The bucket a request counts against.

    Authenticated requests are keyed by user id, anonymous ones by client
    address. Address-only keying puts everybody behind one NAT egress -- an
    office, a university, a mobile carrier -- into a single bucket, so one
    heavy user there throttles the rest. A user id is both more precise and
    harder to rotate than an address.

    The token is read directly rather than through the auth dependency:
    SlowAPI calls this before dependency resolution, and a request that fails
    authentication still has to be counted against *something*, which is what
    the address fallback is for.
    """
    auth_header = request.headers.get("authorization", "")

    if auth_header.startswith("Bearer "):
        from app.core.security import decode_token

        try:
            payload = decode_token(auth_header[7:])
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except ValueError:
            # Expired, forged, or not a JWT at all. Falls through to the
            # address, which is what should be counted anyway -- otherwise
            # sending junk credentials would be a way to dodge the limit.
            pass

    return f"ip:{client_address(request)}"


def reset_caches() -> None:
    """Clear the parsed-configuration cache. For tests that change settings."""
    trusted_networks.cache_clear()


__all__ = [
    "UNKNOWN_ADDRESS",
    "client_address",
    "is_trusted_proxy",
    "rate_limit_key",
    "reset_caches",
    "resolve_client_address",
    "trusted_networks",
]
