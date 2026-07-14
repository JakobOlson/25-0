GET_SERIES_STATE = """
query GetSeriesState(
    $seriesId: ID!
) {
    seriesState(id: $seriesId) {
        version
        id

        title {
            nameShortened
        }

        format
        started
        finished
        valid
        startedAt
        updatedAt
        duration

        teams {
            __typename

            ... on SeriesTeamStateCs2 {
                id
                name
                score
                won
                kills
                deaths
                killAssistsGiven
                killAssistsReceived
                headshots

                players {
                    __typename

                    ... on SeriesPlayerStateCs2 {
                        id
                        name
                        participationStatus
                        kills
                        deaths
                        killAssistsGiven
                        killAssistsReceived
                        headshots
                    }
                }
            }
        }

        games {
            id
            sequenceNumber
            started
            finished
            startedAt
            duration

            map {
                id
                name
            }

            teams {
                __typename

                ... on GameTeamStateCs2 {
                    id
                    name
                    score
                    won
                    kills
                    deaths
                    killAssistsGiven
                    killAssistsReceived
                    headshots
                    damageDealt
                    damageTaken

                    players {
                        __typename

                        ... on GamePlayerStateCs2 {
                            id
                            name
                            participationStatus
                            kills
                            deaths
                            killAssistsGiven
                            killAssistsReceived
                            headshots
                            damageDealt
                            damageTaken
                        }
                    }
                }
            }

            segments {
                id
                type
                sequenceNumber
                started
                finished
                startedAt
                duration

                teams {
                    __typename

                    ... on SegmentTeamStateCs2 {
                        id
                        name
                        side
                        won
                        kills
                        deaths
                        firstKill
                        winType
                        headshots
                        damageDealt
                        damageTaken

                        players {
                            __typename

                            ... on SegmentPlayerStateCs2 {
                                id
                                name
                                participationStatus
                                kills
                                deaths
                                firstKill
                                headshots
                                alive
                                damageDealt
                                damageTaken
                            }
                        }
                    }
                }
            }
        }
    }
}
"""