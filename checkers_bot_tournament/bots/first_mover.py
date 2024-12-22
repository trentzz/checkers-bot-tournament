from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class FirstMover(Bot):
    """
    Just picks the first move :D
    """

    def play_move(self, info: PlayMoveInfo) -> Move:
        return info.move_list[0]

    @classmethod
    def _get_name(cls) -> str:
        return "FirstMover"
