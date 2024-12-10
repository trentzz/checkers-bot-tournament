from dataclasses import dataclass

from checkers_bot_tournament.bots.base_bot import Bot


@dataclass
class GameResultStat:
    white_wins: int = 0
    white_draws: int = 0
    white_losses: int = 0

    black_wins: int = 0
    black_draws: int = 0
    black_losses: int = 0


STARTING_ELO = 1500
# Dynamic learning rate as per USCF: K = 800/(Ne + m),
# where Ne is effective number of games a player's rating is based on, and
# m the number of games the player completed in a tournament for rating consideration

# Each multiple of scale rating difference is a 10x increase in expected score
SCALE = 400


class BotTracker:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.rating: float = STARTING_ELO
        self.stats = GameResultStat()

        self.games_played = 0

        # resets every tournament
        self.tournament_evs: list[float] = []
        self.tournament_scores: list[float] = []

    def calculate_ev(self, other: "BotTracker") -> float:
        Qa = 10 ** (self.rating / SCALE)
        Qb = 10 ** (other.rating / SCALE)

        Ea = Qa / (Qa + Qb)  # Ea + Eb = 1
        return Ea

    def register_ev(self, ev: float) -> None:
        self.tournament_evs.append(ev)

    def register_result(self, score: float) -> None:
        self.tournament_scores.append(score)

    def update_rating(self) -> None:
        assert len(self.tournament_evs) == len(self.tournament_scores), (
            f"{self.tournament_evs} {self.tournament_scores}"
            "You are supposed to call this after registering all tournament results"
        )

        tournament_games_played = len(self.tournament_evs)
        total_ev = sum(self.tournament_evs)
        total_score = sum(self.tournament_scores)

        K_FACTOR = 800 / (self.games_played + tournament_games_played)
        self.rating += K_FACTOR * (total_score - total_ev)

        self.games_played += tournament_games_played
        self.tournament_evs = []
        self.tournament_scores = []
