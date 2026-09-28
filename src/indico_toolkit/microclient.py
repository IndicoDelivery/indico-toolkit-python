"""
Async micro client for Indico Intake & Insights.

Handles authentication, retry, and API boilerplate for GraphQL, REST, and Storage URIs.

Install dependencies with your Python package manager:
E.g. `pip install httpx tenacity`

Usage:
```
async with MicroClient(host, token) as client:
    json = await client.graphql(query, variables, files)
    json = await client.rest(method, path, query, body, files)
    bytes = await client.storage(uri)
```
"""

import asyncio
import json
import re
from base64 import b64encode
from collections.abc import AsyncGenerator, Callable, Iterable, Mapping
from types import SimpleNamespace
from typing import IO, Any, Concatenate, ParamSpec, Self, TypeVar

import httpx
import tenacity

__all__ = ("MicroClient",)


OldSelf = TypeVar("OldSelf")
NewSelf = TypeVar("NewSelf")
MimicParams = ParamSpec("MimicParams")
MimicReturns = TypeVar("MimicReturns")


def mimicmethod(
    method: Callable[Concatenate[OldSelf, MimicParams], MimicReturns],
) -> Callable[
    [Callable[Concatenate[NewSelf, ...], MimicReturns]],
    Callable[Concatenate[NewSelf, MimicParams], MimicReturns],
]:
    """
    Rewrite the call signature of one class's method to look like another's.
    This allows a wrapper that passes all arguments through `*args, **kwargs`
    to automatically mimic all arguments for the purposes of type checking.
    """

    def decorator(
        mimic: Callable[Concatenate[NewSelf, ...], MimicReturns],
    ) -> Callable[Concatenate[NewSelf, MimicParams], MimicReturns]:
        return mimic

    return decorator


def make_namespace(json_object_dict: dict[str, Any]) -> SimpleNamespace:
    """
    Convert a JSON object dictionary to a SimpleNamespace.
    """
    return SimpleNamespace(**json_object_dict)


class MicroClientAuth(httpx.Auth):
    def __init__(self, refresh_url: str, refresh_token: str):
        self._refresh_url = refresh_url
        self._refresh_token = refresh_token
        self._access_token = ""
        self._access_token_lock = asyncio.Lock()

    @property
    def _auth_request(self) -> httpx.Request:
        username = ""
        password = self._refresh_token.strip()
        basic_token = b64encode(f"{username}:{password}".encode()).decode()
        return httpx.Request(
            method="POST",
            url=self._refresh_url,
            headers={"Authorization": f"Basic {basic_token}"},
            data={"grant_type": "client_credentials"},
        )

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        async with self._access_token_lock:
            # Pre-flight authentication when unauthenticated
            if not self._access_token:
                response = yield self._auth_request
                response.raise_for_status()
                await response.aread()
                self._access_token = response.json()["access_token"]

            request_token = self._access_token
            request.headers["Authorization"] = f"Bearer {self._access_token}"

        # Send actual request
        response = yield request

        if response.status_code == httpx.codes.UNAUTHORIZED:
            async with self._access_token_lock:
                # Post-flight reauthentication when expired
                if self._access_token == request_token:
                    response = yield self._auth_request
                    response.raise_for_status()
                    await response.aread()
                    self._access_token = response.json()["access_token"]

                request.headers["Authorization"] = f"Bearer {self._access_token}"

            # Resend actual request
            yield request


class MicroClient:
    def __init__(
        self,
        host: str,
        token: str,
        *,
        is_insights_host: bool | None = None,
        is_bearer_token: bool = False,
    ):
        self._insights = (
            ("insights" in host.casefold())
            if is_insights_host is None
            else is_insights_host
        )
        self._client = httpx.AsyncClient(
            auth=(
                None
                if is_bearer_token
                else MicroClientAuth(
                    refresh_url=(
                        f"https://{host}/restapi/api/v1/auth/access-token"
                        if self._insights
                        else f"https://{host}/restapi/api/v1/auth/refreshToken"
                    ),
                    refresh_token=token,
                )
            ),
            base_url=f"https://{host}",
            headers=({"Authorization": f"Bearer {token}"} if is_bearer_token else None),
            timeout=httpx.Timeout(
                connect=4,
                read=64,
                write=64,
                pool=None,
            ),
        )
        self._retry = tenacity.AsyncRetrying(
            reraise=True,
            retry=tenacity.retry_if_exception_type(httpx.RequestError),
            stop=tenacity.stop_after_attempt(4),
            wait=tenacity.wait_exponential_jitter(
                initial=4,
                exp_base=4,
                jitter=4,
            ),
        )

    async def __aenter__(self) -> Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.__aexit__(*args)

    async def close(self) -> None:
        await self._client.aclose()

    @mimicmethod(httpx.AsyncClient.request)
    async def request(self, *args: Any, **kwargs: Any) -> httpx.Response:
        return await self._retry(self._client.request, *args, **kwargs)

    @mimicmethod(httpx.AsyncClient.stream)
    def stream(self, *args: Any, **kwargs: Any) -> Any:
        return self._client.stream(*args, **kwargs)

    async def graphql(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
        files: Mapping[str, tuple[str, bytes | IO[bytes]]] | None = None,
    ) -> Any:
        if not files:
            response = await self.request(
                method="POST",
                url=("/graphql" if self._insights else "/graph/api/graphql"),
                json={"query": query, "variables": variables},
            )
        else:
            files = dict(files)
            file_map = {str(i): [f"variables.{name}"] for i, name in enumerate(files)}
            files = {str(i): file for i, file in enumerate(files.values())}
            response = await self.request(
                method="POST",
                url=("/graphql" if self._insights else "/graph/api/graphql"),
                data={
                    "operations": json.dumps({"query": query, "variables": variables}),
                    "map": json.dumps(file_map),
                },
                files=files,
            )

        response.raise_for_status()
        response_json = response.json(object_hook=make_namespace)

        if hasattr(response_json, "errors"):
            raise RuntimeError(
                "GraphQL Errors: "
                + "; ".join(error.message for error in response_json.errors)
            )

        return response_json.data

    async def subscription(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
    ) -> Any:
        async with self.stream(
            method="POST",
            url="/graphql",
            headers={"Accept": "multipart/mixed; subscriptionSpec=1.0"},
            json={"query": query, "variables": variables},
            # Disable read timeout for quiet GraphQL subscriptions.
            timeout=httpx.Timeout(**{**self._client.timeout.as_dict(), "read": None}),
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("{") and not line.startswith("{}"):
                    response_json = json.loads(line, object_hook=make_namespace).payload

                    if hasattr(response_json, "errors"):
                        raise RuntimeError(
                            "GraphQL Errors: "
                            + "; ".join(error.message for error in response_json.errors)
                        )

                    yield response_json.data

    async def rest(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        files: Iterable[tuple[str, bytes | IO[bytes]]] | None = None,
    ) -> Any:
        path = path.lstrip("/")
        response = await self.request(
            method=method,
            url=f"/restapi/api/v1/{path}",
            params=query,
            json=body,
            files=[("files", file) for file in files] if files else None,
        )
        response.raise_for_status()
        return response.json(object_hook=make_namespace)

    async def storage(self, uri: str) -> bytes:
        if match := re.search(r"(?:^|/)(?:storage|blob|data)/+(.+)", uri):
            path = match.group(1)
        else:
            raise RuntimeError(f"Unsupported Storage URI: {uri!r}")

        response = await self.request(
            method="GET",
            url=f"/storage/{path}",
        )
        response.raise_for_status()
        return response.content
