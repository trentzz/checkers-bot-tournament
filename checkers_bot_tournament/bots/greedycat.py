import copy

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour


class GreedyCat(Bot):
    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id)
        self.ply = 1

        self.man_value = 1
        self.king_value = 4

    """
    Maximise the length of my move_list after my opponent's best move
    """

    def play_move(self, board: Board, colour: Colour, move_list: list[Move]) -> int:
        # print(f"Ply {self.ply if colour == Colour.WHITE else self.ply + 1} as {colour}")
        opp_colour = Colour.BLACK if colour == Colour.WHITE else Colour.WHITE

        scores1: list[tuple[int, int]] = []
        for i1, move1 in enumerate(move_list):
            searchboard = copy.deepcopy(board)
            searchboard.move_piece(move1)  # Our candidate move, now opp's turn
            move_list_2 = searchboard.get_move_list(opp_colour)

            if len(move_list_2) == 0:
                # Great! This move wins the game.
                return i1

            scores2: list[tuple[int, int]] = []
            for i2, move2 in enumerate(move_list_2):
                searchboard2 = copy.deepcopy(searchboard)
                searchboard2.move_piece(move2)  # Opp's candidate move, now our turn

                # Score by number of moves WE can make
                s2 = self.do_scoring(searchboard2, colour)
                scores2.append(
                    (
                        i2,
                        s2,
                    )
                )

            # print(f"{scores2=}")
            # As opp, one would want to minimise our score. Save the i1th move
            # that would achieve this
            min_index2, min_score2 = min(scores2, key=lambda x: x[1])
            scores1.append(
                (
                    i1,
                    min_score2,
                )
            )

        # Now as ourselves, we want to maximise our score assuming our opp
        # wants to do us as much harm as they can (albeit from by our metrics)
        max_index1, max_score1 = max(scores1, key=lambda x: x[1])
        # print(f"{scores1=}")

        self.ply += 2
        return max_index1

    def do_scoring(self, board: Board, our_colour: Colour) -> int:
        def evaluate_at_point_of_no_captures(
            board: Board, colour_to_move: Colour
        ) -> int:
            move_list = board.get_move_list(colour_to_move)
            if len(move_list) == 0:
                if our_colour == colour_to_move:
                    return -999
                else:
                    return 999

            # Check if we have to capture
            scores: list[tuple[int, int]] = []
            if move_list[0].removed:
                for i, move in enumerate(move_list):
                    search_board = copy.deepcopy(board)
                    search_board.move_piece(move)
                    score = evaluate_at_point_of_no_captures(
                        search_board, colour_to_move.get_opposite()
                    )
                    scores.append(
                        (
                            i,
                            score,
                        )
                    )
                if our_colour == colour_to_move:
                    # we just made a range of moves; the scores are opponent's eval
                    # so we wanna take the max score
                    best_index, best_score = max(scores, key=lambda x: x[1])
                else:
                    # opp just made a range of moves; the scores are our eval
                    # they would wanna take the min score
                    best_index, best_score = min(scores, key=lambda x: x[1])
                return best_score
            else:
                if our_colour == colour_to_move:
                    return len(board.get_move_list(colour_to_move))
                else:
                    return len(board.get_move_list(colour_to_move))

        # Determine the letter representing the opponent's pieces
        opp_colour = our_colour.get_opposite()

        # Calculate the material count for the player's pieces
        material_score = 0
        for i in board.grid:
            for j in i:
                if j:
                    if j.colour is our_colour:
                        if j.is_king:
                            self.king_value += self.king_value
                        else:
                            material_score += self.man_value
                    elif j.colour is opp_colour:
                        if j.is_king:
                            self.king_value -= self.king_value
                        else:
                            material_score -= self.man_value

        # Return the difference in material count
        return material_score

    def get_name(self) -> str:
        return "GreedyCat"
