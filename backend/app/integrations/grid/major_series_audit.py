from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .client import (
    GridClient,
    GridClientError,
    GridRequestError,
)

from .major_catalog import (
    DEFAULT_MAJOR_SLUG,
    get_all_majors,
    get_major,
)

from .queries import (
    GET_SERIES_FOR_TOURNAMENT,
    GET_TOURNAMENT_WITH_CHILDREN,
)


OUTPUT_DIRECTORY = (
    Path(__file__).parent
    / "audit_results"
    / "majors"
)


def save_json(
    filename: str,
    value: Any,
) -> Path:
    """
    Save formatted JSON in the Major audit directory.
    """

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = OUTPUT_DIRECTORY / filename

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            value,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return output_path


def build_series_filter(
    tournament_id: str,
) -> dict[str, Any]:
    """
    Match series attached to the Major or one of its
    child stage tournaments.
    """

    return {
        "tournament": {
            "id": {
                "in": [tournament_id],
            },

            "includeChildren": {
                "equals": True,
            },
        }
    }


def fetch_tournament_hierarchy(
    client: GridClient,
    tournament_id: str,
) -> dict[str, Any]:
    """
    Retrieve the selected tournament and its children.
    """

    data = client.central(
        GET_TOURNAMENT_WITH_CHILDREN,
        variables={
            "tournamentId": tournament_id,
        },
    )

    tournament = data.get("tournament")

    if not isinstance(tournament, dict):
        raise GridRequestError(
            f"GRID did not return tournament "
            f"{tournament_id}."
        )

    return tournament


def fetch_major_series(
    client: GridClient,
    tournament_id: str,
) -> list[dict[str, Any]]:
    """
    Retrieve every series for the Major and its children.
    """

    return client.paginate(
        query=GET_SERIES_FOR_TOURNAMENT,
        connection_name="allSeries",
        variables={
            "filter": build_series_filter(
                tournament_id
            ),
        },
        endpoint="central",
        page_size=50,
    )


def get_series_tournament_name(
    series: dict[str, Any],
) -> str:
    """
    Return the actual stage/tournament name for a series.
    """

    tournament = series.get("tournament")

    if not isinstance(tournament, dict):
        return "Unknown tournament"

    return str(
        tournament.get(
            "name",
            "Unknown tournament",
        )
    )


def get_series_format(
    series: dict[str, Any],
) -> str:
    """
    Return the shortened format name, such as Bo1 or Bo3.
    """

    series_format = series.get("format")

    if not isinstance(series_format, dict):
        return "Unknown"

    return str(
        series_format.get(
            "nameShortened",
            "Unknown",
        )
    )


def extract_teams(
    series_list: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """
    Build one unique list of participating teams.
    """

    teams_by_id: dict[str, dict[str, str]] = {}

    for series in series_list:
        participants = series.get("teams", [])

        if not isinstance(participants, list):
            continue

        for participant in participants:
            if not isinstance(participant, dict):
                continue

            base_info = participant.get("baseInfo")

            if not isinstance(base_info, dict):
                continue

            team_id = base_info.get("id")

            if team_id is None:
                continue

            team_id = str(team_id)

            teams_by_id[team_id] = {
                "id": team_id,
                "name": str(
                    base_info.get(
                        "name",
                        "Unknown team",
                    )
                ),
                "nameShortened": str(
                    base_info.get(
                        "nameShortened",
                        "",
                    )
                    or ""
                ),
            }

    return sorted(
        teams_by_id.values(),
        key=lambda team: team["name"].lower(),
    )


def extract_service_levels(
    series_list: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Count every product/service-level combination.
    """

    counts: Counter[str] = Counter()

    for series in series_list:
        service_levels = series.get(
            "productServiceLevels",
            [],
        )

        if not isinstance(service_levels, list):
            continue

        for service in service_levels:
            if not isinstance(service, dict):
                continue

            product_name = str(
                service.get(
                    "productName",
                    "Unknown product",
                )
            )

            service_level = str(
                service.get(
                    "serviceLevel",
                    "UNKNOWN",
                )
            )

            key = (
                f"{product_name}:"
                f"{service_level}"
            )

            counts[key] += 1

    return dict(
        sorted(counts.items())
    )


def summarize_stages(
    series_list: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Group series by the tournament/stage attached to them.
    """

    grouped: dict[str, list[dict[str, Any]]] = {}

    for series in series_list:
        stage_name = get_series_tournament_name(
            series
        )

        grouped.setdefault(
            stage_name,
            [],
        ).append(series)

    stage_summaries = []

    for stage_name, stage_series in grouped.items():
        start_times = sorted(
            str(series["startTimeScheduled"])
            for series in stage_series
            if series.get("startTimeScheduled")
        )

        format_counts = Counter(
            get_series_format(series)
            for series in stage_series
        )

        stage_summaries.append(
            {
                "name": stage_name,
                "series_count": len(stage_series),

                "first_series": (
                    start_times[0]
                    if start_times
                    else None
                ),

                "last_series": (
                    start_times[-1]
                    if start_times
                    else None
                ),

                "formats": dict(
                    sorted(format_counts.items())
                ),
            }
        )

    stage_summaries.sort(
        key=lambda stage: (
            stage["first_series"] is None,
            stage["first_series"] or "",
            stage["name"],
        )
    )

    return stage_summaries


def create_summary(
    major: dict[str, Any],
    tournament: dict[str, Any],
    series_list: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build a compact report describing Major coverage.
    """

    start_times = sorted(
        str(series["startTimeScheduled"])
        for series in series_list
        if series.get("startTimeScheduled")
    )

    format_counts = Counter(
        get_series_format(series)
        for series in series_list
    )

    children = tournament.get("children", [])

    if not isinstance(children, list):
        children = []

    return {
        "major": major,
        "grid_tournament": tournament,

        "child_tournament_count": len(children),

        "child_tournaments": children,

        "series_count": len(series_list),

        "first_series": (
            start_times[0]
            if start_times
            else None
        ),

        "last_series": (
            start_times[-1]
            if start_times
            else None
        ),

        "formats": dict(
            sorted(format_counts.items())
        ),

        "stages": summarize_stages(
            series_list
        ),

        "teams": extract_teams(
            series_list
        ),

        "service_levels": extract_service_levels(
            series_list
        ),
    }


def display_summary(
    summary: dict[str, Any],
) -> None:
    """
    Print the useful parts of the report.
    """

    major = summary["major"]

    print()
    print("=" * 80)
    print(major["name"])
    print("=" * 80)

    print(
        f"GRID tournament ID: "
        f"{major['grid_tournament_id']}"
    )

    print(
        f"Child tournaments: "
        f"{summary['child_tournament_count']}"
    )

    print(
        f"Series found: "
        f"{summary['series_count']}"
    )

    print(
        f"Teams found: "
        f"{len(summary['teams'])}"
    )

    print(
        f"First series: "
        f"{summary['first_series'] or 'Unknown'}"
    )

    print(
        f"Last series: "
        f"{summary['last_series'] or 'Unknown'}"
    )

    print()
    print("Formats:")

    for format_name, count in summary["formats"].items():
        print(
            f"  {format_name}: {count}"
        )

    print()
    print("Detected stages:")

    for stage in summary["stages"]:
        print(
            f"  {stage['name']}"
            f" | Series: {stage['series_count']}"
            f" | {stage['first_series']}"
            f" -> {stage['last_series']}"
        )

    print()
    print("Teams:")

    for team in summary["teams"]:
        print(
            f"  {team['name']}"
            f" | GRID ID: {team['id']}"
        )

    print()
    print("Product service levels:")

    if not summary["service_levels"]:
        print("  None returned")

    for service_name, count in (
        summary["service_levels"].items()
    ):
        print(
            f"  {service_name}: {count} series"
        )


def list_supported_majors() -> None:
    """
    Print every Major currently in our whitelist.
    """

    print("Supported Majors:")
    print()

    for major in get_all_majors():
        print(
            f"{major['slug']:<20}"
            f"{major['name']}"
            f" | GRID ID "
            f"{major['grid_tournament_id']}"
        )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit GRID series coverage for one "
            "Counter-Strike Major."
        )
    )

    parser.add_argument(
        "--major",
        default=DEFAULT_MAJOR_SLUG,
        help=(
            "Major slug from major_catalog.py. "
            f"Default: {DEFAULT_MAJOR_SLUG}"
        ),
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List supported Major slugs and exit.",
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    if arguments.list:
        list_supported_majors()
        return

    try:
        major = get_major(arguments.major)

    except ValueError as error:
        print(error)
        print()
        list_supported_majors()
        raise SystemExit(1) from error

    print(
        f"Auditing series coverage for "
        f"{major['name']}..."
    )

    try:
        with GridClient() as client:
            tournament = (
                fetch_tournament_hierarchy(
                    client,
                    major["grid_tournament_id"],
                )
            )

            series_list = fetch_major_series(
                client,
                major["grid_tournament_id"],
            )

    except GridClientError as error:
        print()
        print("Major series audit failed.")
        print(error)
        raise SystemExit(1) from error

    summary = create_summary(
        major,
        tournament,
        series_list,
    )

    raw_series_path = save_json(
        f"{major['slug']}_series.json",
        series_list,
    )

    summary_path = save_json(
        f"{major['slug']}_summary.json",
        summary,
    )

    display_summary(summary)

    print()
    print(
        f"Raw series saved to:\n"
        f"{raw_series_path}"
    )

    print()
    print(
        f"Summary saved to:\n"
        f"{summary_path}"
    )


if __name__ == "__main__":
    main()