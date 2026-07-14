from .client import (
    GridClient,
    GridClientError,
)

from .queries import GET_TITLES


def main() -> None:
    print("Connecting to GRID...")

    try:
        with GridClient() as client:
            data = client.central(GET_TITLES)

    except GridClientError as error:
        print()
        print("GRID connection failed.")
        print(error)
        raise SystemExit(1) from error

    titles = data.get("titles", [])

    if not isinstance(titles, list):
        print(
            "GRID connection succeeded, but the titles "
            "response had an unexpected structure."
        )
        raise SystemExit(1)

    print("GRID connection succeeded.")
    print(f"Accessible titles: {len(titles)}")
    print()

    for title in titles:
        if not isinstance(title, dict):
            continue

        title_id = title.get("id", "Unknown ID")
        full_name = title.get(
            "name",
            "Unknown title",
        )

        shortened_name = title.get(
            "nameShortened",
            "Unknown",
        )

        print(
            f"- {full_name} "
            f"({shortened_name}) "
            f"| GRID ID: {title_id}"
        )


if __name__ == "__main__":
    main()