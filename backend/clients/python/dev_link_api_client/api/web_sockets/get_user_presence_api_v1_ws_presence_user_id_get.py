from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_user_presence_api_v1_ws_presence_user_id_get_response_get_user_presence_api_v1_ws_presence_user_id_get import (
    GetUserPresenceApiV1WsPresenceUserIdGetResponseGetUserPresenceApiV1WsPresenceUserIdGet,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    user_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/ws/presence/{user_id}".format(
            user_id=quote(str(user_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetUserPresenceApiV1WsPresenceUserIdGetResponseGetUserPresenceApiV1WsPresenceUserIdGet
    | HTTPValidationError
    | None
):
    if response.status_code == 200:
        response_200 = GetUserPresenceApiV1WsPresenceUserIdGetResponseGetUserPresenceApiV1WsPresenceUserIdGet.from_dict(
            response.json()
        )

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
) -> Response[
    GetUserPresenceApiV1WsPresenceUserIdGetResponseGetUserPresenceApiV1WsPresenceUserIdGet
    | HTTPValidationError
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    user_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[
    GetUserPresenceApiV1WsPresenceUserIdGetResponseGetUserPresenceApiV1WsPresenceUserIdGet
    | HTTPValidationError
]:
    """Get User Presence

     Retrieve presence status of a specific user.

    Args:
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetUserPresenceApiV1WsPresenceUserIdGetResponseGetUserPresenceApiV1WsPresenceUserIdGet | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    user_id: str,
    *,
    client: AuthenticatedClient,
) -> (
    GetUserPresenceApiV1WsPresenceUserIdGetResponseGetUserPresenceApiV1WsPresenceUserIdGet
    | HTTPValidationError
    | None
):
    """Get User Presence

     Retrieve presence status of a specific user.

    Args:
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetUserPresenceApiV1WsPresenceUserIdGetResponseGetUserPresenceApiV1WsPresenceUserIdGet | HTTPValidationError
    """

    return sync_detailed(
        user_id=user_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    user_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[
    GetUserPresenceApiV1WsPresenceUserIdGetResponseGetUserPresenceApiV1WsPresenceUserIdGet
    | HTTPValidationError
]:
    """Get User Presence

     Retrieve presence status of a specific user.

    Args:
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetUserPresenceApiV1WsPresenceUserIdGetResponseGetUserPresenceApiV1WsPresenceUserIdGet | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    user_id: str,
    *,
    client: AuthenticatedClient,
) -> (
    GetUserPresenceApiV1WsPresenceUserIdGetResponseGetUserPresenceApiV1WsPresenceUserIdGet
    | HTTPValidationError
    | None
):
    """Get User Presence

     Retrieve presence status of a specific user.

    Args:
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetUserPresenceApiV1WsPresenceUserIdGetResponseGetUserPresenceApiV1WsPresenceUserIdGet | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            user_id=user_id,
            client=client,
        )
    ).parsed
