from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.verification_request_response import VerificationRequestResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    status_filter: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_status_filter: None | str | Unset
    if isinstance(status_filter, Unset):
        json_status_filter = UNSET
    else:
        json_status_filter = status_filter
    params["status_filter"] = json_status_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/admin/verification/requests",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[VerificationRequestResponse] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = VerificationRequestResponse.from_dict(
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
) -> Response[HTTPValidationError | list[VerificationRequestResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    status_filter: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | list[VerificationRequestResponse]]:
    """List all verification requests

    Args:
        status_filter (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[VerificationRequestResponse]]
    """

    kwargs = _get_kwargs(
        status_filter=status_filter,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    status_filter: None | str | Unset = UNSET,
) -> HTTPValidationError | list[VerificationRequestResponse] | None:
    """List all verification requests

    Args:
        status_filter (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[VerificationRequestResponse]
    """

    return sync_detailed(
        client=client,
        status_filter=status_filter,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    status_filter: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | list[VerificationRequestResponse]]:
    """List all verification requests

    Args:
        status_filter (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[VerificationRequestResponse]]
    """

    kwargs = _get_kwargs(
        status_filter=status_filter,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    status_filter: None | str | Unset = UNSET,
) -> HTTPValidationError | list[VerificationRequestResponse] | None:
    """List all verification requests

    Args:
        status_filter (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[VerificationRequestResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            status_filter=status_filter,
        )
    ).parsed
