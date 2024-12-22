import random

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class CopyCat(Bot):
    """
    Copies what the other bot does, otherwise just plays something random.
    """

    @classmethod
    def _get_name(cls) -> str:
        return "CopyCat"

    def get_mirror_move(self, board: Board, move: Move) -> Move:
        board_size = board.size
        mirrored_start = (
            board_size - 1 - move.start[0],
            board_size - 1 - move.start[1],
        )

        mirrored_end = (board_size - 1 - move.end[0], board_size - 1 - move.end[1])

        # Reflect the removed piece position, if any
        mirrored_removed = None
        if move.removed:
            mirrored_removed = (
                board_size - 1 - move.removed[0],
                board_size - 1 - move.removed[1],
            )

        return Move(mirrored_start, mirrored_end, mirrored_removed)

    def play_move(self, info: PlayMoveInfo) -> Move:
        # If move history is empty i.e. first move, pick a random move
        moves_list = info.move_list

        if not info.move_history:
            return random.choice(moves_list)

        previous_move = info.move_history[-1]
        mirror_move = self.get_mirror_move(info.board, previous_move)

        # Return the index of the mirrored move if it's valid, otherwise pick a random move
        if mirror_move in info.move_list:
            return mirror_move

        return random.choice(moves_list)
