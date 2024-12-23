from abc import ABC, abstractmethod
from typing import final

from checkers_bot_tournament.move import Move
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class Bot(ABC):
    def __init__(self, bot_id: int) -> None:
        self.bot_id = bot_id

    @abstractmethod
    def play_move(self, info: PlayMoveInfo) -> Move:
        """
        Params:
            info    current game info the bot has access to calculate its move.
                    see the PlayMoveInfo dataclass for more info

        Return:
            int     the chosen move from the move_list
        """
        raise RuntimeError("play_move not implemented!")

    @classmethod
    @abstractmethod
    def _get_name(cls) -> str:
        """
        Returns bot's name. Make sure this matches Controller!
        """
        raise RuntimeError("get_name not implemented yet!")

    @final
    def get_name(self) -> str:
        """
        Returns the bot's name through the class method.
        """
        return self.__class__._get_name()
