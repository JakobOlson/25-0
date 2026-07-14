from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .client import GridClient, GridClientError
from .queries import GET_TOURNAMENTS


CSGO_TITLE_ID = "1"
CS2_TITLE_ID = "28"

TITLE_IDS = {
    "csgo": CSGO_TITLE_ID,
    "cs2": CS2_TITLE_ID,
}


OUTPUT_DIRECTORY = (
    Path(__file__).parent
    / "audit_results"
)


MAJOR_SEARCH_TERMS = {
    "major",
    "blast.tv",
    "pgl",
    "star-ladder",
    "starladder",
    "iem rio",
    "rio 2022",
    "paris 2023",
    "copenhagen 2024",
    "shanghai 2024",
    "austin 2025",
}


def tournament_filter_for_title(
    title_id: str,
) -> dict[str, Any]:
    """
    Create the GraphQL filter used to retrieve tournaments
    belonging to one GRID title.
    """

    return {
        "title": {
            "id": {
                "in": [title_id]
            }
        }
    }


def fetch_tournaments_for_title(
    client: GridClient,
    title_id: str,
) -> list[dict[str, Any]]:
    """
    Retrieve all accessible tournaments for one GRID title.
    """

    return client.paginate(
        query=GET_TOURNAMENTS,
        connection_name="tournaments",
        variables={
            "filter": tournament_filter_for_title(
                title_id
            )
        },
        endpoint="central",
        page_size=50,
    )


def normalized_text(value: Any) -> str:
    """
    Convert a value into lowercase searchable text.
    """

    if value is None:
        return ""

    return str(value).strip().lower()


def tournament_search_text(
    tournament: dict[str, Any],
) -> str:
    """
    Combine the tournament and parent names so both are
    checked when searching for likely Majors.
    """

    parent = tournament.get("parent")

    if not isinstance(parent, dict):
        parent = {}

    parts = [
        tournament.get("name"),
        tournament.get("nameShortened"),
        parent.get("name"),
        parent.get("nameShortened"),
    ]

    return " ".join(
        normalized_text(part)
        for part in parts
        if part is not None
    )


def looks_like_major(
    tournament: dict[str, Any],
) -> bool:
    """
    Return True when a tournament or its parent contains
    one of our Major-related search terms.

    This creates candidates, not a guaranteed official-Major
    classification.
    """

    search_text = tournament_search_text(tournament)

    return any(
        term in search_text
        for term in MAJOR_SEARCH_TERMS
    )


def sort_date(
    tournament: dict[str, Any],
) -> str:
    """
    Produce a sortable date.

    Missing dates sort to the beginning.
    """

    start_date = tournament.get("startDate")

    if isinstance(start_date, str):
        return start_date

    return ""


def save_json(
    filename: str,
    data: Any,
) -> Path:
    """
    Save audit information as formatted JSON.
    """

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = OUTPUT_DIRECTORY / filename

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return output_file


def display_tournament(
    tournament: dict[str, Any],
) -> None:
    """
    Print one tournament in a readable terminal format.
    """

    tournament_id = tournament.get(
        "id",
        "Unknown ID",
    )

    name = tournament.get(
        "name",
        "Unknown tournament",
    )

    start_date = tournament.get(
        "startDate",
        "Unknown",
    )

    end_date = tournament.get(
        "endDate",
        "Unknown",
    )

    parent = tournament.get("parent")

    if isinstance(parent, dict):
        parent_name = parent.get(
            "name",
            "Unknown parent",
        )
    else:
        parent_name = "None"

    print(
        f"- {start_date} to {end_date}"
        f" | {name}"
        f" | ID: {tournament_id}"
        f" | Parent: {parent_name}"
    )


def audit_title(
    client: GridClient,
    title_name: str,
    title_id: str,
) -> dict[str, Any]:
    """
    Fetch and analyze tournament coverage for one title.
    """

    print()
    print("=" * 80)
    print(
        f"Auditing {title_name.upper()} "
        f"| GRID title ID {title_id}"
    )
    print("=" * 80)

    tournaments = fetch_tournaments_for_title(
        client,
        title_id,
    )

    tournaments.sort(
        key=sort_date
    )

    major_candidates = [
        tournament
        for tournament in tournaments
        if looks_like_major(tournament)
    ]

    all_output_file = save_json(
        f"{title_name}_all_tournaments.json",
        tournaments,
    )

    candidates_output_file = save_json(
        f"{title_name}_major_candidates.json",
        major_candidates,
    )

    dated_tournaments = [
        tournament
        for tournament in tournaments
        if tournament.get("startDate")
    ]

    earliest_date = None
    latest_date = None

    if dated_tournaments:
        earliest_date = dated_tournaments[0].get(
            "startDate"
        )

        latest_date = dated_tournaments[-1].get(
            "startDate"
        )

    print(
        f"Accessible tournaments: "
        f"{len(tournaments)}"
    )

    print(
        f"Possible Major-related tournaments: "
        f"{len(major_candidates)}"
    )

    print(
        f"Earliest tournament start: "
        f"{earliest_date or 'Unknown'}"
    )

    print(
        f"Latest tournament start: "
        f"{latest_date or 'Unknown'}"
    )

    print(
        f"Saved all tournaments to:\n"
        f"{all_output_file}"
    )

    print(
        f"Saved Major candidates to:\n"
        f"{candidates_output_file}"
    )

    if major_candidates:
        print()
        print("Possible Major tournaments:")
        print()

        for tournament in major_candidates:
            display_tournament(tournament)

    else:
        print()
        print(
            "No possible Majors were found using "
            "the current search terms."
        )

    return {
        "title": title_name,
        "title_id": title_id,
        "tournament_count": len(tournaments),
        "major_candidate_count": len(
            major_candidates
        ),
        "earliest_start_date": earliest_date,
        "latest_start_date": latest_date,
        "all_tournaments_file": str(
            all_output_file
        ),
        "major_candidates_file": str(
            candidates_output_file
        ),
    }


def main() -> None:
    print(
        "Starting GRID Counter-Strike "
        "tournament coverage audit..."
    )

    audit_summary: list[dict[str, Any]] = []

    try:
        with GridClient() as client:
            for title_name, title_id in TITLE_IDS.items():
                result = audit_title(
                    client,
                    title_name,
                    title_id,
                )

                audit_summary.append(result)

    except GridClientError as error:
        print()
        print("GRID tournament audit failed.")
        print(error)
        raise SystemExit(1) from error

    summary_file = save_json(
        "coverage_summary.json",
        audit_summary,
    )

    print()
    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)

    for result in audit_summary:
        print(
            f"{result['title'].upper()}: "
            f"{result['tournament_count']} tournaments, "
            f"{result['major_candidate_count']} "
            f"Major candidates"
        )

    print()
    print(
        f"Summary saved to:\n"
        f"{summary_file}"
    )


if __name__ == "__main__":
    main()