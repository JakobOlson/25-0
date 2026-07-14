from __future__ import annotations

from typing import Any


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """
    Convert a GRID value to an integer safely.
    """

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_divide(
    numerator: int | float,
    denominator: int | float,
) -> float:
    """
    Divide safely and return zero when the denominator is zero.
    """

    if denominator == 0:
        return 0.0

    return float(numerator) / float(denominator)


def get_finished_rounds(
    game: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Return completed round segments from one map.
    """

    segments = game.get("segments", [])

    if not isinstance(segments, list):
        return []

    return [
        segment
        for segment in segments
        if (
            isinstance(segment, dict)
            and str(
                segment.get("type", "")
            ).lower() == "round"
            and bool(segment.get("finished"))
        )
    ]


def transform_player(
    player: dict[str, Any],
    round_count: int,
) -> dict[str, Any]:
    """
    Transform one map-level player state into a compact record.
    """

    kills = safe_int(
        player.get("kills")
    )

    deaths = safe_int(
        player.get("deaths")
    )

    assists = safe_int(
        player.get("killAssistsGiven")
    )

    assists_received = safe_int(
        player.get("killAssistsReceived")
    )

    headshots = safe_int(
        player.get("headshots")
    )

    damage_dealt = safe_int(
        player.get("damageDealt")
    )

    damage_taken = safe_int(
        player.get("damageTaken")
    )

    return {
        "player_id": str(
            player.get(
                "id",
                "",
            )
        ),

        "name": str(
            player.get(
                "name",
                "Unknown player",
            )
        ),

        "participation_status": str(
            player.get(
                "participationStatus",
                "unknown",
            )
        ),

        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "assists_received": assists_received,
        "headshots": headshots,
        "damage_dealt": damage_dealt,
        "damage_taken": damage_taken,

        "kd_ratio": round(
            safe_divide(
                kills,
                deaths,
            ),
            3,
        ),

        "adr": round(
            safe_divide(
                damage_dealt,
                round_count,
            ),
            2,
        ),

        "kills_per_round": round(
            safe_divide(
                kills,
                round_count,
            ),
            3,
        ),

        "deaths_per_round": round(
            safe_divide(
                deaths,
                round_count,
            ),
            3,
        ),

        "assists_per_round": round(
            safe_divide(
                assists,
                round_count,
            ),
            3,
        ),

        "headshot_percentage": round(
            safe_divide(
                headshots,
                kills,
            ) * 100,
            2,
        ),
    }


def transform_game_team(
    team: dict[str, Any],
    round_count: int,
) -> dict[str, Any]:
    """
    Transform one team's map-level state.
    """

    damage_dealt = safe_int(
        team.get("damageDealt")
    )

    players = team.get(
        "players",
        [],
    )

    if not isinstance(players, list):
        players = []

    transformed_players = [
        transform_player(
            player,
            round_count,
        )
        for player in players
        if isinstance(player, dict)
    ]

    return {
        "team_id": str(
            team.get(
                "id",
                "",
            )
        ),

        "name": str(
            team.get(
                "name",
                "Unknown team",
            )
        ),

        "score": safe_int(
            team.get("score")
        ),

        "won": bool(
            team.get("won")
        ),

        "kills": safe_int(
            team.get("kills")
        ),

        "deaths": safe_int(
            team.get("deaths")
        ),

        "assists": safe_int(
            team.get("killAssistsGiven")
        ),

        "headshots": safe_int(
            team.get("headshots")
        ),

        "damage_dealt": damage_dealt,

        "damage_taken": safe_int(
            team.get("damageTaken")
        ),

        "team_adr": round(
            safe_divide(
                damage_dealt,
                round_count,
            ),
            2,
        ),

        "players": transformed_players,
    }


def transform_game(
    game: dict[str, Any],
) -> dict[str, Any]:
    """
    Transform one GRID game, which represents one CS map.
    """

    finished_rounds = get_finished_rounds(
        game
    )

    round_count = len(
        finished_rounds
    )

    map_data = game.get(
        "map",
        {},
    )

    if not isinstance(map_data, dict):
        map_data = {}

    teams = game.get(
        "teams",
        [],
    )

    if not isinstance(teams, list):
        teams = []

    transformed_teams = [
        transform_game_team(
            team,
            round_count,
        )
        for team in teams
        if isinstance(team, dict)
    ]

    winning_team_id = None

    for team in transformed_teams:
        if team["won"]:
            winning_team_id = team["team_id"]
            break

    return {
        "game_id": str(
            game.get(
                "id",
                "",
            )
        ),

        "sequence_number": safe_int(
            game.get("sequenceNumber")
        ),

        "map_id": str(
            map_data.get(
                "id",
                "",
            )
        ),

        "map_name": str(
            map_data.get(
                "name",
                "Unknown map",
            )
        ),

        "started": bool(
            game.get("started")
        ),

        "finished": bool(
            game.get("finished")
        ),

        "started_at": game.get(
            "startedAt"
        ),

        "duration": game.get(
            "duration"
        ),

        "round_count": round_count,
        "winning_team_id": winning_team_id,
        "teams": transformed_teams,
    }


def transform_series_team(
    team: dict[str, Any],
) -> dict[str, Any]:
    """
    Transform a series-level team record.
    """

    players = team.get(
        "players",
        [],
    )

    if not isinstance(players, list):
        players = []

    return {
        "team_id": str(
            team.get(
                "id",
                "",
            )
        ),

        "name": str(
            team.get(
                "name",
                "Unknown team",
            )
        ),

        "score": safe_int(
            team.get("score")
        ),

        "won": bool(
            team.get("won")
        ),

        "kills": safe_int(
            team.get("kills")
        ),

        "deaths": safe_int(
            team.get("deaths")
        ),

        "assists": safe_int(
            team.get("killAssistsGiven")
        ),

        "assists_received": safe_int(
            team.get("killAssistsReceived")
        ),

        "headshots": safe_int(
            team.get("headshots")
        ),

        "players": [
            {
                "player_id": str(
                    player.get(
                        "id",
                        "",
                    )
                ),

                "name": str(
                    player.get(
                        "name",
                        "Unknown player",
                    )
                ),

                "participation_status": str(
                    player.get(
                        "participationStatus",
                        "unknown",
                    )
                ),

                "kills": safe_int(
                    player.get("kills")
                ),

                "deaths": safe_int(
                    player.get("deaths")
                ),

                "assists": safe_int(
                    player.get(
                        "killAssistsGiven"
                    )
                ),

                "assists_received": safe_int(
                    player.get(
                        "killAssistsReceived"
                    )
                ),

                "headshots": safe_int(
                    player.get("headshots")
                ),
            }
            for player in players
            if isinstance(player, dict)
        ],
    }


def transform_series_state(
    series_state: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert a full GRID Series State response into the compact
    structure that our game will store.
    """

    games = series_state.get(
        "games",
        [],
    )

    if not isinstance(games, list):
        games = []

    transformed_games = [
        transform_game(game)
        for game in games
        if isinstance(game, dict)
    ]

    transformed_games.sort(
        key=lambda game: game[
            "sequence_number"
        ]
    )

    teams = series_state.get(
        "teams",
        [],
    )

    if not isinstance(teams, list):
        teams = []

    transformed_teams = [
        transform_series_team(team)
        for team in teams
        if isinstance(team, dict)
    ]

    winning_team_id = None

    for team in transformed_teams:
        if team["won"]:
            winning_team_id = team["team_id"]
            break

    total_rounds = sum(
        game["round_count"]
        for game in transformed_games
    )

    return {
        "series_id": str(
            series_state.get(
                "id",
                "",
            )
        ),

        "title": str(
            (
                series_state.get(
                    "title",
                    {},
                )
                or {}
            ).get(
                "nameShortened",
                "",
            )
        ),

        "data_model_version": str(
            series_state.get(
                "version",
                "",
            )
        ),

        "format": str(
            series_state.get(
                "format",
                "",
            )
        ),

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

        "duration": series_state.get(
            "duration"
        ),

        "winning_team_id": winning_team_id,
        "map_count": len(transformed_games),
        "round_count": total_rounds,
        "teams": transformed_teams,
        "games": transformed_games,
    }