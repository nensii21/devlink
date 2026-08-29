from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.bookmark_collection_response import BookmarkCollectionResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    bookmark_id: UUID,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/bookmark-collections/bookmark/{bookmark_id}/collections".format(
            bookmark_id=quote(str(bookmark_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[BookmarkCollectionResponse] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = BookmarkCollectionResponse.from_dict(
                response_200_item_data
            )

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | list[BookmarkCollectionResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    bookmark_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | list[BookmarkCollectionResponse]]:
    """Get Bookmark Collections

    Args:
        bookmark_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[BookmarkCollectionResponse]]
    """

    kwargs = _get_kwargs(
        bookmark_id=bookmark_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    bookmark_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | list[BookmarkCollectionResponse] | None:
    """Get Bookmark Collections

    Args:
        bookmark_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[BookmarkCollectionResponse]
    """

    return sync_detailed(
        bookmark_id=bookmark_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    bookmark_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | list[BookmarkCollectionResponse]]:
    """Get Bookmark Collections

    Args:
        bookmark_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[BookmarkCollectionResponse]]
    """

    kwargs = _get_kwargs(
        bookmark_id=bookmark_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    bookmark_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | list[BookmarkCollectionResponse] | None:
    """Get Bookmark Collections

    Args:
        bookmark_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[BookmarkCollectionResponse]
    """

    return (
        await asyncio_detailed(
            bookmark_id=bookmark_id,
            client=client,
        )
    ).parsed
