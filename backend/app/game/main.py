from .data import load_players, get_team_year_options
from .draft import play_draft_round

game_state = {
    "round_number": 1,
    "reroll_available": True,
    "current_team": None,
    "current_year": None,
    "selected_players": []
}

def main():
    players = load_players()
    options = get_team_year_options(players)

    reroll_available = True
    reroll_text = "Available" if reroll_available else "Used"
    selected_players = []
    for round_number in range(1, 6):
        print(
            f"\n{'=' * 60}\n"
            f"Draft Round {round_number} of 5 "
            f"| Reroll Available: {reroll_text}\n"
            f"{'=' * 60}"
        )
        
        selected_player, reroll_available = play_draft_round(players, options, reroll_available)

        print(
            f"\nSelected: {selected_player.get('name')} "
            f"| {selected_player.get('team')} "
            f"{selected_player.get('year')} "
            f"| {selected_player.get('primary_role')}"
        )
        selected_players.append(selected_player)

    print("\n===================== Your Completed Team ======================")

    for num, player in enumerate(selected_players, start=1):
        team = player.get('team').center(24)
        name = player.get('name').center(24)
        role = player.get('primary_role').center(24)
        secRole = player.get('secondary_roles')
        swing = player.get('round_swing').center(24)
        rating = player.get('rating').center(24)
        adr = player.get('adr').center(24)
        kast = player.get('kast').center(24)

        secondary_roles = ", ".join(player.get("secondary_roles", []))

        print(
            f"{num}. {player.get('name')} "
            f"| {player.get('team')} {player.get('year')} "
            f"| Primary: {player.get('primary_role')} "
            f"| Secondary: {secondary_roles or 'None'} "
            f"| Rating: {player.get('rating'):.2f} "
            f"| ADR: {player.get('adr'):.1f} "
            f"| KAST: {player.get('kast'):.1f}% "
            f"| Round Swing: {player.get('round_swing'):+.2f}%"
        )


    


if __name__ == "__main__":
    main()