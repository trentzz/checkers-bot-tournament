import copy

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour


class ScaredyCat(Bot):
    """
    Maximise the length of my opponent's move list (unless I can win)
    """

    def play_move(self, board: Board, colour: Colour, move_list: list[Move]) -> int:
        opp_colour = Colour.BLACK if colour == Colour.WHITE else Colour.WHITE

        scores1: list[tuple[int, int]] = []
        for i1, move1 in enumerate(move_list):
            searchboard = copy.deepcopy(board)
            searchboard.move_piece(move1)  # Our candidate move, now opp's turn
            move_list_2 = searchboard.get_move_list(opp_colour)

            if len(move_list_2) == 0:
                # Great! This move wins the game.
                return i1
            scores1.append(
                (
                    i1,
                    len(move_list_2),
                )
            )

        # Give our opponent as many choices as possible
        # Indirectly means we tend to offer them less capturing chances
        max_index1, max_score1 = max(scores1, key=lambda x: x[1])

        return max_index1

    def get_name(self) -> str:
        return "ScaredyCat"
