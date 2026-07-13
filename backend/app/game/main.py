from .data import (
    get_team_year_options,
    load_players,
)

from .draft import (
    create_game_state,
    reroll_current_team,
    reroll_current_year,
    select_player,
    start_round,
)


COLUMN_WIDTH = 24
PLAYER_TABLE_WIDTH = 4 + (COLUMN_WIDTH * 3)
TEAM_TABLE_WIDTH = 4 + (COLUMN_WIDTH * 4)


def format_number(value, decimals=2):
    """
    Safely format a number for terminal display.
    """

    if isinstance(value, (int, float)):
        return f"{value:.{decimals}f}"

    return "Unknown"


def display_players(players):
    """
    Display the current player options.
    """

    print()

    print(
        f"{'#'.center(4)}"
        f"{'PLAYER'.center(COLUMN_WIDTH)}"
        f"{'PRIMARY ROLE'.center(COLUMN_WIDTH)}"
        f"{'RATING'.center(COLUMN_WIDTH)}"
    )

    print("-" * PLAYER_TABLE_WIDTH)

    for number, player in enumerate(
        players,
        start=1,
    ):
        name = player.get("name", "Unknown")
        role = player.get(
            "primary_role",
            "Unknown",
        )

        rating = format_number(
            player.get("rating"),
            2,
        )

        print(
            f"{str(number).center(4)}"
            f"{name.center(COLUMN_WIDTH)}"
            f"{role.center(COLUMN_WIDTH)}"
            f"{rating.center(COLUMN_WIDTH)}"
        )


def ask_yes_or_no(message):
    """
    Continue asking until the user enters yes or no.
    """

    while True:
        answer = input(message).strip().lower()

        if answer in {"yes", "y"}:
            return True

        if answer in {"no", "n"}:
            return False

        print("Please enter yes or no.")


def ask_for_reroll(
    game_state,
    players,
    options,
):
    """
    Ask whether the player wants to use the reroll.

    Returns:
        Updated game state
        Whether a reroll occurred this round
    """

    if not game_state["reroll_available"]:
        print("\nReroll: already used")
        return game_state, False

    wants_reroll = ask_yes_or_no(
        "\nWould you like to use your reroll? "
        "yes or no: "
    )

    if not wants_reroll:
        return game_state, False

    while True:
        reroll_choice = input(
            "Would you like to reroll "
            "the team or year? "
        ).strip().lower()

        if reroll_choice == "team":
            game_state = reroll_current_team(
                game_state,
                players,
                options,
            )

            return game_state, True

        if reroll_choice == "year":
            game_state = reroll_current_year(
                game_state,
                players,
                options,
            )

            return game_state, True

        print(
            "Please enter either 'team' or 'year'."
        )


def ask_for_player_selection(game_state):
    """
    Ask the user to select one available player.

    Returns the selected player's ID.
    """

    available_players = (
        game_state["available_players"]
    )

    while True:
        try:
            choice = int(
                input(
                    "\nWho would you like to pick? "
                    f"(1-{len(available_players)}): "
                )
            )

            if (
                1
                <= choice
                <= len(available_players)
            ):
                selected_player = (
                    available_players[choice - 1]
                )

                return selected_player.get(
                    "player_id"
                )

            print(
                "That number is outside "
                "the available choices."
            )

        except ValueError:
            print("Please enter a number.")


def display_completed_team(selected_players):
    """
    Display the completed five-player roster.
    """

    print()
    print("=" * TEAM_TABLE_WIDTH)
    print(
        "YOUR COMPLETED TEAM".center(
            TEAM_TABLE_WIDTH
        )
    )
    print("=" * TEAM_TABLE_WIDTH)

    print(
        f"{'#'.center(4)}"
        f"{'PLAYER'.center(COLUMN_WIDTH)}"
        f"{'TEAM / YEAR'.center(COLUMN_WIDTH)}"
        f"{'PRIMARY ROLE'.center(COLUMN_WIDTH)}"
        f"{'SECONDARY'.center(COLUMN_WIDTH)}"
    )

    print("-" * TEAM_TABLE_WIDTH)

    for number, player in enumerate(
        selected_players,
        start=1,
    ):
        name = player.get("name", "Unknown")

        team_year = (
            f"{player.get('team', 'Unknown')} "
            f"{player.get('year', 'Unknown')}"
        )

        primary_role = player.get(
            "primary_role",
            "Unknown",
        )

        secondary_roles = ", ".join(
            player.get("secondary_roles", [])
        )

        if not secondary_roles:
            secondary_roles = "None"

        print(
            f"{str(number).center(4)}"
            f"{name.center(COLUMN_WIDTH)}"
            f"{team_year.center(COLUMN_WIDTH)}"
            f"{primary_role.center(COLUMN_WIDTH)}"
            f"{secondary_roles.center(COLUMN_WIDTH)}"
        )

        rating_text = (
            "Rating: "
            + format_number(
                player.get("rating"),
                2,
            )
        )

        adr_text = (
            "ADR: "
            + format_number(
                player.get("adr"),
                1,
            )
        )

        kast_text = (
            "KAST: "
            + format_number(
                player.get("kast"),
                1,
            )
            + "%"
        )

        round_swing = player.get(
            "round_swing"
        )

        if isinstance(
            round_swing,
            (int, float),
        ):
            round_swing_text = (
                f"Round Swing: "
                f"{round_swing:+.2f}%"
            )

        else:
            round_swing_text = (
                "Round Swing: Unknown"
            )

        print(
            f"{''.center(4)}"
            f"{rating_text.center(COLUMN_WIDTH)}"
            f"{adr_text.center(COLUMN_WIDTH)}"
            f"{kast_text.center(COLUMN_WIDTH)}"
            f"{round_swing_text.center(COLUMN_WIDTH)}"
        )

        print("-" * TEAM_TABLE_WIDTH)


def display_round_header(game_state):
    """
    Display the current draft-round information.
    """

    reroll_text = (
        "Available"
        if game_state["reroll_available"]
        else "Used"
    )

    title = (
        f"Draft Round "
        f"{game_state['round_number']} of 5"
        f" | Reroll: {reroll_text}"
    )

    print()
    print("=" * PLAYER_TABLE_WIDTH)
    print(title.center(PLAYER_TABLE_WIDTH))
    print("=" * PLAYER_TABLE_WIDTH)


def main():
    players = load_players()

    options = get_team_year_options(
        players
    )

    game_state = create_game_state()

    while not game_state["game_complete"]:
        display_round_header(game_state)

        game_state = start_round(
            game_state,
            players,
            options,
        )

        rolled_team = str(
            game_state["current_team"]
        ).upper()

        rolled_year = game_state["current_year"]

        print(
            f"\nYou rolled "
            f"{rolled_team}, {rolled_year}"
        )

        # Show the original options before asking
        # whether the player wants to reroll.
        display_players(
            game_state["available_players"]
        )

        game_state, rerolled = ask_for_reroll(
            game_state,
            players,
            options,
        )

        if rerolled:
            new_team = str(
                game_state["current_team"]
            ).upper()

            new_year = (
                game_state["current_year"]
            )

            print(
                f"\nYour new roll is "
                f"{new_team}, {new_year}"
            )

            display_players(
                game_state[
                    "available_players"
                ]
            )

        selected_player_id = (
            ask_for_player_selection(
                game_state
            )
        )

        game_state, selected_player = (
            select_player(
                game_state,
                selected_player_id,
            )
        )

        print(
            f"\nYou selected "
            f"{selected_player.get('name')} "
            f"from "
            f"{selected_player.get('team')} "
            f"{selected_player.get('year')}."
        )

    display_completed_team(
        game_state["selected_players"]
    )


if __name__ == "__main__":
    main()