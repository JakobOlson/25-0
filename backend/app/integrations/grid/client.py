from __future__ import annotations

import os
import time
from typing import Any

import httpx
from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv(usecwd=True))


DEFAULT_CENTRAL_DATA_URL = (
    "https://api-op.grid.gg/central-data/graphql"
)

DEFAULT_SERIES_STATE_URL = (
    "https://api-op.grid.gg/"
    "live-data-feed/series-state/graphql"
)

DEFAULT_STATS_FEED_URL = (
    "https://api-op.grid.gg/statistics-feed/graphql"
)


class GridClientError(RuntimeError):
    """
    Base exception for GRID client errors.
    """


class GridConfigurationError(GridClientError):
    """
    Raised when required GRID configuration is missing.
    """


class GridRequestError(GridClientError):
    """
    Raised when an HTTP request to GRID fails.
    """


class GridGraphQLError(GridClientError):
    """
    Raised when GRID returns GraphQL errors.
    """

    def __init__(
        self,
        errors: list[dict[str, Any]],
    ) -> None:
        self.errors = errors

        messages = []

        for error in errors:
            message = error.get(
                "message",
                "Unknown GraphQL error",
            )

            messages.append(str(message))

        combined_message = "; ".join(messages)

        super().__init__(
            f"GRID returned GraphQL errors: "
            f"{combined_message}"
        )


class GridClient:
    """
    Client for GRID Open Access GraphQL APIs.
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout_seconds: float = 30.0,
        minimum_request_interval: float = 3.2,
        maximum_retries: int = 5,
        rate_limit_wait_seconds: float = 61.0,
    ) -> None:
        loaded_api_key = (
            api_key
            or os.getenv("GRID_API_KEY", "")
        ).strip()

        if not loaded_api_key:
            raise GridConfigurationError(
                "GRID_API_KEY is missing. Add it to "
                "your .env file."
            )

        self.api_key = loaded_api_key

        self.endpoints = {
            "central": os.getenv(
                "GRID_CENTRAL_DATA_URL",
                DEFAULT_CENTRAL_DATA_URL,
            ).strip(),

            "series_state": os.getenv(
                "GRID_SERIES_STATE_URL",
                DEFAULT_SERIES_STATE_URL,
            ).strip(),

            "stats": os.getenv(
                "GRID_STATS_FEED_URL",
                DEFAULT_STATS_FEED_URL,
            ).strip(),
        }

        self.minimum_request_interval = (
            minimum_request_interval
        )

        self.maximum_retries = maximum_retries

        self.rate_limit_wait_seconds = (
            rate_limit_wait_seconds
        )

        self._last_request_time: float | None = None

        timeout = httpx.Timeout(
            timeout_seconds,
            connect=10.0,
        )

        self._http_client = httpx.Client(
            headers={
                "x-api-key": self.api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "25-0-CS-Draft/0.1",
            },
            timeout=timeout,
            follow_redirects=True,
        )

    def close(self) -> None:
        self._http_client.close()

    def __enter__(self) -> GridClient:
        return self

    def __exit__(
        self,
        exception_type: object,
        exception_value: object,
        traceback: object,
    ) -> None:
        self.close()

    def _wait_for_request_slot(self) -> None:
        """
        Keep requests safely below GRID's Open Platform
        rate limit.
        """

        if self._last_request_time is None:
            return

        elapsed = (
            time.monotonic()
            - self._last_request_time
        )

        remaining_wait = (
            self.minimum_request_interval
            - elapsed
        )

        if remaining_wait > 0:
            time.sleep(remaining_wait)

    def _record_request_time(self) -> None:
        self._last_request_time = time.monotonic()

    @staticmethod
    def _contains_rate_limit_error(
        errors: Any,
    ) -> bool:
        """
        Inspect GraphQL errors for a rate-limit message.
        """

        if not isinstance(errors, list):
            return False

        for error in errors:
            if isinstance(error, dict):
                message = str(
                    error.get("message", "")
                ).lower()
            else:
                message = str(error).lower()

            if (
                "rate limit" in message
                or "too many requests" in message
            ):
                return True

        return False

    def _get_retry_wait(
        self,
        response: httpx.Response,
    ) -> float:
        """
        Use GRID's Retry-After header when provided.
        """

        retry_after = response.headers.get(
            "Retry-After"
        )

        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass

        return self.rate_limit_wait_seconds

    def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        endpoint: str = "central",
    ) -> dict[str, Any]:
        """
        Execute one GRID GraphQL request.
        """

        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                "GraphQL query must be a non-empty string."
            )

        endpoint_url = self.endpoints.get(endpoint)

        if endpoint_url is None:
            allowed = ", ".join(
                sorted(self.endpoints.keys())
            )

            raise ValueError(
                f"Unknown GRID endpoint '{endpoint}'. "
                f"Allowed endpoints: {allowed}"
            )

        request_body = {
            "query": query,
            "variables": variables or {},
        }

        for attempt in range(
            1,
            self.maximum_retries + 1,
        ):
            self._wait_for_request_slot()

            try:
                response = self._http_client.post(
                    endpoint_url,
                    json=request_body,
                )

                self._record_request_time()

            except httpx.TimeoutException as error:
                if attempt == self.maximum_retries:
                    raise GridRequestError(
                        f"GRID request to '{endpoint}' "
                        f"timed out after "
                        f"{self.maximum_retries} attempts."
                    ) from error

                wait_seconds = attempt * 5

                print(
                    f"GRID request timed out. "
                    f"Retrying in {wait_seconds} seconds..."
                )

                time.sleep(wait_seconds)
                continue

            except httpx.RequestError as error:
                if attempt == self.maximum_retries:
                    raise GridRequestError(
                        f"Could not connect to GRID "
                        f"endpoint '{endpoint}': {error}"
                    ) from error

                wait_seconds = attempt * 5

                print(
                    f"GRID connection failed. "
                    f"Retrying in {wait_seconds} seconds..."
                )

                time.sleep(wait_seconds)
                continue

            if response.status_code == 429:
                wait_seconds = self._get_retry_wait(
                    response
                )

                if attempt == self.maximum_retries:
                    raise GridRequestError(
                        "GRID rate limit was still active "
                        "after all retry attempts."
                    )

                print(
                    f"GRID rate limit reached. "
                    f"Waiting {wait_seconds:.0f} seconds "
                    f"before retrying..."
                )

                time.sleep(wait_seconds)
                continue

            if response.status_code >= 400:
                response_preview = response.text[:1000]

                raise GridRequestError(
                    f"GRID returned HTTP "
                    f"{response.status_code} from "
                    f"'{endpoint}'. Response: "
                    f"{response_preview}"
                )

            try:
                response_body = response.json()

            except ValueError as error:
                raise GridRequestError(
                    "GRID returned a response that was "
                    "not valid JSON."
                ) from error

            if not isinstance(response_body, dict):
                raise GridRequestError(
                    "GRID returned an unexpected "
                    "JSON structure."
                )

            graphql_errors = response_body.get(
                "errors"
            )

            if self._contains_rate_limit_error(
                graphql_errors
            ):
                if attempt == self.maximum_retries:
                    raise GridGraphQLError(
                        graphql_errors
                    )

                wait_seconds = (
                    self.rate_limit_wait_seconds
                )

                print(
                    f"GRID GraphQL rate limit reached. "
                    f"Waiting {wait_seconds:.0f} seconds "
                    f"before retrying..."
                )

                time.sleep(wait_seconds)
                continue

            if graphql_errors:
                if not isinstance(
                    graphql_errors,
                    list,
                ):
                    graphql_errors = [
                        {
                            "message": str(
                                graphql_errors
                            )
                        }
                    ]

                raise GridGraphQLError(
                    graphql_errors
                )

            data = response_body.get("data")

            if not isinstance(data, dict):
                raise GridRequestError(
                    "GRID response did not contain "
                    "a valid 'data' object."
                )

            return data

        raise GridRequestError(
            "GRID request failed unexpectedly."
        )

    def central(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.execute(
            query=query,
            variables=variables,
            endpoint="central",
        )

    def series_state(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.execute(
            query=query,
            variables=variables,
            endpoint="series_state",
        )

    def stats(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.execute(
            query=query,
            variables=variables,
            endpoint="stats",
        )

    def paginate(
        self,
        query: str,
        connection_name: str,
        variables: dict[str, Any] | None = None,
        endpoint: str = "central",
        page_size: int = 50,
        after_variable: str = "after",
        first_variable: str = "first",
    ) -> list[dict[str, Any]]:
        """
        Retrieve every node from a paginated connection.
        """

        if not 1 <= page_size <= 50:
            raise ValueError(
                "GRID page_size must be between 1 and 50."
            )

        original_variables = dict(variables or {})

        all_nodes: list[dict[str, Any]] = []

        after_cursor: str | None = None
        page_number = 1

        while True:
            print(
                f"Requesting page {page_number} "
                f"of '{connection_name}'..."
            )

            page_variables = dict(
                original_variables
            )

            page_variables[first_variable] = (
                page_size
            )

            page_variables[after_variable] = (
                after_cursor
            )

            data = self.execute(
                query=query,
                variables=page_variables,
                endpoint=endpoint,
            )

            connection = data.get(
                connection_name
            )

            if not isinstance(connection, dict):
                raise GridRequestError(
                    f"GraphQL response did not "
                    f"contain connection "
                    f"'{connection_name}'."
                )

            edges = connection.get("edges", [])

            if not isinstance(edges, list):
                raise GridRequestError(
                    f"Connection '{connection_name}' "
                    f"did not contain a valid edges list."
                )

            page_node_count = 0

            for edge in edges:
                if not isinstance(edge, dict):
                    continue

                node = edge.get("node")

                if isinstance(node, dict):
                    all_nodes.append(node)
                    page_node_count += 1

            print(
                f"Received {page_node_count} records. "
                f"Total collected: {len(all_nodes)}"
            )

            page_info = connection.get(
                "pageInfo",
                {},
            )

            if not isinstance(page_info, dict):
                raise GridRequestError(
                    f"Connection '{connection_name}' "
                    f"did not contain valid pageInfo."
                )

            has_next_page = bool(
                page_info.get("hasNextPage")
            )

            if not has_next_page:
                break

            next_cursor = page_info.get(
                "endCursor"
            )

            if (
                not isinstance(next_cursor, str)
                or not next_cursor
            ):
                raise GridRequestError(
                    "GRID reported another page "
                    "but did not provide an endCursor."
                )

            if next_cursor == after_cursor:
                raise GridRequestError(
                    "GRID returned the same "
                    "pagination cursor twice."
                )

            after_cursor = next_cursor
            page_number += 1

        return all_nodes