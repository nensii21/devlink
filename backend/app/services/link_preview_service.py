"""
Turning a pasted URL into a preview card.

The metadata side of this is simple: read Open Graph tags, fall back to Twitter
card tags, fall back to the plain ``<title>``. The part that needs care is
everything around it, because fetching a URL chosen by a user means the caller
is steering our outbound HTTP client.

The rules this module enforces on every fetch:

* the destination is validated before we connect (see ``utils.url_safety``),
  and re-validated at every redirect hop -- following redirects automatically
  would let a public URL bounce us to ``169.254.169.254``
* the connection is pinned to the address that validation approved, so DNS
  cannot answer differently between the check and the connect
* the body is streamed and abandoned once it exceeds a byte cap, so a hostile
  server cannot make us buffer a gigabyte
* only HTML content types are parsed
* connect and read timeouts are short, and the hop count is bounded

Results are cached, negative results too, because a link pasted into a busy
conversation is otherwise fetched once per reader.
"""

from __future__ import annotations

import html
import logging
import re
from dataclasses import asdict, dataclass
from typing import Optional
from urllib.parse import urljoin

import httpx

from app.core.cache import cache_manager
from app.core.config import settings
from app.utils.url_safety import (
    SafeTarget,
    UnsafeURL,
    normalise_url,
    pin_target,
    validate_outbound_url,
)

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "linkpreview:"
_FAILURE_SENTINEL = {"__failed__": True}

# Matches a <meta> tag and captures the whole attribute blob, which is then
# picked apart separately. Doing it in one regex with fixed attribute order
# fails on the very common `content="..." property="..."` spelling.
_META_TAG = re.compile(r"<meta\b([^>]*)>", re.IGNORECASE)
_ATTRIBUTE = re.compile(
    r"""(\w[\w:.-]*)\s*=\s*("([^"]*)"|'([^']*)'|([^\s"'>]+))""",
    re.IGNORECASE | re.VERBOSE,
)
_TITLE_TAG = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

# Anything past these lengths is decoration. Truncating here keeps the cache
# entries small and stops a hostile page pushing megabytes into our responses.
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 500
MAX_SITE_NAME_LENGTH = 100

HTML_CONTENT_TYPES = ("text/html", "application/xhtml+xml")


@dataclass(frozen=True)
class LinkPreview:
    """What we managed to learn about a URL."""

    url: str
    final_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    site_name: Optional[str] = None
    image_url: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)


class LinkPreviewService:
    """
    Fetch and parse link metadata.

    Stateless apart from the shared cache; a module-level singleton is provided
    at the bottom of the file.
    """

    def __init__(
        self,
        timeout: Optional[float] = None,
        max_bytes: Optional[int] = None,
        max_redirects: Optional[int] = None,
    ) -> None:
        self.timeout = (
            timeout if timeout is not None else settings.LINK_PREVIEW_TIMEOUT_SECONDS
        )
        self.max_bytes = (
            max_bytes if max_bytes is not None else settings.LINK_PREVIEW_MAX_BYTES
        )
        self.max_redirects = (
            max_redirects
            if max_redirects is not None
            else settings.LINK_PREVIEW_MAX_REDIRECTS
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def preview(self, url: str, *, use_cache: bool = True) -> Optional[LinkPreview]:
        """
        Metadata for a URL, or ``None`` if it could not be previewed.

        Raises :class:`UnsafeURL` when the URL is one we refuse to fetch --
        that is a client error worth reporting, unlike a timeout, which is
        just an absent preview.
        """
        target = validate_outbound_url(url)

        cache_key = _CACHE_PREFIX + normalise_url(target.url)

        if use_cache:
            cached = cache_manager.get(cache_key)
            if cached == _FAILURE_SENTINEL:
                return None
            if cached is not None:
                return LinkPreview(**cached)

        fetched = self._fetch_html(target)
        if fetched is None:
            cache_manager.set(
                cache_key,
                _FAILURE_SENTINEL,
                ttl=settings.LINK_PREVIEW_FAILURE_CACHE_TTL_SECONDS,
            )
            return None

        body, final_url = fetched
        preview = self._parse(body, requested_url=url, final_url=final_url)

        cache_manager.set(
            cache_key,
            preview.as_dict(),
            ttl=settings.LINK_PREVIEW_CACHE_TTL_SECONDS,
        )
        return preview

    def preview_many(self, urls: list[str]) -> dict[str, Optional[LinkPreview]]:
        """
        Preview several URLs, keyed by the URL as it was given to us.

        One bad link does not fail the batch: an unsafe or unreachable URL maps
        to ``None`` and the rest are still returned.
        """
        results: dict[str, Optional[LinkPreview]] = {}

        for url in urls:
            if url in results:
                continue
            try:
                results[url] = self.preview(url)
            except UnsafeURL:
                results[url] = None

        return results

    # ------------------------------------------------------------------
    # Fetching
    # ------------------------------------------------------------------

    def _fetch_html(self, target: SafeTarget) -> Optional[tuple[str, str]]:
        """
        Fetch a validated target and return ``(body, final_url)``, or ``None``.

        Two things happen by hand here rather than being left to ``httpx``:

        * **Redirects.** Every hop goes back through
          :func:`validate_outbound_url`. ``httpx``'s own redirect following
          would happily walk us onto the metadata service.
        * **Address resolution.** Each hop connects to the address that hop's
          validation actually approved, via :func:`pin_target`. Handing the
          hostname to ``httpx`` would let it resolve a second time, and a
          short-TTL record that answers public-then-private turns the whole
          guard into decoration.

        ``final_url`` is the logical URL, not the pinned one -- the IP is a
        transport detail and has no business ending up in a preview card.
        """
        current_target = target
        current_url = target.url

        try:
            with httpx.Client(
                timeout=self.timeout,
                follow_redirects=False,
                headers={
                    "User-Agent": settings.LINK_PREVIEW_USER_AGENT,
                    # Some sites serve a stripped page to clients that do not
                    # ask for HTML.
                    "Accept": "text/html,application/xhtml+xml",
                },
            ) as client:
                for _ in range(self.max_redirects + 1):
                    pinned = pin_target(current_target)

                    with client.stream(
                        "GET",
                        pinned.url,
                        headers=pinned.headers,
                        extensions=pinned.extensions,
                    ) as response:
                        if response.is_redirect:
                            location = response.headers.get("location")
                            if not location:
                                return None

                            # Relative redirects are legal and common, and must
                            # resolve against the logical URL rather than the
                            # pinned one, or they would inherit the IP.
                            current_url = urljoin(current_url, location)

                            # The whole point of doing this by hand: re-check
                            # and re-pin, so hop two cannot be 169.254.169.254.
                            current_target = validate_outbound_url(current_url)
                            continue

                        if response.status_code >= 400:
                            return None

                        content_type = response.headers.get("content-type", "")
                        if not any(
                            content_type.lower().startswith(t)
                            for t in HTML_CONTENT_TYPES
                        ):
                            return None

                        body = self._read_capped(response)
                        return body, current_url

        except UnsafeURL:
            # A redirect walked somewhere we will not follow. Treat it as an
            # absent preview rather than an error: the user pasted a URL that
            # was fine, and what happened after that is not their fault.
            logger.info("Link preview redirect rejected for %s", target.url)
            return None
        except httpx.HTTPError as exc:
            logger.info("Link preview fetch failed for %s: %s", target.url, exc)
            return None
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Unexpected link preview error for %s: %s", target.url, exc)
            return None

        # Ran out of redirect budget.
        return None

    def _read_capped(self, response: httpx.Response) -> str:
        """
        Read at most ``max_bytes`` of a streaming response.

        The metadata we want lives in ``<head>``, so the cap costs us nothing
        on a well-formed page and protects us from a server that streams
        forever. Decoding is lenient because plenty of real pages declare one
        encoding and serve another.
        """
        chunks: list[bytes] = []
        total = 0

        for chunk in response.iter_bytes():
            chunks.append(chunk)
            total += len(chunk)
            if total >= self.max_bytes:
                break

        raw = b"".join(chunks)[: self.max_bytes]
        return raw.decode(response.encoding or "utf-8", errors="replace")

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse(self, body: str, *, requested_url: str, final_url: str) -> LinkPreview:
        """Pull metadata out of an HTML document."""
        meta = self._collect_meta(body)

        title = (
            meta.get("og:title")
            or meta.get("twitter:title")
            or self._document_title(body)
        )
        description = (
            meta.get("og:description")
            or meta.get("twitter:description")
            or meta.get("description")
        )
        site_name = meta.get("og:site_name") or meta.get("application-name")
        image = meta.get("og:image") or meta.get("twitter:image")

        # og:url is the page's own canonical spelling of itself, which is a
        # better thing to link to than whatever redirect chain we followed.
        canonical = meta.get("og:url") or final_url

        return LinkPreview(
            url=requested_url,
            final_url=canonical,
            title=_clean(title, MAX_TITLE_LENGTH),
            description=_clean(description, MAX_DESCRIPTION_LENGTH),
            site_name=_clean(site_name, MAX_SITE_NAME_LENGTH),
            # Relative image paths resolve against the page we actually landed
            # on, not against the URL that was originally submitted.
            image_url=urljoin(final_url, image) if image else None,
        )

    @staticmethod
    def _collect_meta(body: str) -> dict[str, str]:
        """
        Every ``<meta>`` tag, keyed by ``property`` or ``name``.

        The first occurrence of a key wins, which matches how browsers and
        crawlers treat duplicate Open Graph tags.
        """
        found: dict[str, str] = {}

        for match in _META_TAG.finditer(body):
            attributes = {}
            for attr in _ATTRIBUTE.finditer(match.group(1)):
                value = attr.group(3) or attr.group(4) or attr.group(5) or ""
                attributes[attr.group(1).lower()] = value

            key = attributes.get("property") or attributes.get("name")
            content = attributes.get("content")

            if not key or content is None:
                continue

            found.setdefault(key.lower(), content)

        return found

    @staticmethod
    def _document_title(body: str) -> Optional[str]:
        match = _TITLE_TAG.search(body)
        return match.group(1) if match else None


def _clean(value: Optional[str], max_length: int) -> Optional[str]:
    """
    Normalise a scrap of text pulled out of a page.

    Entities are decoded (``&amp;`` really is meant to be ``&``), whitespace is
    collapsed because these tags are frequently pretty-printed across lines,
    and the result is truncated on a word boundary where one is nearby.
    """
    if value is None:
        return None

    text = html.unescape(value)
    text = " ".join(text.split())

    if not text:
        return None

    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    last_space = truncated.rfind(" ")

    # Only back up to a word boundary if it is close to the end; otherwise a
    # long unbroken token would shrink the text dramatically.
    if last_space > max_length * 0.8:
        truncated = truncated[:last_space]

    return truncated.rstrip() + "…"


link_preview_service = LinkPreviewService()
