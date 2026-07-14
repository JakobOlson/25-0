from __future__ import annotations

from typing import Any


MAJORS: dict[str, dict[str, Any]] = {
    "berlin_2019": {
        "slug": "berlin_2019",
        "grid_tournament_id": "23",
        "name": "StarLadder Berlin Major 2019",
        "year": 2019,
        "title": "csgo",
        "title_id": "1",
    },

    "stockholm_2021": {
        "slug": "stockholm_2021",
        "grid_tournament_id": "84565",
        "name": "PGL Major Stockholm 2021",
        "year": 2021,
        "title": "csgo",
        "title_id": "1",
    },

    "antwerp_2022": {
        "slug": "antwerp_2022",
        "grid_tournament_id": "106034",
        "name": "PGL Major Antwerp 2022",
        "year": 2022,
        "title": "csgo",
        "title_id": "1",
    },

    "rio_2022": {
        "slug": "rio_2022",
        "grid_tournament_id": "106853",
        "name": "Intel Extreme Masters Rio Major 2022",
        "year": 2022,
        "title": "csgo",
        "title_id": "1",
    },

    "paris_2023": {
        "slug": "paris_2023",
        "grid_tournament_id": "322042",
        "name": "BLAST.tv Paris Major 2023",
        "year": 2023,
        "title": "csgo",
        "title_id": "1",
    },

    "copenhagen_2024": {
        "slug": "copenhagen_2024",
        "grid_tournament_id": "757326",
        "name": "PGL Major Copenhagen 2024",
        "year": 2024,
        "title": "cs2",
        "title_id": "28",
    },

    "shanghai_2024": {
        "slug": "shanghai_2024",
        "grid_tournament_id": "775453",
        "name": "Perfect World Shanghai Major 2024",
        "year": 2024,
        "title": "cs2",
        "title_id": "28",
    },

    "austin_2025": {
        "slug": "austin_2025",
        "grid_tournament_id": "826167",
        "name": "BLAST.tv Austin Major 2025",
        "year": 2025,
        "title": "cs2",
        "title_id": "28",
    },
}


DEFAULT_MAJOR_SLUG = "austin_2025"


def get_major(major_slug: str) -> dict[str, Any]:
    """
    Return one supported Major definition.
    """

    major = MAJORS.get(major_slug)

    if major is None:
        available = ", ".join(sorted(MAJORS))

        raise ValueError(
            f"Unknown Major '{major_slug}'. "
            f"Available Majors: {available}"
        )

    return dict(major)


def get_all_majors() -> list[dict[str, Any]]:
    """
    Return every supported Major in chronological order.
    """

    return sorted(
        (dict(major) for major in MAJORS.values()),
        key=lambda major: (
            major["year"],
            major["name"],
        ),
    )