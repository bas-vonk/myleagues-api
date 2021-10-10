from abc import ABC, abstractmethod


class Ranking(ABC):
    def __init__(self, league):

        self.league = league

        self.players = self.league.players
        self.all_matches = self.league.matches

    @abstractmethod
    def get_ranking(self):
        raise NotImplementedError(
            "Child class must contain 'get_current_ranking' method."
        )

    @abstractmethod
    def get_ranking_history(self):
        raise NotImplementedError(
            "Child class must contain 'get_ranking_history' method."
        )
