from myleagues_api.models.ranking_systems.ranking import Ranking


class PerronFrobenius(Ranking):
    def __init__(self, league):
        super().__init__(league)

    def get_ranking_history():
        print("Hello ranking history.")

    def get_ranking(self):

        print("Hello current ranking.")
