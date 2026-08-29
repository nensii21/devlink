from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_presences_api_v1_ws_presence_get_response_get_all_presences_api_v1_ws_presence_get import (
    GetAllPresencesApiV1WsPresenceGetResponseGetAllPresencesApiV1WsPresenceGet,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/ws/presence",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetAllPresencesApiV1WsPresenceGetResponseGetAllPresencesApiV1WsPresenceGet | None:
    if response.status_code == 200:
        response_200 = GetAllPresencesApiV1WsPresenceGetResponseGetAllPresencesApiV1WsPresenceGet.from_dict(
            response.json()
        )

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllPresencesApiV1WsPresenceGetResponseGetAllPresencesApiV1WsPresenceGet
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[
    GetAllPresencesApiV1WsPresenceGetResponseGetAllPresencesApiV1WsPresenceGet
]:
    """Get All Presences

     Retrieve active presence states for all connected users.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAllPresencesApiV1WsPresenceGetResponseGetAllPresencesApiV1WsPresenceGet]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> GetAllPresencesApiV1WsPresenceGetResponseGetAllPresencesApiV1WsPresenceGet | None:
    """Get All Presences

     Retrieve active presence states for all connected users.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAllPresencesApiV1WsPresenceGetResponseGetAllPresencesApiV1WsPresenceGet
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[
    GetAllPresencesApiV1WsPresenceGetResponseGetAllPresencesApiV1WsPresenceGet
]:
    """Get All Presences

     Retrieve active presence states for all connected users.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAllPresencesApiV1WsPresenceGetResponseGetAllPresencesApiV1WsPresenceGet]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> GetAllPresencesApiV1WsPresenceGetResponseGetAllPresencesApiV1WsPresenceGet | None:
    """Get All Presences

     Retrieve active presence states for all connected users.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAllPresencesApiV1WsPresenceGetResponseGetAllPresencesApiV1WsPresenceGet
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
