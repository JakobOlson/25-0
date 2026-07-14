import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

GRID_API_BASE_URL = "https://api-op.grid.gg"

GRID_CENTRAL_DATA_URL = (
    f"{GRID_API_BASE_URL}/central-data/graphql"
)

GRID_SERIES_STATE_URL = (
    f"{GRID_API_BASE_URL}/live-data-feed/series-state/graphql"
)

GRID_API_KEY = os.getenv("GRID_API_KEY", "").strip()


def get_grid_headers() -> dict[str, str]:
    if not GRID_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GRID_API_KEY is missing from the .env file.",
        )

    return {
        "x-api-key": GRID_API_KEY,
        "accept": "application/json",
        "content-type": "application/json",
    }


async def execute_grid_query(
    url: str,
    query: str,
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=get_grid_headers(),
                json={"query": query},
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="The GRID request timed out.",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to GRID: {exc}",
        ) from exc

    try:
        response_body = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "GRID returned a non-JSON response.",
                "status_code": response.status_code,
                "response": response.text[:500],
            },
        ) from exc

    if response.is_error:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "GRID returned an HTTP error.",
                "grid_status_code": response.status_code,
                "grid_response": response_body,
            },
        )

    if response_body.get("errors"):
        raise HTTPException(
            status_code=502,
            detail={
                "message": "GRID GraphQL returned query errors.",
                "errors": response_body["errors"],
            },
        )

    data = response_body.get("data")

    if data is None:
        raise HTTPException(
            status_code=502,
            detail="GRID returned no data.",
        )

    return data


def format_grid_datetime(value: datetime) -> str:
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


async def get_grid_series(limit: int = 50) -> dict[str, Any]:
    limit = max(1, min(limit, 100))

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(years=7)
    end_time = now + timedelta(days=7)

    start_value = format_grid_datetime(start_time)
    end_value = format_grid_datetime(end_time)

    query = f"""
    query AllSeries {{
        allSeries(
            filter: {{
                startTimeScheduled: {{
                    gte: "{start_value}"
                    lte: "{end_value}"
                }}
            }}
            orderBy: StartTimeScheduled
        ) {{
            totalCount
            edges {{
                node {{
                    id
                    startTimeScheduled
                    teams {{
                        baseInfo {{
                            id
                            name
                        }}
                    }}
                    tournament {{
                        id
                        name
                    }}
                }}
            }}
            pageInfo {{
                endCursor
                hasNextPage
            }}
        }}
    }}
    """

    data = await execute_grid_query(
        url=GRID_CENTRAL_DATA_URL,
        query=query,
    )

    connection = data.get("allSeries", {})
    edges = connection.get("edges", [])

    series = [
        edge["node"]
        for edge in edges[:limit]
        if edge.get("node") is not None
    ]

    return {
        "total_count": connection.get("totalCount", 0),
        "returned_count": len(series),
        "series": series,
        "page_info": connection.get("pageInfo"),
    }


async def get_grid_series_state(
    series_id: str,
) -> dict[str, Any]:
    clean_series_id = series_id.strip()

    if not clean_series_id.isdigit():
        raise HTTPException(
            status_code=400,
            detail="GRID series ID must contain only numbers.",
        )

    query = f"""
    query SeriesState {{
        seriesState(id: "{clean_series_id}") {{
            startedAt
            started
            finished
            teams {{
                won
                score
                kills
                deaths
                players {{
                    kills
                    deaths
                }}
            }}
        }}
    }}
    """

    data = await execute_grid_query(
        url=GRID_SERIES_STATE_URL,
        query=query,
    )

    series_state = data.get("seriesState")

    if series_state is None:
        raise HTTPException(
            status_code=404,
            detail=f"GRID series {clean_series_id} was not found.",
        )

    return series_state