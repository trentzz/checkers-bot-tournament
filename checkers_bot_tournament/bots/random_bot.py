from random import randint

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour


class RandomBot(Bot):
    def play_move(self, board: Board, colour: Colour, move_list: list[Move]) -> int:
        return randint(0, len(move_list) - 1)

    def get_name(self) -> str:
        return "RandomBot"
