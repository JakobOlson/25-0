from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .transform_series_state import (
    transform_series_state,
)


INPUT_FILE = (
    Path(__file__).parent
    / "audit_results"
    / "series_states"
    / "2812784.json"
)


OUTPUT_FILE = (
    Path(__file__).parent
    / "audit_results"
    / "series_states"
    / "2812784_compact.json"
)


def load_json(
    file_path: Path,
) -> dict[str, Any]:
    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        value = json.load(file)

    if not isinstance(value, dict):
        raise ValueError(
            f"{file_path} does not contain "
            "a JSON object."
        )

    return value


def save_json(
    file_path: Path,
    value: Any,
) -> None:
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            value,
            file,
            indent=2,
            ensure_ascii=False,
        )


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n"
            f"{INPUT_FILE}"
        )

    raw_state = load_json(
        INPUT_FILE
    )

    compact_state = transform_series_state(
        raw_state
    )

    save_json(
        OUTPUT_FILE,
        compact_state,
    )

    print(
        f"Series: "
        f"{compact_state['series_id']}"
    )

    print(
        f"Valid: "
        f"{compact_state['valid']}"
    )

    print(
        f"Maps: "
        f"{compact_state['map_count']}"
    )

    print(
        f"Rounds: "
        f"{compact_state['round_count']}"
    )

    print(
        f"Winner ID: "
        f"{compact_state['winning_team_id']}"
    )

    print()
    print("Map summary:")

    for game in compact_state["games"]:
        team_scores = " | ".join(
            f"{team['name']} "
            f"{team['score']}"
            for team in game["teams"]
        )

        print(
            f"- {game['map_name']}: "
            f"{team_scores}"
            f" | Rounds: "
            f"{game['round_count']}"
        )

    print()
    print(
        f"Compact JSON saved to:\n"
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()