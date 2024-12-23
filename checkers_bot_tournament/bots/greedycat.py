import copy

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class GreedyCat(Bot):
    """
    Maximise my material after 3 layers of search
    """

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id)
        self.ply = 1

        self.man_value = 1
        self.king_value = 4

    def play_move(self, info: PlayMoveInfo) -> Move:
        colour = info.colour
        board = info.board

        # print(f"Ply {self.ply if colour == Colour.WHITE else self.ply + 1} as {colour}")
        best_line, best_eval = self.minimax(board, 3, -999, 999, colour)

        self.ply += 2
        return best_line.pop()

    def minimax(
        self, board: Board, depth: int, alpha: int, beta: int, colour_to_move: Colour
    ) -> tuple[list[Move], int]:
        move_list = board.get_move_list(colour_to_move)
        if len(move_list) == 0:
            if colour_to_move == Colour.WHITE:
                return [], -999 - depth
            else:
                return [], 999 + depth

        if depth > 0 or move_list[0].removed:
            # Continue searching/finish the capture sequence
            if colour_to_move == Colour.WHITE:
                max_eval = -9999
                max_move = None
                max_moves = None
                for move in move_list:
                    search_board = copy.deepcopy(board)
                    search_board.move_piece(move)
                    moves, evaluation = self.minimax(
                        search_board, depth - 1, alpha, beta, Colour.BLACK
                    )
                    if evaluation > max_eval:
                        max_eval = evaluation
                        max_move = move
                        max_moves = moves
                    alpha = max(alpha, max_eval)
                    if alpha >= beta:
                        break

                assert max_move
                max_moves = [] if max_moves is None else max_moves
                max_moves.append(max_move)
                return max_moves, max_eval
            else:
                min_eval = 9999
                min_move = None
                min_moves = None
                for move in move_list:
                    search_board = copy.deepcopy(board)
                    search_board.move_piece(move)
                    moves, evaluation = self.minimax(
                        search_board, depth - 1, alpha, beta, Colour.WHITE
                    )
                    if evaluation < min_eval:
                        min_eval = evaluation
                        min_move = move
                        min_moves = moves
                    beta = min(beta, min_eval)
                    if beta <= alpha:
                        break

                assert min_move
                min_moves = [] if min_moves is None else min_moves
                min_moves.append(min_move)
                return min_moves, min_eval
        else:
            return [], self.static_eval(board)

    def static_eval(self, board: Board) -> int:
        """
        Evaluate board without searching further
        + score favours white pieces // white is the maximising player
        - score favours black pieces
        """

        material_score = 0
        for i in board.grid:
            for j in i:
                if j:
                    if j.colour is Colour.WHITE:
                        if j.is_king:
                            material_score += self.king_value
                        else:
                            material_score += self.man_value
                    elif j.colour is Colour.BLACK:
                        if j.is_king:
                            material_score -= self.king_value
                        else:
                            material_score -= self.man_value

        return material_score

    @classmethod
    def _get_name(cls) -> str:
        return "GreedyCat"
