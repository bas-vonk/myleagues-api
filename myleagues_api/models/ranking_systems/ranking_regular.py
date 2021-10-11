from myleagues_api.models.ranking_systems.ranking import BaseRankingSystem


class RegularRankingSystem(BaseRankingSystem):
    """Regular ranking system class."""

    def __init__(self, league):
        super().__init__(league)

    def get_ranking(self, matches=[]):
        """Get ranking."""

        if not matches:
            matches = self.all_matches

        ranking_dict = self.get_initial_ranking_dict()

        for match in matches:
            self.add_points_to_ranking_dict(match, ranking_dict)

        return self.get_ranking_list_from_dict(ranking_dict)

    def add_points_to_ranking_dict(self, match, ranking_dict):
        """Add points to the ranking dictionary."""

        home_pts_pri, away_pts_pri = self.get_primary_points_for_match(match)
        home_pts_sec, away_pts_sec = self.get_secondary_points_for_match(match)

        ranking_dict[match.home_player_id]["pts_primary"] += home_pts_pri
        ranking_dict[match.home_player_id]["pts_secondary"] += home_pts_sec

        ranking_dict[match.away_player_id]["pts_primary"] += away_pts_pri
        ranking_dict[match.away_player_id]["pts_secondary"] += away_pts_sec

    @staticmethod
    def get_primary_points_for_match(match):
        """Get primary points for match."""

        # Return home_score, away_score

        if match.home_score > match.away_score:
            return 2, 0
        elif match.home_score < match.away_score:
            return 0, 2
        else:
            return 1, 1

    @staticmethod
    def get_secondary_points_for_match(match):
        """Get secondary points for match."""

        score_difference = match.home_score - match.away_score

        return score_difference, -score_difference
