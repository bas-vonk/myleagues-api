from numpy import absolute, argmax, linalg, sign, sqrt, zeros

from myleagues_api.models.ranking_systems.ranking import BaseRankingSystem

NOT_PLAYED_PLACEHOLDER = -1
NOT_PLAYED_SCORE = 0


class PerronFrobeniusRankingSystem(BaseRankingSystem):
    """Perron Frobenius Ranking system class."""

    def __init__(self, league):
        super().__init__(league)

    def get_ranking(self, matches: list = []):
        """Get ranking."""

        ranking_dict = self.get_initial_ranking_dict()

        if not matches:
            matches = self.all_matches

        self.add_primary_points_to_ranking_dict(ranking_dict, matches)
        self.add_secondary_points_to_ranking_dict(ranking_dict, matches)

        return self.get_ranking_list_from_dict(ranking_dict)

    @classmethod
    def add_primary_points_to_ranking_dict(cls, ranking_dict, matches):
        """Add primary points to ranking dictionary."""

        # Initialize the head-to-head points dict
        player_ids = list(ranking_dict.keys())

        h2h_points = cls.get_h2h_points(player_ids, matches)
        h2h_scores = cls.get_h2h_scores(player_ids, h2h_points)
        matrix_a = cls.get_matrix_a(player_ids, h2h_scores)
        lead_ev = cls.get_lead_ev(matrix_a)

        cls.add_points_to_ranking_dict(ranking_dict, player_ids, lead_ev)

    @staticmethod
    def add_secondary_points_to_ranking_dict(ranking_dict, matches):
        """Add secondary points to ranking dictionary."""

        for match in matches:

            if match.home_score > match.away_score:
                ranking_dict[match.home_player_id]["pts_secondary"] += 1
            elif match.home_score < match.away_score:
                ranking_dict[match.away_player_id]["pts_secondary"] += 1
            else:
                ranking_dict[match.home_player_id]["pts_secondary"] += 0.5
                ranking_dict[match.away_player_id]["pts_secondary"] += 0.5

    @classmethod
    def get_h2h_scores(cls, player_ids, h2h_points):
        """Get head-to-head scores from head-to-head points."""

        player_dict = {player_id: 0 for player_id in player_ids}

        h2h_scores = {player_id: player_dict.copy() for player_id in player_ids}

        for player_id, opponents in h2h_points.items():
            for opponent_id, points in opponents.items():
                s_i_j = points
                s_j_i = h2h_points[opponent_id][player_id]

                if s_i_j == NOT_PLAYED_PLACEHOLDER:
                    h2h_scores[player_id][opponent_id] = NOT_PLAYED_SCORE
                else:
                    h2h_scores[player_id][opponent_id] = cls.a_i_j(s_i_j, s_j_i)

        return h2h_scores

    @staticmethod
    def get_h2h_points(player_ids, matches):
        """Get head-to-head points from matches."""

        player_dict = {player_id: NOT_PLAYED_PLACEHOLDER for player_id in player_ids}

        h2h_points = {player_id: player_dict.copy() for player_id in player_ids}

        for match in matches:
            h2h_points[match.home_player_id][match.away_player_id] += match.home_score
            h2h_points[match.away_player_id][match.home_player_id] += match.away_score

        return h2h_points

    @staticmethod
    def get_matrix_a(player_ids, h2h_scores):
        """Get matrix A."""

        matrix_a = zeros([len(player_ids), len(player_ids)])
        for idx1, player_1_id in enumerate(player_ids):
            for idx2, player_2_id in enumerate(player_ids):
                a_i_j = h2h_scores[player_1_id][player_2_id]
                matrix_a[idx1, idx2] = a_i_j

        return matrix_a

    @staticmethod
    def get_lead_ev(matrix_a):
        """Get the leading eigenvector."""

        eigenvalues, eigenvectors = linalg.eig(matrix_a)

        # Retrieve the index of the largest eigenvalue, as stated in the paper
        index: int = argmax(eigenvalues)

        # Get the absolute eigenvector
        return absolute(eigenvectors[:, index])

    @staticmethod
    def add_points_to_ranking_dict(ranking_dict, player_ids, lead_ev):
        """Add points to the ranking dictionary."""

        for index, player_id in enumerate(player_ids):
            ranking_dict[player_id]["pts_primary"] += int(lead_ev[index] * 1000)

    @classmethod
    def a_i_j(cls, s_i_j: int, s_j_i: int) -> float:
        """Calculate the value a_i_j."""
        return cls.h((s_i_j + 1) / (s_i_j + s_j_i + 2))

    @staticmethod
    def h(x: float) -> float:
        """Calculate the value for h from x."""
        return 0.5 + 0.5 * sign(x - 0.5) * sqrt(abs(2 * x - 1))
