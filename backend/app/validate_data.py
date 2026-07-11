import json
from collections import Counter
from pathlib import Path
from datetime import date, timedelta, datetime

DATA_FILE = Path(__file__).parent / "data" / "players.json"

REQUIRED_FIELDS = {
    "player_id",
    "name",
    "team",
    "year",
    "period_start",
    "period_end",
    "maps_played",
    "round_swing",
    "rating",
    "adr",
    "kast",
    "primary_role",
    "secondary_roles",
    "stat_scope",
    "source",
    "updated_at",
}
ALLOWED_YEARS = {2024, 2025, 2026}
RATING_CAP = 4.0
ROUND_SWING_CAP = 4.0 
ALLOWED_ROLES = {"awper", "igl", "rifler", "flex", "anchor", "entry"}
errors = []

def loadplayers():
    if not DATA_FILE.exists():
        errors.append(f"Data file {DATA_FILE} does not exist.")
        raise FileNotFoundError(f"Data file {DATA_FILE} does not exist.")

    
    with DATA_FILE.open("r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError as e:
            errors.append(f"JSON decode error: {e}")
            raise ValueError(f"JSON decode error: {e}")
        
        if not isinstance(data, list):
            errors.append("Data is not a list of players.")
            raise ValueError("Data is not a list of players.")
        
        #need to add more file loading checks like invisible charcters, and other things that could break the code
    return data


def validate_data():
    players = loadplayers()
    #main check for missing fields and invalid data types
    seen_ids = set()
    for index, player in enumerate(players):
        player_id = player.get('player_id', 'unknown')
        # checks if the player is a dictionary and if the secondary_roles field is a list

        if not isinstance(player, dict):
            errors.append(f"Player {player_id} does not have a valid dictionary structure | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player.get('player_id', 'unkown')} does not have a valid dictionary structure | line {players.index(player) + 1}")
            continue
        
        if not isinstance(player.get('secondary_roles', []), list):
            errors.append(f"Player {player_id} does not have a valid list for the secondary_roles field | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} does not have a valid list for the secondary_roles field | line {players.index(player) + 1}")
            continue

        # Check for missing required fields

        missing_fields = REQUIRED_FIELDS - player.keys()
        if missing_fields:
            errors.append(f"Player {player_id} is missing fields: {missing_fields} | line {players.index(player) + 1}")
            #raise KeyError(f"Player {player_id} is missing fields: {missing_fields} | line {players.index(player) + 1}")
            continue

        #**************************************                 VALIDATION CHECKS FOR EACH FIELD, CHECKS IF THE FIELD IS THE CORRECT TYPE AND IF IT IS EMPTY OR NOT                     ************************************** ##

        if not isinstance(player.get('player_id'), str) or len(player.get('player_id').strip()) == 0:
            errors.append(f"Player {player_id} has an invalid type for player_id, expected str | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for player_id, expected str | line {players.index(player) + 1}")

        if player.get('player_id') in seen_ids:
            errors.append(f"Player {player_id} has a duplicate ID | line {players.index(player) + 1}")
        else:
            if player.get('player_id') != player.get('player_id').lower():
                errors.append(f"Player {player_id} does not have a uniform lower case player id.")

            seen_ids.add(player.get('player_id'))

        if not isinstance(player.get('name'), str) or len(player.get('name').strip()) == 0:
            errors.append(f"Player {player_id} has an invalid type for name, expected str | line {players.index(player) + 1}")
            # raise TypeError(f"Player {player_id} has an invalid type for name, expected str | line {players.index(player) + 1}")

        if not isinstance(player.get('team'), str) or len(player.get('team').strip()) == 0:
            errors.append(f"Player {player_id} has an invalid type for team, expected str | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for team, expected str | line {players.index(player) + 1}")

        if not isinstance(player.get('year'), (int, float)) or len(str(player.get('year')).strip()) == 0:
            errors.append(f"Player {player_id} has an invalid type for year, expected int or float | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for year, expected int or float | line {players.index(player) + 1}")
        if player.get('year') not in ALLOWED_YEARS: errors.append(f"Player {player.get('player_id')} has a year not allowed within current restrictions | line {players.index(player) + 1}")


        

        if not isinstance(player.get('period_start'), str):
            errors.append(f"Player {player_id} has an invalid type for period_start, expected str | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for period_start, expected str | line {players.index(player) + 1}")

        if not isinstance(player.get('period_end'), str) or len(player.get("period_end").strip()) == 0:
            errors.append(f"Player {player_id} has an invalid type for period_end, expected str | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for period_end, expected str | line {players.index(player) + 1}")
        
        try:
            period_start = date.fromisoformat(player.get("period_start"))
            period_end = date.fromisoformat(player.get("period_end"))
            updated_at = date.fromisoformat(player.get("updated_at"))

        except (ValueError, TypeError):
            errors.append(
                f"Player {player.get('player_id', 'unknown')} "
                f"has an incorrectly formatted or empty date "
                f"| line {index + 1}"
            )
            continue

        #if date.fromisoformat(player.get('period_start')) >= date.fromisoformat(player.get('period_end')):
        if not date.fromisoformat(player.get('period_start')) <= date.fromisoformat(player.get('period_end')):
            errors.append(f"Player {player.get('player_id')} has invalid years, the start is not before the end | line {players.index(player) + 1}")

        # need to add a check to make sure that the period is contained withing the team year
        

        #********************************************************************* INTS FLOATS ***********************************************************************************# 

        if not isinstance(player.get('maps_played'), (int, float)):
            errors.append(f"Player {player_id} has an invalid type for maps_played, expected int or float | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for maps_played, expected int or float | line {players.index(player) + 1}")
        if player.get('maps_played') < 0:
            errors.append(f"Player {player.get('player_id')} has less than 0 maps played | line {players.index(player) + 1}")

        if not isinstance(player.get('round_swing'), (int, float)):
            errors.append(f"Player {player_id} has an invalid type for round_swing, expected int or float | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for round_swing, expected int or float | line {players.index(player) + 1}")
        if player.get('round_swing') > ROUND_SWING_CAP:
            errors.append(f"player {player.get('player_id')} has a round swing outside of allowed range")

        rating = player.get("rating")
        if not isinstance(rating, (int, float)):
            errors.append(f"Player {player_id} has an invalid type for rating, expected int for float | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for rating, expected int or float | line {players.index(player) + 1}")
        elif rating > RATING_CAP:
            errors.append(f"player {player.get('player_id')} has a rating outside of allowed range")
            
        adr = player.get('adr')
        if not isinstance(adr, (int, float)):
            errors.append(f"Player {player_id} has an invalid type for adr, expected int or float | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for adr, expected int or float | line {players.index(player) + 1}")
        elif adr < 0:
            errors.append(f"Player {player.get('player_id')} has less than 0 adr played | line {players.index(player) + 1}")

        kast = player.get('kast')
        if not isinstance(kast, (int, float)):
            errors.append(f"Player {player_id} has an invalid type for kast, expected int or float | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for kast, expected int or float | line {players.index(player) + 1}")
        if player.get('kast') < 0 or player.get('kast') > 100:
            errors.append(f"Player {player_id} has a value for kast outside of allowed range | line {players.index(player) + 1}")

        if not isinstance(player.get('primary_role'), str) or len(player.get("primary_role").strip()) == 0:
            errors.append(f"Player {player_id} has an invalid type for primary_role, expected str | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for primary_role, expected str | line {players.index(player) + 1}")

        if not isinstance(player.get('secondary_roles'), list):
            errors.append(f"Player {player_id} has an invalid type for secondary_roles, expected list | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for secondary_roles, expected list | line {players.index(player) + 1}")
            

        if not isinstance(player.get('stat_scope'), str) or len(player.get('stat_scope').strip()) == 0:
            errors.append(f"Player {player_id} has an invalid type for stat_scope, expected str | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for stat_scope, expected str | line {players.index(player) + 1}")

        if not isinstance(player.get('source'), str) or len(player.get('source').strip()) == 0:
            errors.append(f"Player {player_id} has an invalid type for source, expected str | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for source, expected str | line {players.index(player) + 1}")

        if not isinstance(player.get('updated_at'), str):
            errors.append(f"Player {player_id} has an invalid type for updated_at, expected str | line {players.index(player) + 1}")
            #raise TypeError(f"Player {player_id} has an invalid type for updated_at, expected str | line {players.index(player) + 1}")

        if player.get('primary_role') not in ALLOWED_ROLES:
            errors.append(f"Player {player.get("player_id")} does not have an allowed primary role | line {players.index(player) + 1}")
            for role in player.get('secondary_roles'):
                if role not in ALLOWED_ROLES:
                    errors.append(f"Player {player.get('player_id')} has a secondary role that is not allowed | line {players.index(player) + 1}")
                if not isinstance(role, str):
                    errors.append(f"Player {player.get('player_id')} has a non string inside of their secondary roles | line {players.index(player) + 1}")
                if role == player.get('primary_role'):
                    errors.append(f"Player {player.get('player_id')} has their current primary role located in their secondary roles | line {players.index(player) + 1}")


        
        unexpected_fields = player.keys() - REQUIRED_FIELDS

        if unexpected_fields:
            errors.append(
                f"Player {player.get('player_id', 'unknown')} "
                f"has unexpected fields: {unexpected_fields} "
                f"| line {index + 1}"
            )

    return errors

                        
            
def main():
    validation_errors = validate_data()

    if validation_errors:
        for error in validation_errors:
            print(error)
    else:
        print("Validation passed.")

if __name__ == "__main__":
    main()



        


