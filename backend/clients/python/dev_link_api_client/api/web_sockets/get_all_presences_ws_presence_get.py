from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_presences_ws_presence_get_response_get_all_presences_ws_presence_get import (
    GetAllPresencesWsPresenceGetResponseGetAllPresencesWsPresenceGet,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/ws/presence",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetAllPresencesWsPresenceGetResponseGetAllPresencesWsPresenceGet | None:
    if response.status_code == 200:
        response_200 = (
            GetAllPresencesWsPresenceGetResponseGetAllPresencesWsPresenceGet.from_dict(
                response.json()
            )
        )

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetAllPresencesWsPresenceGetResponseGetAllPresencesWsPresenceGet]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[GetAllPresencesWsPresenceGetResponseGetAllPresencesWsPresenceGet]:
    """Get All Presences

     Retrieve active presence states for all connected users.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAllPresencesWsPresenceGetResponseGetAllPresencesWsPresenceGet]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> GetAllPresencesWsPresenceGetResponseGetAllPresencesWsPresenceGet | None:
    """Get All Presences

     Retrieve active presence states for all connected users.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAllPresencesWsPresenceGetResponseGetAllPresencesWsPresenceGet
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[GetAllPresencesWsPresenceGetResponseGetAllPresencesWsPresenceGet]:
    """Get All Presences

     Retrieve active presence states for all connected users.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAllPresencesWsPresenceGetResponseGetAllPresencesWsPresenceGet]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> GetAllPresencesWsPresenceGetResponseGetAllPresencesWsPresenceGet | None:
    """Get All Presences

     Retrieve active presence states for all connected users.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAllPresencesWsPresenceGetResponseGetAllPresencesWsPresenceGet
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
