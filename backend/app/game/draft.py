from .data import *
def display_players(players):
    for number, player in enumerate(players, start=1):
        print(
            f"{number}. {player.get('name')} "
            f"| {player.get('primary_role')} "
            f"| Rating: {player.get('rating')}"
        )

def play_draft_round(players, options, reroll_available):
    current_team, current_year = roll_team_year(options)

    print(f"You rolled {current_team.upper()}, {current_year}")

    # Ask whether the user wants to keep, reroll team,
    # or reroll year.

    # If a reroll is used:
    # update current_team/current_year
    # set reroll_available to False

    available_players = get_players_for_team_year(
        players,
        current_team,
        current_year
    )


    # Display players
    # Ask the user to select one
    # Return selected player and reroll_available

    if reroll_available:
        use_reroll = input(f"Would you like to use your reroll yes or no? ")
        if use_reroll == "yes":
            reroll_available = False
            team_or_year = str(input(f"would you like to reroll team or year? "))
            if team_or_year == "team":
                current_team, current_year = reroll_team(
                    options,
                    current_team,
                    current_year
                    )
                print(f'New Team: {current_team} | Current Year: {current_year}')
            elif team_or_year == "year":
                current_team, current_year = reroll_year(
                    options,
                    current_team,
                    current_year
                )
                print(f'Current Team: {current_team} | New Year: {current_year}')
            else:
                use_reroll = str(input(f"\n Would you like to use your reroll yes or no? "))
        elif use_reroll == "no":
            available_players = get_players_for_team_year(
                    players,
                    current_team,
                    current_year
                )
            
    if not reroll_available:
        available_players = get_players_for_team_year(
            players,
            current_team,
            current_year
        )

    display_players(available_players)
    while (True):
        try:
            player_selected = int(input(f'\nWho would you like to pick? (1-{len(available_players)}): '))
            if 1 <= player_selected <= len(available_players):
                break
            
            print("That number is outside the available choices.")

        except ValueError:
            print("Please enter a number.")
    
    selected_player = available_players[player_selected - 1]



    return selected_player, reroll_available
