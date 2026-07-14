from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .client import GridClient, GridClientError
from .state_queries import GET_SERIES_STATE
from .transform_series_state import transform_series_state


MAJOR_SLUG = "austin_2025"
MAJOR_NAME = "BLAST.tv Austin Major 2025"
TOURNAMENT_ID = "826167"


BASE_DIRECTORY = Path(__file__).parent

SERIES_LIST_FILE = (
    BASE_DIRECTORY
    / "audit_results"
    / "majors"
    / "austin_2025_series.json"
)

IMPORT_DIRECTORY = (
    BASE_DIRECTORY
    / "import_results"
    / "austin_2025"
)

RAW_STATE_DIRECTORY = (
    IMPORT_DIRECTORY
    / "raw_series_states"
)

COMPACT_STATE_DIRECTORY = (
    IMPORT_DIRECTORY
    / "compact_series_states"
)

PROGRESS_FILE = (
    IMPORT_DIRECTORY
    / "import_progress.json"
)

FINAL_OUTPUT_FILE = (
    IMPORT_DIRECTORY
    / "austin_2025_major.json"
)

FAILED_OUTPUT_FILE = (
    IMPORT_DIRECTORY
    / "failed_series.json"
)


# These are aliases representing the same organization.
TEAM_CANONICALIZATION: dict[str, dict[str, str]] = {
    "52000": {
        "canonical_team_id": "49643",
        "canonical_name": "paiN",
    },

    "52230": {
        "canonical_team_id": "52198",
        "canonical_name": "Wildcard Gaming",
    },
}


STAGE_BOUNDARIES = [
    {
        "name": "stage_1",
        "display_name": "Stage 1",
        "start": "2025-06-03T00:00:00Z",
        "end": "2025-06-07T00:00:00Z",
    },
    {
        "name": "stage_2",
        "display_name": "Stage 2",
        "start": "2025-06-07T00:00:00Z",
        "end": "2025-06-11T00:00:00Z",
    },
    {
        "name": "stage_3",
        "display_name": "Stage 3",
        "start": "2025-06-12T00:00:00Z",
        "end": "2025-06-16T00:00:00Z",
    },
    {
        "name": "playoffs",
        "display_name": "Playoffs",
        "start": "2025-06-19T00:00:00Z",
        "end": "2025-06-23T00:00:00Z",
    },
]


def ensure_directories() -> None:
    """
    Create all importer output directories.
    """

    RAW_STATE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    COMPACT_STATE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def load_json(
    file_path: Path,
) -> Any:
    """
    Load JSON from disk.
    """

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_json(
    file_path: Path,
    value: Any,
) -> None:
    """
    Save formatted JSON to disk.
    """

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_file = file_path.with_suffix(
        file_path.suffix + ".tmp"
    )

    with temporary_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            value,
            file,
            indent=2,
            ensure_ascii=False,
        )

    temporary_file.replace(file_path)


def load_series_list() -> list[dict[str, Any]]:
    """
    Load the Central Data series list created by the Major audit.
    """

    if not SERIES_LIST_FILE.exists():
        raise FileNotFoundError(
            "Austin series list was not found:\n"
            f"{SERIES_LIST_FILE}\n\n"
            "Run the Major series audit first."
        )

    value = load_json(
        SERIES_LIST_FILE
    )

    if not isinstance(value, list):
        raise ValueError(
            "Austin series list must contain a JSON array."
        )

    return [
        series
        for series in value
        if isinstance(series, dict)
    ]


def parse_utc_datetime(
    value: str,
) -> datetime:
    """
    Parse GRID's ISO-8601 UTC datetime format.
    """

    normalized = value.strip()

    if normalized.endswith("Z"):
        normalized = (
            normalized[:-1]
            + "+00:00"
        )

    parsed = datetime.fromisoformat(
        normalized
    )

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.astimezone(
        timezone.utc
    )


def determine_stage(
    scheduled_start: str | None,
) -> dict[str, str]:
    """
    Assign an Austin Major stage based on scheduled match time.
    """

    if not scheduled_start:
        return {
            "name": "unknown",
            "display_name": "Unknown",
        }

    match_time = parse_utc_datetime(
        scheduled_start
    )

    for boundary in STAGE_BOUNDARIES:
        start_time = parse_utc_datetime(
            boundary["start"]
        )

        end_time = parse_utc_datetime(
            boundary["end"]
        )

        if start_time <= match_time < end_time:
            return {
                "name": boundary["name"],
                "display_name": boundary[
                    "display_name"
                ],
            }

    return {
        "name": "unknown",
        "display_name": "Unknown",
    }


def central_series_team_names(
    series: dict[str, Any],
) -> list[str]:
    """
    Extract team names from a Central Data series record.
    """

    participants = series.get(
        "teams",
        [],
    )

    if not isinstance(participants, list):
        return []

    names: list[str] = []

    for participant in participants:
        if not isinstance(participant, dict):
            continue

        base_info = participant.get(
            "baseInfo",
            {},
        )

        if not isinstance(base_info, dict):
            continue

        name = base_info.get("name")

        if name:
            names.append(
                str(name)
            )

    return names


def fetch_series_state(
    client: GridClient,
    series_id: str,
) -> dict[str, Any]:
    """
    Request one full Series State response from GRID.
    """

    data = client.series_state(
        GET_SERIES_STATE,
        variables={
            "seriesId": series_id,
        },
    )

    series_state = data.get(
        "seriesState"
    )

    if not isinstance(series_state, dict):
        raise RuntimeError(
            f"GRID returned no state for "
            f"series {series_id}."
        )

    return series_state


def canonicalize_team(
    team: dict[str, Any],
) -> None:
    """
    Normalize known duplicate team identities in-place.
    """

    original_team_id = str(
        team.get(
            "team_id",
            "",
        )
    )

    canonical = TEAM_CANONICALIZATION.get(
        original_team_id
    )

    if canonical is None:
        team["original_team_id"] = (
            original_team_id
        )

        return

    team["original_team_id"] = (
        original_team_id
    )

    team["team_id"] = canonical[
        "canonical_team_id"
    ]

    team["name"] = canonical[
        "canonical_name"
    ]


def canonicalize_compact_state(
    compact_state: dict[str, Any],
) -> None:
    """
    Normalize team IDs throughout one transformed series.
    """

    original_winner_id = compact_state.get(
        "winning_team_id"
    )

    if original_winner_id is not None:
        canonical = TEAM_CANONICALIZATION.get(
            str(original_winner_id)
        )

        if canonical is not None:
            compact_state[
                "winning_team_id"
            ] = canonical[
                "canonical_team_id"
            ]

    series_teams = compact_state.get(
        "teams",
        [],
    )

    if isinstance(series_teams, list):
        for team in series_teams:
            if isinstance(team, dict):
                canonicalize_team(team)

    games = compact_state.get(
        "games",
        [],
    )

    if not isinstance(games, list):
        return

    for game in games:
        if not isinstance(game, dict):
            continue

        winning_team_id = game.get(
            "winning_team_id"
        )

        if winning_team_id is not None:
            canonical = (
                TEAM_CANONICALIZATION.get(
                    str(winning_team_id)
                )
            )

            if canonical is not None:
                game[
                    "winning_team_id"
                ] = canonical[
                    "canonical_team_id"
                ]

        game_teams = game.get(
            "teams",
            [],
        )

        if not isinstance(game_teams, list):
            continue

        for team in game_teams:
            if isinstance(team, dict):
                canonicalize_team(team)


def add_schedule_information(
    compact_state: dict[str, Any],
    central_series: dict[str, Any],
) -> None:
    """
    Add schedule, stage, and original Central Data context.
    """

    scheduled_start = central_series.get(
        "startTimeScheduled"
    )

    stage = determine_stage(
        str(scheduled_start)
        if scheduled_start
        else None
    )

    compact_state[
        "scheduled_start"
    ] = scheduled_start

    compact_state[
        "stage"
    ] = stage["name"]

    compact_state[
        "stage_display_name"
    ] = stage["display_name"]

    compact_state[
        "scheduled_team_names"
    ] = central_series_team_names(
        central_series
    )

    series_format = central_series.get(
        "format",
        {},
    )

    if isinstance(series_format, dict):
        compact_state[
            "scheduled_format"
        ] = series_format.get(
            "nameShortened"
        )
    else:
        compact_state[
            "scheduled_format"
        ] = None


def should_include_series(
    compact_state: dict[str, Any],
) -> tuple[bool, str]:
    """
    Decide whether a series belongs in the clean Major dataset.
    """

    if not compact_state.get("valid"):
        return False, "invalid"

    if not compact_state.get("started"):
        return False, "not_started"

    if not compact_state.get("finished"):
        return False, "not_finished"

    map_count = int(
        compact_state.get(
            "map_count",
            0,
        )
    )

    if map_count <= 0:
        return False, "no_maps"

    round_count = int(
        compact_state.get(
            "round_count",
            0,
        )
    )

    if round_count <= 0:
        return False, "no_rounds"

    teams = compact_state.get(
        "teams",
        [],
    )

    if not isinstance(teams, list):
        return False, "invalid_teams"

    if len(teams) != 2:
        return False, "unexpected_team_count"

    return True, "included"


def load_progress() -> dict[str, Any]:
    """
    Load resumable import progress.
    """

    if not PROGRESS_FILE.exists():
        return {
            "completed_series_ids": [],
            "failed": [],
        }

    value = load_json(
        PROGRESS_FILE
    )

    if not isinstance(value, dict):
        return {
            "completed_series_ids": [],
            "failed": [],
        }

    completed = value.get(
        "completed_series_ids",
        [],
    )

    failed = value.get(
        "failed",
        [],
    )

    if not isinstance(completed, list):
        completed = []

    if not isinstance(failed, list):
        failed = []

    return {
        "completed_series_ids": [
            str(series_id)
            for series_id in completed
        ],
        "failed": failed,
    }


def save_progress(
    completed_series_ids: set[str],
    failures: list[dict[str, Any]],
) -> None:
    """
    Save importer progress after each series.
    """

    save_json(
        PROGRESS_FILE,
        {
            "completed_series_ids": sorted(
                completed_series_ids
            ),
            "failed": failures,
        },
    )


def compact_file_for_series(
    series_id: str,
) -> Path:
    return (
        COMPACT_STATE_DIRECTORY
        / f"{series_id}.json"
    )


def raw_file_for_series(
    series_id: str,
) -> Path:
    return (
        RAW_STATE_DIRECTORY
        / f"{series_id}.json"
    )


def process_series(
    client: GridClient,
    central_series: dict[str, Any],
    keep_raw: bool,
    force: bool,
) -> dict[str, Any]:
    """
    Fetch, transform, enrich, and save one series.
    """

    series_id = str(
        central_series.get(
            "id",
            "",
        )
    )

    if not series_id:
        raise ValueError(
            "Central Data series has no ID."
        )

    compact_file = compact_file_for_series(
        series_id
    )

    if compact_file.exists() and not force:
        compact_state = load_json(
            compact_file
        )

        if not isinstance(
            compact_state,
            dict,
        ):
            raise ValueError(
                f"Compact cache for {series_id} "
                "is not a JSON object."
            )

        return compact_state

    raw_file = raw_file_for_series(
        series_id
    )

    if raw_file.exists() and not force:
        series_state = load_json(
            raw_file
        )

        if not isinstance(
            series_state,
            dict,
        ):
            raise ValueError(
                f"Raw cache for {series_id} "
                "is not a JSON object."
            )
    else:
        series_state = fetch_series_state(
            client,
            series_id,
        )

        if keep_raw:
            save_json(
                raw_file,
                series_state,
            )

    compact_state = transform_series_state(
        series_state
    )

    add_schedule_information(
        compact_state,
        central_series,
    )

    canonicalize_compact_state(
        compact_state
    )

    included, reason = should_include_series(
        compact_state
    )

    compact_state[
        "included_in_major"
    ] = included

    compact_state[
        "exclusion_reason"
    ] = (
        None
        if included
        else reason
    )

    save_json(
        compact_file,
        compact_state,
    )

    return compact_state


def find_exact_duplicate_groups(
    series_list: list[dict[str, Any]],
) -> list[list[str]]:
    """
    Find series with the same scheduled teams and similar start time.

    This is only a report. Validity still decides which records survive.
    """

    grouped: dict[
        tuple[str, tuple[str, ...]],
        list[str],
    ] = {}

    for series in series_list:
        series_id = str(
            series.get(
                "series_id",
                "",
            )
        )

        scheduled_start = str(
            series.get(
                "scheduled_start",
                "",
            )
        )

        teams = series.get(
            "scheduled_team_names",
            [],
        )

        if not isinstance(teams, list):
            teams = []

        team_key = tuple(
            sorted(
                str(team).lower()
                for team in teams
            )
        )

        if not scheduled_start or not team_key:
            continue

        parsed_time = parse_utc_datetime(
            scheduled_start
        )

        date_key = parsed_time.strftime(
            "%Y-%m-%d"
        )

        key = (
            date_key,
            team_key,
        )

        grouped.setdefault(
            key,
            [],
        ).append(series_id)

    return [
        series_ids
        for series_ids in grouped.values()
        if len(series_ids) > 1
    ]


def build_player_index(
    included_series: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build a unique player list from all valid Austin series.
    """

    players: dict[
        str,
        dict[str, Any],
    ] = {}

    for series in included_series:
        games = series.get(
            "games",
            [],
        )

        if not isinstance(games, list):
            continue

        for game in games:
            if not isinstance(game, dict):
                continue

            teams = game.get(
                "teams",
                [],
            )

            if not isinstance(teams, list):
                continue

            for team in teams:
                if not isinstance(team, dict):
                    continue

                team_id = str(
                    team.get(
                        "team_id",
                        "",
                    )
                )

                team_name = str(
                    team.get(
                        "name",
                        "Unknown team",
                    )
                )

                game_players = team.get(
                    "players",
                    [],
                )

                if not isinstance(
                    game_players,
                    list,
                ):
                    continue

                for player in game_players:
                    if not isinstance(
                        player,
                        dict,
                    ):
                        continue

                    player_id = str(
                        player.get(
                            "player_id",
                            "",
                        )
                    )

                    if not player_id:
                        continue

                    record = players.setdefault(
                        player_id,
                        {
                            "player_id": player_id,
                            "name": str(
                                player.get(
                                    "name",
                                    "Unknown player",
                                )
                            ),
                            "teams": {},
                            "maps_played": 0,
                            "rounds_played": 0,
                            "kills": 0,
                            "deaths": 0,
                            "assists": 0,
                            "headshots": 0,
                            "damage_dealt": 0,
                        },
                    )

                    record["teams"][
                        team_id
                    ] = team_name

                    record["maps_played"] += 1

                    record["rounds_played"] += int(
                        game.get(
                            "round_count",
                            0,
                        )
                    )

                    record["kills"] += int(
                        player.get(
                            "kills",
                            0,
                        )
                    )

                    record["deaths"] += int(
                        player.get(
                            "deaths",
                            0,
                        )
                    )

                    record["assists"] += int(
                        player.get(
                            "assists",
                            0,
                        )
                    )

                    record["headshots"] += int(
                        player.get(
                            "headshots",
                            0,
                        )
                    )

                    record[
                        "damage_dealt"
                    ] += int(
                        player.get(
                            "damage_dealt",
                            0,
                        )
                    )

    output: list[dict[str, Any]] = []

    for record in players.values():
        rounds_played = int(
            record["rounds_played"]
        )

        kills = int(
            record["kills"]
        )

        deaths = int(
            record["deaths"]
        )

        record["adr"] = round(
            (
                record["damage_dealt"]
                / rounds_played
            )
            if rounds_played
            else 0.0,
            2,
        )

        record["kd_ratio"] = round(
            (
                kills
                / deaths
            )
            if deaths
            else float(kills),
            3,
        )

        record["kills_per_round"] = round(
            (
                kills
                / rounds_played
            )
            if rounds_played
            else 0.0,
            3,
        )

        record["teams"] = [
            {
                "team_id": team_id,
                "name": team_name,
            }
            for team_id, team_name
            in sorted(
                record["teams"].items()
            )
        ]

        output.append(record)

    return sorted(
        output,
        key=lambda player: (
            -player["adr"],
            player["name"].lower(),
        ),
    )


def build_team_index(
    included_series: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build a unique team list from valid Austin series.
    """

    teams: dict[
        str,
        dict[str, Any],
    ] = {}

    for series in included_series:
        series_teams = series.get(
            "teams",
            [],
        )

        if not isinstance(series_teams, list):
            continue

        for team in series_teams:
            if not isinstance(team, dict):
                continue

            team_id = str(
                team.get(
                    "team_id",
                    "",
                )
            )

            if not team_id:
                continue

            record = teams.setdefault(
                team_id,
                {
                    "team_id": team_id,
                    "name": str(
                        team.get(
                            "name",
                            "Unknown team",
                        )
                    ),
                    "series_played": 0,
                    "series_won": 0,
                    "series_lost": 0,
                },
            )

            record["series_played"] += 1

            if team.get("won"):
                record["series_won"] += 1
            else:
                record["series_lost"] += 1

    return sorted(
        teams.values(),
        key=lambda team: team["name"].lower(),
    )


def build_final_dataset(
    imported_series: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build the final clean Austin Major dataset.
    """

    included_series = [
        series
        for series in imported_series
        if series.get(
            "included_in_major"
        )
    ]

    excluded_series = [
        {
            "series_id": series.get(
                "series_id"
            ),
            "scheduled_start": series.get(
                "scheduled_start"
            ),
            "scheduled_team_names": series.get(
                "scheduled_team_names"
            ),
            "reason": series.get(
                "exclusion_reason"
            ),
            "valid": series.get("valid"),
            "started": series.get("started"),
            "finished": series.get("finished"),
            "map_count": series.get(
                "map_count"
            ),
            "round_count": series.get(
                "round_count"
            ),
        }
        for series in imported_series
        if not series.get(
            "included_in_major"
        )
    ]

    included_series.sort(
        key=lambda series: (
            str(
                series.get(
                    "scheduled_start",
                    "",
                )
            ),
            str(
                series.get(
                    "series_id",
                    "",
                )
            ),
        )
    )

    stage_counts = Counter(
        str(
            series.get(
                "stage",
                "unknown",
            )
        )
        for series in included_series
    )

    format_counts = Counter(
        str(
            series.get(
                "scheduled_format",
                "Unknown",
            )
        )
        for series in included_series
    )

    return {
        "major": {
            "slug": MAJOR_SLUG,
            "name": MAJOR_NAME,
            "grid_tournament_id": (
                TOURNAMENT_ID
            ),
            "title": "cs2",
            "year": 2025,
        },

        "import_summary": {
            "scheduled_series_count": len(
                imported_series
            ),

            "included_series_count": len(
                included_series
            ),

            "excluded_series_count": len(
                excluded_series
            ),

            "failed_request_count": len(
                failures
            ),

            "stage_counts": dict(
                sorted(
                    stage_counts.items()
                )
            ),

            "format_counts": dict(
                sorted(
                    format_counts.items()
                )
            ),
        },

        "duplicate_candidate_groups": (
            find_exact_duplicate_groups(
                imported_series
            )
        ),

        "excluded_series": excluded_series,
        "failed_series": failures,

        "teams": build_team_index(
            included_series
        ),

        "players": build_player_index(
            included_series
        ),

        "series": included_series,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import and clean all BLAST.tv "
            "Austin Major 2025 Series State data."
        )
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Ignore compact caches and request "
            "series again."
        ),
    )

    parser.add_argument(
        "--keep-raw",
        action="store_true",
        help=(
            "Keep the very large raw Series State "
            "response for every match."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Process only the first N series. "
            "Useful for testing."
        ),
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    ensure_directories()

    central_series_list = load_series_list()

    central_series_list.sort(
        key=lambda series: (
            str(
                series.get(
                    "startTimeScheduled",
                    "",
                )
            ),
            str(
                series.get(
                    "id",
                    "",
                )
            ),
        )
    )

    if arguments.limit is not None:
        if arguments.limit <= 0:
            raise ValueError(
                "--limit must be greater than zero."
            )

        central_series_list = (
            central_series_list[
                :arguments.limit
            ]
        )

    progress = load_progress()

    completed_series_ids = set(
        progress[
            "completed_series_ids"
        ]
    )

    failures = [
        failure
        for failure in progress["failed"]
        if isinstance(failure, dict)
    ]

    imported_series: list[
        dict[str, Any]
    ] = []

    total_series = len(
        central_series_list
    )

    print(
        f"Importing {total_series} Austin "
        f"Major series..."
    )

    print(
        f"Already completed: "
        f"{len(completed_series_ids)}"
    )

    try:
        with GridClient() as client:
            for index, central_series in enumerate(
                central_series_list,
                start=1,
            ):
                series_id = str(
                    central_series.get(
                        "id",
                        "",
                    )
                )

                teams_text = " vs ".join(
                    central_series_team_names(
                        central_series
                    )
                )

                print()
                print(
                    f"[{index}/{total_series}] "
                    f"{series_id} "
                    f"{teams_text}"
                )

                try:
                    compact_state = process_series(
                        client=client,
                        central_series=central_series,
                        keep_raw=arguments.keep_raw,
                        force=arguments.force,
                    )

                except (
                    GridClientError,
                    RuntimeError,
                    ValueError,
                ) as error:
                    print(
                        f"FAILED: {error}"
                    )

                    failure_record = {
                        "series_id": series_id,
                        "error": str(error),
                    }

                    failures = [
                        failure
                        for failure in failures
                        if failure.get(
                            "series_id"
                        ) != series_id
                    ]

                    failures.append(
                        failure_record
                    )

                    save_progress(
                        completed_series_ids,
                        failures,
                    )

                    continue

                imported_series.append(
                    compact_state
                )

                completed_series_ids.add(
                    series_id
                )

                failures = [
                    failure
                    for failure in failures
                    if failure.get(
                        "series_id"
                    ) != series_id
                ]

                save_progress(
                    completed_series_ids,
                    failures,
                )

                included = compact_state.get(
                    "included_in_major"
                )

                if included:
                    print(
                        "INCLUDED"
                        f" | Stage: "
                        f"{compact_state['stage_display_name']}"
                        f" | Maps: "
                        f"{compact_state['map_count']}"
                        f" | Rounds: "
                        f"{compact_state['round_count']}"
                    )
                else:
                    print(
                        "EXCLUDED"
                        f" | Reason: "
                        f"{compact_state['exclusion_reason']}"
                    )

    except KeyboardInterrupt:
        print()
        print(
            "Import interrupted. Progress was saved."
        )

        raise SystemExit(130)

    # Load compact files for all selected series so a resumed
    # import also includes data completed in earlier runs.
    imported_series = []

    for central_series in central_series_list:
        series_id = str(
            central_series.get(
                "id",
                "",
            )
        )

        compact_file = compact_file_for_series(
            series_id
        )

        if not compact_file.exists():
            continue

        compact_state = load_json(
            compact_file
        )

        if isinstance(compact_state, dict):
            imported_series.append(
                compact_state
            )

    final_dataset = build_final_dataset(
        imported_series,
        failures,
    )

    save_json(
        FINAL_OUTPUT_FILE,
        final_dataset,
    )

    save_json(
        FAILED_OUTPUT_FILE,
        failures,
    )

    summary = final_dataset[
        "import_summary"
    ]

    print()
    print("=" * 80)
    print("AUSTIN MAJOR IMPORT COMPLETE")
    print("=" * 80)

    print(
        f"Scheduled records: "
        f"{summary['scheduled_series_count']}"
    )

    print(
        f"Included valid series: "
        f"{summary['included_series_count']}"
    )

    print(
        f"Excluded series: "
        f"{summary['excluded_series_count']}"
    )

    print(
        f"Failed requests: "
        f"{summary['failed_request_count']}"
    )

    print()
    print("Stage counts:")

    for stage, count in (
        summary[
            "stage_counts"
        ].items()
    ):
        print(
            f"  {stage}: {count}"
        )

    print()
    print("Format counts:")

    for series_format, count in (
        summary[
            "format_counts"
        ].items()
    ):
        print(
            f"  {series_format}: {count}"
        )

    print()
    print(
        f"Teams: "
        f"{len(final_dataset['teams'])}"
    )

    print(
        f"Players: "
        f"{len(final_dataset['players'])}"
    )

    print()
    print(
        f"Final dataset saved to:\n"
        f"{FINAL_OUTPUT_FILE}"
    )

    if (
        arguments.limit is None
        and summary[
            "included_series_count"
        ] != 106
    ):
        print()
        print(
            "WARNING: Expected 106 valid Austin "
            "Major series, but imported "
            f"{summary['included_series_count']}."
        )

        print(
            "Review excluded_series, failed_series, "
            "and duplicate_candidate_groups in the "
            "output file."
        )


if __name__ == "__main__":
    main()