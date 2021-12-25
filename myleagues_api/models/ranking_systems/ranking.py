from abc import ABC, abstractmethod


class BaseRankingSystem(ABC):
    """Base class for the ranking systems."""

    def __init__(self, league):

        self.league = league

        self.players = self.league.players
        self.all_matches = self.league.matches

    @abstractmethod
    def get_ranking(self):
        """Get ranking."""
        raise NotImplementedError("Child class must contain 'get_ranking' method.")

    def get_ranking_list_from_dict(self, ranking_dict):
        """Get ranking list from ranking dictionary."""

        ranking: list = list(ranking_dict.values())
        ranking = sorted(ranking, key=lambda k: -k["pts_secondary"])
        ranking = sorted(ranking, key=lambda k: -k["pts_primary"])
        ranking = [dict(d, **{"position": idx + 1}) for idx, d in enumerate(ranking)]
        ranking = [dict(d, **{"league_id": self.league.id}) for d in ranking]

        return ranking

    def get_initial_ranking_dict(self):
        """Get the empty ranking dictionary object."""

        # Build the empty ranking
        initial_dictionary = {}
        for player in self.players:
            initial_dictionary[player.id] = {
                "username": player.username,
                "pts_primary": 0,
                "pts_secondary": 0,
                "player_id": player.id,
            }

        return initial_dictionary

    def get_ranking_history(self):
        """Get the ranking history."""

        labels = ["start"]
        datasets = {player.id: {"data": [0]} for player in self.players}

        for i in range(1, len(self.all_matches) + 1):

            matches = self.all_matches[:i]

            labels.append(
                f"{matches[-1].home_player.username} - "
                f"{matches[-1].away_player.username} "
                f"({matches[-1].home_score} - "
                f"{matches[-1].away_score})"
            )

            ranking = self.get_ranking(matches)

            for row in ranking:
                player_id = row["player_id"]
                datasets[player_id]["data"].append(row["pts_primary"])
                datasets[player_id][
                    "label"
                ] = f"{row['position']}. {row['username']} ({row['pts_primary']})"
                datasets[player_id]["position"] = row["position"]

        datasets = sorted(list(datasets.values()), key=lambda k: k["position"])

        return {"labels": labels, "datasets": datasets}


class RankingSystemFactory:
    """Ranking system factory."""

    def __init__(self):
        self._ranking_systems = {}

    def register_ranking_system(self, ranking_system_name, ranking_system_obj):
        """Register a ranking system."""

        self._ranking_systems[ranking_system_name] = ranking_system_obj

    def get_ranking_system(self, ranking_system_name, **kwargs):
        """Get a ranking system."""

        ranking_system_obj = self._ranking_systems.get(ranking_system_name)
        if not ranking_system_obj:
            raise ValueError(ranking_system_name)

        return ranking_system_obj(**kwargs)
