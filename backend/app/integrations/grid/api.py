from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from grid_client import get_grid_series, get_grid_series_state
from typing import Any

from game.data import (
    get_team_year_options,
    load_players,
)

from game.draft import (
    create_game_state,
    reroll_current_team,
    reroll_current_year,
    select_player,
    start_round,
)


app = FastAPI(
    title="25-0 Counter-Strike Draft API",
    version="0.1.0",
)


players = load_players()
options = get_team_year_options(players)

# Temporary storage for one active game.
current_game = None


class PlayerSelection(BaseModel):
    player_id: str


def require_active_game():
    if current_game is None:
        raise HTTPException(
            status_code=409,
            detail="No active game. Start a game first.",
        )

    return current_game


@app.get("/")
def health_check():
    return {
        "message": "25-0 API is running",
        "player_records": len(players),
        "team_year_options": len(options),
    }


@app.post("/game/start")
def start_game():
    global current_game

    current_game = create_game_state()

    current_game = start_round(
        current_game,
        players,
        options,
    )

    return current_game


@app.get("/game/state")
def get_game_state():
    return require_active_game()


@app.post("/game/reroll/team")
def reroll_game_team():
    global current_game

    require_active_game()

    try:
        current_game = reroll_current_team(
            current_game,
            players,
            options,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return current_game


@app.post("/game/reroll/year")
def reroll_game_year():
    global current_game

    require_active_game()

    try:
        current_game = reroll_current_year(
            current_game,
            players,
            options,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return current_game


@app.post("/game/select")
def select_game_player(selection: PlayerSelection):
    global current_game

    require_active_game()

    try:
        current_game, selected_player = select_player(
            current_game,
            selection.player_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    # Automatically roll the next team/year after a selection.
    if not current_game["game_complete"]:
        current_game = start_round(
            current_game,
            players,
            options,
        )

    return {
        "selected_player": selected_player,
        "game": current_game,
    }

@app.get("/grid/series")
async def list_grid_series(limit: int = 50):
    return await get_grid_series(limit=limit)


@app.get("/grid/series/{series_id}/state")
async def read_grid_series_state(series_id: str):
    return await get_grid_series_state(series_id=series_id)