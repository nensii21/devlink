from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.webhook_delivery_paginated_response import (
    WebhookDeliveryPaginatedResponse,
)
from ...models.webhook_delivery_status import WebhookDeliveryStatus
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = 1,
    limit: int | Unset = 20,
    status: None | Unset | WebhookDeliveryStatus = UNSET,
    event_type: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, WebhookDeliveryStatus):
        json_status = status.value
    else:
        json_status = status
    params["status"] = json_status

    json_event_type: None | str | Unset
    if isinstance(event_type, Unset):
        json_event_type = UNSET
    else:
        json_event_type = event_type
    params["event_type"] = json_event_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/webhooks/deliveries",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | WebhookDeliveryPaginatedResponse | None:
    if response.status_code == 200:
        response_200 = WebhookDeliveryPaginatedResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | WebhookDeliveryPaginatedResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    limit: int | Unset = 20,
    status: None | Unset | WebhookDeliveryStatus = UNSET,
    event_type: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | WebhookDeliveryPaginatedResponse]:
    """List webhook deliveries with status filters and pagination

     List webhook delivery history.

    Args:
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 20.
        status (None | Unset | WebhookDeliveryStatus): Filter by status e.g. pending, delivered,
            failed, exhausted
        event_type (None | str | Unset): Filter by event type

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WebhookDeliveryPaginatedResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        status=status,
        event_type=event_type,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    limit: int | Unset = 20,
    status: None | Unset | WebhookDeliveryStatus = UNSET,
    event_type: None | str | Unset = UNSET,
) -> HTTPValidationError | WebhookDeliveryPaginatedResponse | None:
    """List webhook deliveries with status filters and pagination

     List webhook delivery history.

    Args:
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 20.
        status (None | Unset | WebhookDeliveryStatus): Filter by status e.g. pending, delivered,
            failed, exhausted
        event_type (None | str | Unset): Filter by event type

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WebhookDeliveryPaginatedResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        status=status,
        event_type=event_type,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    limit: int | Unset = 20,
    status: None | Unset | WebhookDeliveryStatus = UNSET,
    event_type: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | WebhookDeliveryPaginatedResponse]:
    """List webhook deliveries with status filters and pagination

     List webhook delivery history.

    Args:
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 20.
        status (None | Unset | WebhookDeliveryStatus): Filter by status e.g. pending, delivered,
            failed, exhausted
        event_type (None | str | Unset): Filter by event type

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WebhookDeliveryPaginatedResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        status=status,
        event_type=event_type,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    limit: int | Unset = 20,
    status: None | Unset | WebhookDeliveryStatus = UNSET,
    event_type: None | str | Unset = UNSET,
) -> HTTPValidationError | WebhookDeliveryPaginatedResponse | None:
    """List webhook deliveries with status filters and pagination

     List webhook delivery history.

    Args:
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 20.
        status (None | Unset | WebhookDeliveryStatus): Filter by status e.g. pending, delivered,
            failed, exhausted
        event_type (None | str | Unset): Filter by event type

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WebhookDeliveryPaginatedResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            status=status,
            event_type=event_type,
        )
    ).parsed
