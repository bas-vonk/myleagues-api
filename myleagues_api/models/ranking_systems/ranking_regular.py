from pprint import pprint

from myleagues_api.models.ranking_systems.ranking import Ranking


class Regular(Ranking):
    def __init__(self, league):
        super().__init__(league)

    def get_ranking_history(self):

        labels = ["start"]
        datasets = {player.id: {"data": [0]} for player in self.players}

        for i in range(1, len(self.all_matches) + 1):

            matches = self.all_matches[:i]

            labels.append(
                f"{matches[-1].home_player.username} - {matches[-1].away_player.username} "
                f"({matches[-1].home_score} - {matches[-1].away_score})"
            )

            ranking = self.get_ranking(matches)

            pprint(ranking)
            print("doei")

            for row in ranking:
                player_id = row["player_id"]
                datasets[player_id]["data"].append(row["pts_primary"])
                datasets[player_id]["label"] = f"{row['position']}. {row['username']}"
                datasets[player_id]["position"] = row["position"]

        datasets = sorted(list(datasets.values()), key=lambda k: k["position"])

        return {"labels": labels, "datasets": datasets}

    def get_ranking(self, matches=[]):

        if not matches:
            matches = self.all_matches

        ranking_dict = self.get_initial_ranking_dict()

        for match in matches:
            self.add_points_to_ranking_dict(match, ranking_dict)

        return self.get_ranking_list_from_dict(ranking_dict)

    def get_initial_ranking_dict(self):

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

    def add_points_to_ranking_dict(self, match, ranking_dict):

        home_pts_pri, away_pts_pri = self.get_primary_points_for_match(match)
        home_pts_sec, away_pts_sec = self.get_secondary_points_for_match(match)

        ranking_dict[match.home_player_id]["pts_primary"] += home_pts_pri
        ranking_dict[match.home_player_id]["pts_secondary"] += home_pts_sec

        ranking_dict[match.away_player_id]["pts_primary"] += away_pts_pri
        ranking_dict[match.away_player_id]["pts_secondary"] += away_pts_sec

    def get_ranking_list_from_dict(self, ranking_dict):

        ranking: list = list(ranking_dict.values())
        ranking = sorted(ranking, key=lambda k: -k["pts_secondary"])
        ranking = sorted(ranking, key=lambda k: -k["pts_primary"])
        ranking = [dict(d, **{"position": idx + 1}) for idx, d in enumerate(ranking)]
        ranking = [dict(d, **{"league_id": self.league.id}) for d in ranking]

        return ranking

    @staticmethod
    def get_primary_points_for_match(match):

        # Return home_score, away_score

        if match.home_score > match.away_score:
            return 2, 0
        elif match.home_score < match.away_score:
            return 0, 2
        else:
            return 1, 1

    @staticmethod
    def get_secondary_points_for_match(match):

        score_difference = match.home_score - match.away_score

        return score_difference, -score_difference
