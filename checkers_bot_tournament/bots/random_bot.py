import random

from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class RandomBot(Bot):
    def play_move(self, info: PlayMoveInfo) -> Move:
        return random.choice(info.move_list)

    @classmethod
    def _get_name(cls) -> str:
        return "RandomBot"
