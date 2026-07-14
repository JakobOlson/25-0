GET_TITLES = """
query GetTitles {
    titles {
        id
        name
        nameShortened
    }
}
"""


GET_TOURNAMENTS = """
query GetTournaments(
    $first: Int!
    $after: String
    $filter: TournamentFilter
) {
    tournaments(
        first: $first
        after: $after
        filter: $filter
    ) {
        totalCount

        pageInfo {
            hasNextPage
            endCursor
        }

        edges {
            node {
                id
                name
                nameShortened
                startDate
                endDate
                venueType

                parent {
                    id
                    name
                    nameShortened
                    startDate
                    endDate
                }
            }
        }
    }
}
"""


GET_TOURNAMENT_WITH_CHILDREN = """
query GetTournamentWithChildren(
    $tournamentId: ID!
) {
    tournament(id: $tournamentId) {
        id
        name
        nameShortened
        startDate
        endDate
        venueType

        parent {
            id
            name
            nameShortened
            startDate
            endDate
        }

        children {
            id
            name
            nameShortened
            startDate
            endDate
            venueType
        }
    }
}
"""


GET_SERIES_FOR_TOURNAMENT = """
query GetSeriesForTournament(
    $first: Int!
    $after: String
    $filter: SeriesFilter
) {
    allSeries(
        first: $first
        after: $after
        filter: $filter
    ) {
        totalCount

        pageInfo {
            hasNextPage
            endCursor
        }

        edges {
            node {
                id
                startTimeScheduled

                format {
                    id
                    nameShortened
                }

                title {
                    id
                    name
                    nameShortened
                }

                tournament {
                    id
                    name
                    nameShortened
                    startDate
                    endDate

                    parent {
                        id
                        name
                        nameShortened
                    }
                }

                teams {
                    scoreAdvantage

                    baseInfo {
                        id
                        name
                        nameShortened
                    }
                }

                productServiceLevels {
                    productName
                    serviceLevel
                }
            }
        }
    }
}
"""