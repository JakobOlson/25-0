from .data import (
    get_players_for_team_year,
    reroll_team,
    reroll_year,
    roll_team_year,
)


DRAFT_SIZE = 5


def create_game_state():
    """
    Create and return a new game's starting state.
    """

    return {
        "round_number": 1,
        "reroll_available": True,
        "current_team": None,
        "current_year": None,
        "available_players": [],
        "selected_players": [],
        "game_complete": False,
    }


def start_round(game_state, players, options):
    """
    Start a draft round by rolling a team and year.
    """

    if game_state["game_complete"]:
        raise ValueError(
            "The game is complete. Another round cannot begin."
        )

    current_team, current_year = roll_team_year(options)

    available_players = get_players_for_team_year(
        players,
        current_team,
        current_year,
    )

    game_state["current_team"] = current_team
    game_state["current_year"] = current_year
    game_state["available_players"] = available_players

    return game_state


def reroll_current_team(game_state, players, options):
    """
    Reroll the current team while keeping the current year.
    """

    if not game_state["reroll_available"]:
        raise ValueError("The reroll has already been used.")

    new_team, same_year = reroll_team(
        options,
        game_state["current_team"],
        game_state["current_year"],
    )

    game_state["current_team"] = new_team
    game_state["current_year"] = same_year

    game_state["available_players"] = (
        get_players_for_team_year(
            players,
            new_team,
            same_year,
        )
    )

    game_state["reroll_available"] = False

    return game_state


def reroll_current_year(game_state, players, options):
    """
    Reroll the current year while keeping the current team.
    """

    if not game_state["reroll_available"]:
        raise ValueError("The reroll has already been used.")

    same_team, new_year = reroll_year(
        options,
        game_state["current_team"],
        game_state["current_year"],
    )

    game_state["current_team"] = same_team
    game_state["current_year"] = new_year

    game_state["available_players"] = (
        get_players_for_team_year(
            players,
            same_team,
            new_year,
        )
    )

    game_state["reroll_available"] = False

    return game_state


def select_player(game_state, player_id):
    """
    Add one available player to the drafted roster.
    """

    selected_player = None

    for player in game_state["available_players"]:
        if player.get("player_id") == player_id:
            selected_player = player
            break

    if selected_player is None:
        raise ValueError(
            f"Player {player_id} is not available this round."
        )

    game_state["selected_players"].append(
        selected_player
    )

    if (
        len(game_state["selected_players"])
        >= DRAFT_SIZE
    ):
        game_state["game_complete"] = True

    else:
        game_state["round_number"] += 1

    # Clear the current roll now that the selection is complete.
    game_state["current_team"] = None
    game_state["current_year"] = None
    game_state["available_players"] = []

    return game_state, selected_player