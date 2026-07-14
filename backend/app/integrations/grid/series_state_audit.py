from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .client import GridClient, GridClientError
from .state_queries import GET_SERIES_STATE


DEFAULT_SERIES_ID = "2812784"


DUPLICATE_CANDIDATE_IDS = [
    # Falcons vs B8
    "2812712",
    "2814375",

    # FaZe vs Heroic
    "2812713",
    "2814374",

    # 3DMAX vs BetBoom
    "2812714",
    "2814382",

    # Virtus.Pro vs OG
    "2812715",
    "2814381",
]


OUTPUT_DIRECTORY = (
    Path(__file__).parent
    / "audit_results"
    / "series_states"
)


def save_json(
    filename: str,
    value: Any,
) -> Path:
    """
    Save one Series State response as formatted JSON.
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


def fetch_series_state(
    client: GridClient,
    series_id: str,
) -> dict[str, Any]:
    """
    Retrieve the final or current GRID state for one series.
    """

    data = client.series_state(
        GET_SERIES_STATE,
        variables={
            "seriesId": series_id,
        },
    )

    series_state = data.get("seriesState")

    if not isinstance(series_state, dict):
        raise RuntimeError(
            f"GRID returned no Series State object "
            f"for series {series_id}."
        )

    return series_state


def extract_players(
    series_state: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Extract every player from both teams.
    """

    players: list[dict[str, Any]] = []

    teams = series_state.get("teams", [])

    if not isinstance(teams, list):
        return players

    for team in teams:
        if not isinstance(team, dict):
            continue

        team_id = str(
            team.get(
                "id",
                "unknown",
            )
        )

        team_name = str(
            team.get(
                "name",
                "Unknown team",
            )
        )

        team_players = team.get(
            "players",
            [],
        )

        if not isinstance(team_players, list):
            continue

        for player in team_players:
            if not isinstance(player, dict):
                continue

            player_copy = dict(player)

            player_copy["team_id"] = team_id
            player_copy["team_name"] = team_name

            players.append(player_copy)

    return players


def display_team(
    team: dict[str, Any],
) -> None:
    """
    Print one team's series-level statistics and players.
    """

    name = team.get(
        "name",
        "Unknown team",
    )

    team_id = team.get(
        "id",
        "Unknown",
    )

    score = team.get(
        "score",
        "Unknown",
    )

    won = bool(
        team.get(
            "won",
            False,
        )
    )

    kills = team.get(
        "kills",
        0,
    )

    deaths = team.get(
        "deaths",
        0,
    )

    assists = team.get(
        "killAssistsGiven",
        0,
    )

    headshots = team.get(
        "headshots",
        0,
    )

    result_text = (
        "WINNER"
        if won
        else "LOSER"
    )

    print()
    print(
        f"{name} "
        f"| Team ID: {team_id}"
    )

    print(
        f"  Result: {result_text}"
        f" | Series score: {score}"
        f" | Kills: {kills}"
        f" | Deaths: {deaths}"
        f" | Assists: {assists}"
        f" | Headshots: {headshots}"
    )

    players = team.get(
        "players",
        [],
    )

    if not isinstance(players, list):
        return

    print()
    print("  Players:")

    for player in players:
        if not isinstance(player, dict):
            continue

        player_name = player.get(
            "name",
            "Unknown player",
        )

        player_id = player.get(
            "id",
            "Unknown",
        )

        participation = player.get(
            "participationStatus",
            "UNKNOWN",
        )

        player_kills = player.get(
            "kills",
            0,
        )

        player_deaths = player.get(
            "deaths",
            0,
        )

        assists_given = player.get(
            "killAssistsGiven",
            0,
        )

        assists_received = player.get(
            "killAssistsReceived",
            0,
        )

        headshots = player.get(
            "headshots",
            0,
        )

        print(
            f"    {str(player_name):<20}"
            f" ID: {str(player_id):<8}"
            f" K: {player_kills:<3}"
            f" D: {player_deaths:<3}"
            f" A: {assists_given:<3}"
            f" AR: {assists_received:<3}"
            f" HS: {headshots:<3}"
            f" {participation}"
        )

def safe_ratio(
    numerator: int | float,
    denominator: int | float,
) -> float:
    """
    Divide two values without crashing on zero.
    """

    if denominator == 0:
        return 0.0

    return numerator / denominator


def display_game_player(
    player: dict[str, Any],
    round_count: int,
) -> None:
    """
    Print one player's map-level statistics.
    """

    name = str(
        player.get(
            "name",
            "Unknown player",
        )
    )

    player_id = str(
        player.get(
            "id",
            "Unknown",
        )
    )

    kills = int(
        player.get(
            "kills",
            0,
        )
    )

    deaths = int(
        player.get(
            "deaths",
            0,
        )
    )

    assists = int(
        player.get(
            "killAssistsGiven",
            0,
        )
    )

    headshots = int(
        player.get(
            "headshots",
            0,
        )
    )

    damage_dealt = int(
        player.get(
            "damageDealt",
            0,
        )
    )

    damage_taken = int(
        player.get(
            "damageTaken",
            0,
        )
    )

    kd_ratio = safe_ratio(
        kills,
        deaths,
    )

    adr = calculate_adr(
        damage_dealt,
        round_count,
    )

    print(
        f"      {name:<18}"
        f" ID: {player_id:<18}"
        f" K: {kills:<3}"
        f" D: {deaths:<3}"
        f" A: {assists:<3}"
        f" HS: {headshots:<3}"
        f" DMG: {damage_dealt:<5}"
        f" ADR: {adr:<6.2f}"
        f" K/D: {kd_ratio:.2f}"
    )


def display_game_team(
    team: dict[str, Any],
    round_count: int,
) -> None:
    """
    Print one team's map-level statistics.
    """

    name = str(
        team.get(
            "name",
            "Unknown team",
        )
    )

    score = team.get(
        "score",
        "Unknown",
    )

    won = bool(
        team.get(
            "won",
            False,
        )
    )

    kills = int(
        team.get(
            "kills",
            0,
        )
    )

    deaths = int(
        team.get(
            "deaths",
            0,
        )
    )

    damage_dealt = int(
        team.get(
            "damageDealt",
            0,
        )
    )

    damage_taken = int(
        team.get(
            "damageTaken",
            0,
        )
    )

    team_adr = calculate_adr(
        damage_dealt,
        round_count,
    )

    result = (
        "WINNER"
        if won
        else "LOSER"
    )

    print()
    print(
        f"    {name}"
        f" | {result}"
        f" | Score: {score}"
        f" | K: {kills}"
        f" | D: {deaths}"
        f" | Damage: {damage_dealt}"
        f" | Team ADR: {team_adr:.2f}"
        f" | Taken: {damage_taken}"
    )

    players = team.get(
        "players",
        [],
    )

    if not isinstance(players, list):
        return

    for player in players:
        if isinstance(player, dict):
            display_game_player(
                player,
                round_count,
            )

def get_finished_rounds(
    game: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Return only completed round segments.

    GRID may include other segment types, so we do not count
    every segment automatically.
    """

    segments = game.get(
        "segments",
        [],
    )

    if not isinstance(segments, list):
        return []

    finished_rounds: list[dict[str, Any]] = []

    for segment in segments:
        if not isinstance(segment, dict):
            continue

        segment_type = str(
            segment.get(
                "type",
                "",
            )
        ).strip().lower()

        finished = bool(
            segment.get(
                "finished",
                False,
            )
        )

        if finished and segment_type == "round":
            finished_rounds.append(segment)

    return finished_rounds


def calculate_adr(
    damage_dealt: int | float,
    round_count: int,
) -> float:
    """
    Calculate average damage per round.
    """

    if round_count <= 0:
        return 0.0

    return float(damage_dealt) / round_count


def display_round(
    segment: dict[str, Any],
) -> None:
    """
    Print a compact summary for one completed round.
    """

    sequence_number = segment.get(
        "sequenceNumber",
        "?",
    )

    teams = segment.get(
        "teams",
        [],
    )

    if not isinstance(teams, list):
        teams = []

    winner_name = "Unknown"
    winner_side = "Unknown"
    win_type = "Unknown"

    for team in teams:
        if not isinstance(team, dict):
            continue

        if bool(team.get("won", False)):
            winner_name = str(
                team.get(
                    "name",
                    "Unknown",
                )
            )

            winner_side = str(
                team.get(
                    "side",
                    "Unknown",
                )
            )

            win_type = str(
                team.get(
                    "winType",
                    "",
                )
                or "Unknown"
            )

            break

    print(
        f"      Round {sequence_number:<3}"
        f" Winner: {winner_name:<18}"
        f" Side: {winner_side:<18}"
        f" Type: {win_type}"
    )


def display_round_summary(
    game: dict[str, Any],
) -> None:
    """
    Print the completed round count and round winners.
    """

    rounds = get_finished_rounds(game)

    print()
    print(
        f"    Completed rounds: {len(rounds)}"
    )

    for segment in sorted(
        rounds,
        key=lambda round_state: round_state.get(
            "sequenceNumber",
            0,
        ),
    ):
        display_round(segment)

def display_game(
    game: dict[str, Any],
) -> None:
    """
    Print one map and its team/player statistics.
    """

    sequence_number = game.get(
        "sequenceNumber",
        "?",
    )

    map_data = game.get(
        "map",
        {},
    )

    if not isinstance(map_data, dict):
        map_data = {}

    map_name = str(
        map_data.get(
            "name",
            "Unknown map",
        )
    )

    finished = bool(
        game.get(
            "finished",
            False,
        )
    )

    duration = game.get(
        "duration",
        "Unknown",
    )

    finished_rounds = get_finished_rounds(
        game
    )

    round_count = len(
        finished_rounds
    )

    print()
    print("-" * 80)

    print(
        f"Map {sequence_number}: {map_name}"
        f" | Finished: {finished}"
        f" | Duration: {duration}"
        f" | Rounds: {round_count}"
    )

    print("-" * 80)

    teams = game.get(
        "teams",
        [],
    )

    if isinstance(teams, list):
        for team in teams:
            if isinstance(team, dict):
                display_game_team(
                    team,
                    round_count,
                )

    display_round_summary(game)

def display_series_state(
    series_state: dict[str, Any],
) -> None:
    """
    Print the important information from one state.
    """

    series_id = series_state.get(
        "id",
        "Unknown",
    )

    version = series_state.get(
        "version",
        "Unknown",
    )

    series_format = series_state.get(
        "format",
        "Unknown",
    )

    started = series_state.get(
        "started",
        False,
    )

    finished = series_state.get(
        "finished",
        False,
    )

    forfeited = series_state.get(
        "forfeited",
        False,
    )

    valid = series_state.get(
        "valid",
        False,
    )

    started_at = series_state.get(
        "startedAt",
        None,
    )

    updated_at = series_state.get(
        "updatedAt",
        None,
    )

    games = series_state.get(
        "games",
        [],
    )

    if not isinstance(games, list):
        games = []

    teams = series_state.get(
        "teams",
        [],
    )

    if not isinstance(teams, list):
        teams = []

    print()
    print("=" * 80)

    print(
        f"Series {series_id}"
    )

    print("=" * 80)

    print(
        f"Format: {series_format}"
    )

    print(
        f"Data model version: {version}"
    )

    print(
        f"Started: {started}"
        f" | Finished: {finished}"
        f" | Valid: {valid}"
    )

    print(
        f"Started at: {started_at}"
    )

    print(
        f"Updated at: {updated_at}"
    )

    print(
        f"Games/maps returned: {len(games)}"
    )

    if games:
        print()
        print("Map-level statistics:")

        sorted_games = sorted(
            games,
            key=lambda game: game.get(
                "sequenceNumber",
                0,
            ),
        )

        for game in sorted_games:
            if isinstance(game, dict):
                display_game(game)


def summarize_for_duplicate_check(
    series_state: dict[str, Any],
) -> dict[str, Any]:
    """
    Create a compact record used to compare duplicate IDs.
    """

    teams = series_state.get(
        "teams",
        [],
    )

    if not isinstance(teams, list):
        teams = []

    games = series_state.get(
        "games",
        [],
    )

    if not isinstance(games, list):
        games = []

    team_names = sorted(
        str(team.get("name", "Unknown"))
        for team in teams
        if isinstance(team, dict)
    )

    return {
        "series_id": str(
            series_state.get(
                "id",
                "Unknown",
            )
        ),

        "teams": team_names,

        "started": bool(
            series_state.get("started")
        ),

        "finished": bool(
            series_state.get("finished")
        ),

        "valid": bool(
            series_state.get("valid")
        ),

        "started_at": series_state.get(
            "startedAt"
        ),

        "updated_at": series_state.get(
            "updatedAt"
        ),

        "game_count": len(games),

        "player_count": len(
            extract_players(series_state)
        ),
    }


def display_duplicate_summary(
    summaries: list[dict[str, Any]],
) -> None:
    """
    Print a compact table comparing duplicate candidates.
    """

    print()
    print("=" * 110)
    print("DUPLICATE SERIES STATE CHECK")
    print("=" * 110)

    header = (
        f"{'SERIES ID':<12}"
        f"{'VALID':<8}"
        f"{'STARTED':<10}"
        f"{'FINISHED':<11}"
        f"{'GAMES':<8}"
        f"{'PLAYERS':<10}"
        f"{'TEAMS'}"
    )

    print(header)
    print("-" * 110)

    for summary in summaries:
        teams_text = " vs ".join(
            summary["teams"]
        )

        print(
            f"{summary['series_id']:<12}"
            f"{str(summary['valid']):<8}"
            f"{str(summary['started']):<10}"
            f"{str(summary['finished']):<11}"
            f"{summary['game_count']:<8}"
            f"{summary['player_count']:<10}"
            f"{teams_text}"
        )


def parse_arguments() -> argparse.Namespace:
    """
    Parse terminal arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Retrieve and inspect GRID Series State "
            "for completed Counter-Strike matches."
        )
    )

    parser.add_argument(
        "--series",
        action="append",
        dest="series_ids",
        help=(
            "GRID series ID to retrieve. "
            "May be supplied more than once."
        ),
    )

    parser.add_argument(
        "--duplicates",
        action="store_true",
        help=(
            "Check the eight suspected duplicate "
            "Austin Stage 2 records."
        ),
    )

    return parser.parse_args()


def determine_series_ids(
    arguments: argparse.Namespace,
) -> list[str]:
    """
    Determine which series IDs should be requested.
    """

    if arguments.duplicates:
        return list(
            DUPLICATE_CANDIDATE_IDS
        )

    if arguments.series_ids:
        return [
            str(series_id).strip()
            for series_id in arguments.series_ids
            if str(series_id).strip()
        ]

    return [DEFAULT_SERIES_ID]


def main() -> None:
    arguments = parse_arguments()

    series_ids = determine_series_ids(
        arguments
    )

    print(
        f"Retrieving GRID Series State for "
        f"{len(series_ids)} series..."
    )

    successful_states: list[
        dict[str, Any]
    ] = []

    failed_series: list[
        dict[str, str]
    ] = []

    with GridClient() as client:
        for index, series_id in enumerate(
            series_ids,
            start=1,
        ):
            print()
            print(
                f"[{index}/{len(series_ids)}] "
                f"Requesting series {series_id}..."
            )

            try:
                series_state = fetch_series_state(
                    client,
                    series_id,
                )

            except (
                GridClientError,
                RuntimeError,
            ) as error:
                print(
                    f"Series {series_id} failed: "
                    f"{error}"
                )

                failed_series.append(
                    {
                        "series_id": series_id,
                        "error": str(error),
                    }
                )

                continue

            successful_states.append(
                series_state
            )

            output_path = save_json(
                f"{series_id}.json",
                series_state,
            )

            display_series_state(
                series_state
            )

            print()
            print(
                f"Saved state to:\n"
                f"{output_path}"
            )

    if arguments.duplicates:
        duplicate_summaries = [
            summarize_for_duplicate_check(
                state
            )
            for state in successful_states
        ]

        display_duplicate_summary(
            duplicate_summaries
        )

        comparison_path = save_json(
            "austin_stage_2_duplicate_check.json",
            {
                "successful": duplicate_summaries,
                "failed": failed_series,
            },
        )

        print()
        print(
            f"Duplicate comparison saved to:\n"
            f"{comparison_path}"
        )

    if failed_series:
        print()
        print("=" * 80)

        print(
            f"Failed series requests: "
            f"{len(failed_series)}"
        )

        for failure in failed_series:
            print(
                f"- {failure['series_id']}: "
                f"{failure['error']}"
            )

    if not successful_states:
        raise SystemExit(1)


if __name__ == "__main__":
    main()