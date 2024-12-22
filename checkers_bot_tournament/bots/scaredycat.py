import copy

from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class ScaredyCat(Bot):
    """
    Maximise the length of my opponent's move list (unless I can win)
    """

    def play_move(self, info: PlayMoveInfo) -> Move:
        colour = info.colour
        move_list = info.move_list
        board = info.board

        opp_colour = Colour.BLACK if colour == Colour.WHITE else Colour.WHITE

        scores1: list[tuple[Move, int]] = []
        for move1 in move_list:
            searchboard = copy.deepcopy(board)
            searchboard.move_piece(move1)  # Our candidate move, now opp's turn
            move_list_2 = searchboard.get_move_list(opp_colour)

            if len(move_list_2) == 0:
                # Great! This move wins the game.
                return move1
            scores1.append(
                (
                    move1,
                    len(move_list_2),
                )
            )

        # Give our opponent as many choices as possible
        # Indirectly means we tend to offer them less capturing chances
        best_move1, max_score = max(scores1, key=lambda x: x[1])

        return best_move1

    @classmethod
    def _get_name(cls) -> str:
        return "ScaredyCat"
