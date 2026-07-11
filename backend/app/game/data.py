import json
from pathlib import Path
import random

DATA_FILE = Path(__file__).parent.parent / "data" / "players.json"

def load_players():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        loaded_players = json.load(file)
    return loaded_players

def get_team_year_options(players):
    options = set()
    for player in players:
        ty_tuple = tuple((player.get('team'), player.get('year')))
        options.add(ty_tuple)

    return options


def get_players_for_team_year(players, team, year):
    players_for_team_year = []
    for player in players:
        if player.get('team') == team and player.get('year') == year:
            players_for_team_year.append(player)
    return players_for_team_year

def roll_team_year(options):
    return random.choice(list(options))

def get_team_reroll_options(options, current_team, current_year):
    reroll_options = []

    for team, year in options:
        if year == current_year and team != current_team:
            reroll_options.append((team, year))
    
    return reroll_options

def get_year_reroll_options(options, current_team, current_year):
    reroll_options = []

    for team, year in options:
        if year != current_year and team == current_team:
            reroll_options.append((team, year))
    
    return reroll_options

def reroll_team(options, current_team, current_year):
    reroll_options = get_team_reroll_options(options, current_team, current_year)
    return random.choice(reroll_options)

def reroll_year(options, current_team, current_year):
    reroll_options = get_year_reroll_options(options, current_team, current_year)
    return random.choice(reroll_options)

def test_team_reroll(options):
    for _ in range(100):
        current_team, current_year = roll_team_year(options)

        possible_rerolls = [
            options
            for option in options
            if option[1] == current_year
            and option[0] != current_team
        ]

        if possible_rerolls:
            new_team, new_year = reroll_team(
                options, 
                current_team,
                current_year
            )

            assert new_year == current_year
            assert new_team != current_team
            assert (new_team, new_year) in options
    print("Team reroll test passed.")

def test_year_reroll(options):
    for _ in range(100):
        current_team, current_year = roll_team_year(options)

        possible_rerolls = [
            option
            for option in options
            if option[0] == current_team
            and option[1] != current_year
        ]

        if possible_rerolls:
            new_team, new_year = reroll_year(
                options,
                current_team,
                current_year
            )

            assert new_team == current_team
            assert new_year != current_year
            assert (new_team, new_year) in options

    print("Year reroll test passed.")

def main(): 
    players = load_players()
    options = get_team_year_options(players)

    test_team_reroll(options)
    test_year_reroll(options)

if __name__ == "__main__":
    main()