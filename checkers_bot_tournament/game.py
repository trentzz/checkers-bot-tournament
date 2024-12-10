import copy
from typing import Optional, Tuple, overload

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.bot_tracker import BotTracker
from checkers_bot_tournament.checkers_util import make_unique_bot_string
from checkers_bot_tournament.game_result import GameResult, Result
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour

AUTO_DRAW_MOVECOUNT = 50 * 2


class Game:
    def __init__(
        self,
        white: BotTracker,
        black: BotTracker,
        board: Board,
        game_id: int,
        game_round: int,
        verbose: bool,
        start_pdn: Optional[str],
    ):
        self.white = white
        self.black = black
        self.board = board
        self.game_id = game_id
        self.game_round = game_round
        self.verbose = verbose
        self.pdn = start_pdn

        self.current_turn = Colour.WHITE
        self.move_number = 1
        self.is_first_move = True

        # There must be a capture or promotion within last 50 moves
        # of both players, or 100 by our count.
        self.last_action_move = 0

        self.white_kings_made = 0
        self.white_num_captures = 0
        self.black_kings_made = 0
        self.black_num_captures = 0

        self.game_result: Optional[GameResult] = None
        self.moves_string = ""  # if verbose else None

        if self.pdn:
            self.import_pdn(self.pdn)

    def import_pdn(self, filename: str) -> None:
        """
        Imports a PDN file and populates the move history and board state.
        """
        with open(filename, "r", encoding="utf-8") as file:
            pdn_content = file.read().strip()

        moves = pdn_content.split()  # Assumes moves are space-separated

        for move in moves:
            if "-" in move:  # Regular move
                start, end = move.split("-")
            elif "x" in move:  # Capture move
                start, end = move.split("x")
            else:
                raise ValueError(f"Invalid move format: {move}")

            start_pos = self._pdn_to_coordinates(start)
            end_pos = self._pdn_to_coordinates(end)
            removed_pos = self._get_removed_position(start_pos, end_pos) if "x" in move else None

            move_obj = Move(start_pos, end_pos, removed_pos)

            if not self.board.is_valid_move(self.current_turn, move_obj):
                raise RuntimeError(f"Invalid move in import_pdn: {move}")

            capture, promotion = self.board.move_piece(move_obj)
            if capture or promotion:
                # Reset action move, since capture or promotion occured
                self.last_action_move = self.move_number
                if capture:
                    self._record_capture()
                if promotion:
                    self._record_promotion()

            self.move_number += 1
            self.swap_turn()

    @overload
    def export_pdn(self, filename: str) -> None: ...

    @overload
    def export_pdn(self) -> str: ...

    def export_pdn(self, filename: Optional[str] = None) -> None | str:
        """
        Exports the move history to a PDN file or as a string in PDN format.
        
        If a filename is provided, the PDN content is written to the file.
        If no filename is provided, the PDN content is returned as a string.
        """
        pdn_moves = []

        for move in self.board.get_move_history():
            start = self._coordinates_to_pdn(move.start)
            end = self._coordinates_to_pdn(move.end)
            if move.removed:
                pdn_move = f"{start}x{end}"
            else:
                pdn_move = f"{start}-{end}"
            pdn_moves.append(pdn_move)

        pdn_content = " ".join(pdn_moves)

        if filename is not None:
            with open(filename, "w", encoding="utf-8") as file:
                file.write(pdn_content)
            return None
        else:
            return pdn_content

    def _pdn_to_coordinates(self, pdn: str) -> Tuple[int, int]:
        """Converts a PDN square number to a (row, col) coordinate."""
        square_num = int(pdn)
        row = (square_num - 1) // (self.board.size // 2)
        col = ((square_num - 1) % (self.board.size // 2)) * 2 + (1 if row % 2 == 0 else 0)

        return row, col

    def _coordinates_to_pdn(self, coord: Tuple[int, int]) -> str:
        """Converts a (row, col) coordinate to a PDN square number."""
        row, col = coord
        square_num = row * (self.board.size // 2) + (col // 2) + 1
        return str(square_num)

    def _get_removed_position(
        self, start: Tuple[int, int], end: Tuple[int, int]
    ) -> Tuple[int, int]:
        """Returns the position of the captured piece for a capture move."""
        start_row, start_col = start
        end_row, end_col = end
        removed_row = (start_row + end_row) // 2
        removed_col = (start_col + end_col) // 2
        return removed_row, removed_col

    def make_move(self) -> Optional[Result]:
        bot = self.white.bot if self.current_turn == Colour.WHITE else self.black.bot
        move_list: list[Move] = self.board.get_move_list(self.current_turn)

        if len(move_list) == 0:
            result = Result.BLACK if self.current_turn == Colour.WHITE else Result.WHITE
            # TODO: You can add extra information here (and pass it into write_game_result)
            # and GameResult as needed
            # self.write_game_result(result)
            return result

        # TODO: Add a futures thingo to limit each bot to 10 seconds per move or smth
        # from concurrent.futures import ThreadPoolExecutor
        # with ThreadPoolExecutor() as executor:
        #     future = executor.submit(...)
        #     try:
        #         return future.result(timeout=10)
        #     except TimeoutError:
        #         !!!
        move_idx = bot.play_move(copy.deepcopy(self.board), self.current_turn, copy.copy(move_list))
        if move_idx < 0 or move_idx >= len(move_list):
            bot_string = make_unique_bot_string(bot.bot_id, bot.get_name())
            raise RuntimeError(f"bot: {bot_string} has played an invalid move")

        move = move_list[move_idx]
        capture, promotion = self.board.move_piece(move)
        if capture or promotion:
            # Reset action move, since capture or promotion occured
            self.last_action_move = self.move_number
            if capture:
                self._record_capture()
            if promotion:
                self._record_promotion()

        if self.verbose:
            self.moves_string += f"Move {self.move_number}: {self.current_turn}'s turn\n"
            self.moves_string += f"Moved from {str(move.start)} to {str(move.end)}\n"
            self.moves_string += "\n" + self.board.display()

        if self.move_number - self.last_action_move >= AUTO_DRAW_MOVECOUNT:
            result = Result.DRAW
            # TODO: You can add extra information here (and pass it into write_game_result)
            # and GameResult as needed

            if self.verbose:
                self.moves_string += f"Automatic draw by {AUTO_DRAW_MOVECOUNT/2}-move rule!\n"
            # self.write_game_result(result)
            return result

        self.move_number += 1
        return None

    def _record_capture(self) -> None:
        if self.current_turn == Colour.WHITE:
            self.white_num_captures += 1
        else:
            self.black_num_captures += 1

    def _record_promotion(self) -> None:
        if self.current_turn == Colour.WHITE:
            self.white_kings_made += 1
        else:
            self.black_kings_made += 1

    def run(self) -> GameResult:
        while True:
            # TODO: Implement chain moves (use is_first_move)
            result = self.make_move()
            if result:
                break
            else:
                self.swap_turn()

        return self._write_game_result(result)

    def _write_game_result(self, result: Result) -> GameResult:
        self.game_result = GameResult(
            game_id=self.game_id,
            game_round=self.game_round,
            result=result,
            white_name=make_unique_bot_string(self.white),
            white_rating=round(self.white.rating),
            white_kings_made=self.white_kings_made,
            white_num_captures=self.white_num_captures,
            black_name=make_unique_bot_string(self.black),
            black_rating=round(self.black.rating),
            black_kings_made=self.black_kings_made,
            black_num_captures=self.black_num_captures,
            num_moves=self.move_number,
            moves=self.moves_string,
            moves_pdn=self.export_pdn(),
        )
        return self.game_result

    def swap_turn(self) -> None:
        self.current_turn = self.current_turn.get_opposite()

        self.is_first_move = True
