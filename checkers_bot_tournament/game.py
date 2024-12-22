import copy
from collections import defaultdict
from typing import Optional, Tuple, overload

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.bots.bot_tracker import BotTracker
from checkers_bot_tournament.checkers_util import make_unique_bot_string
from checkers_bot_tournament.game_result import GameResult, Result
from checkers_bot_tournament.move import IllegalMoveException, Move
from checkers_bot_tournament.piece import Colour
from checkers_bot_tournament.play_move_info import PlayMoveInfo

AUTO_DRAW_MOVECOUNT = 40 * 2


class Game:
    def __init__(
        self,
        white_tracker: BotTracker,
        black_tracker: BotTracker,
        board: Board,
        game_id: int,
        game_round: int,
        verbose: bool,
        start_pdn: Optional[str],
    ):
        self.white_tracker = white_tracker
        self.black_tracker = black_tracker
        self.white_bot: Optional[Bot] = None
        self.black_bot: Optional[Bot] = None

        self.board = board
        self.game_id = game_id
        self.game_round = game_round
        self.verbose = verbose
        self.pdn = start_pdn

        self.current_turn = Colour.WHITE
        self.is_first_move = True

        # There must be a capture or promotion within last 40 moves
        # of both players, or 80 by our count.
        self.last_action_move = 0

        self.white_kings_made = 0
        self.white_num_captures = 0
        self.black_kings_made = 0
        self.black_num_captures = 0

        self.game_result: Optional[GameResult] = None
        self.moves_string: str = ""  # if verbose else None
        self.move_history: list[Move] = []
        self.board_hashes: dict[Board, list[int]] = defaultdict(list)

        if self.pdn:
            self.import_pdn(self.pdn)

    @property
    def move_number(self) -> int:
        """
        Querying move_number happens after a move is made, so move_number
        represents the move number of the last recorded move in move_history
        and NOT the move number of the next move.

        To clarify, this means the first move should have move_number 1.
        """
        return len(self.move_history)

    def import_pdn(self, filename: str) -> None:
        """
        Imports a PDN file and populates the move history and board state.
        """
        with open(filename, "r", encoding="utf-8") as file:
            pdn_content = file.read().strip()

        moves = pdn_content.split()  # Assumes moves are space-separated

        # Record the starting board state
        position_occurences = self.board_hashes[self.board.__hash__()]
        position_occurences.append(self.move_number)

        for idx, move in enumerate(moves):
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

            # Check if the first move is valid for white or black and set
            # current_turn accordingly
            if idx == 0:
                assert not self.move_history

                if self.board.is_valid_move(Colour.WHITE, move_obj):
                    self.current_turn = Colour.WHITE
                elif self.board.is_valid_move(Colour.BLACK, move_obj):
                    self.current_turn = Colour.BLACK
                else:
                    raise IllegalMoveException(
                        f"First move in import_pdn is invalid for both white and black: {move}"
                    )
            else:
                if not self.board.is_valid_move(self.current_turn, move_obj):
                    raise IllegalMoveException(
                        f"Invalid move in import_pdn for colour: {str(self.current_turn)}, turn: {self.move_number + 1}, move: {move}"
                    )

            result = self.execute_move(move_obj, True)
            # Don't accept pdns where the game has already finished
            if result:
                raise RuntimeError(
                    f"PDN game: {self.pdn} is already complete on move {self.move_number} with result: {result.name}. There's nothing for bots to do!"
                )
            self.swap_turn()

    def execute_move(self, move: Move, from_import: bool = False) -> Optional[Result]:
        # Update move history
        self.move_history.append(move)
        capture, promotion = self.board.move_piece(move)
        position_occurences = self.board_hashes[self.board.__hash__()]
        position_occurences.append(self.move_number)

        if capture or promotion:
            # Reset action move, since capture or promotion occured
            self.last_action_move = self.move_number
            if capture:
                self._record_capture()
            if promotion:
                self._record_promotion()

        if self.verbose:
            self.moves_string += f"Move {self.move_number}: {self.current_turn}'s turn\n"
            self.moves_string += f"Moved from {str(move.start)} to {str(move.end)}"
            if from_import:
                self.moves_string += " (Book Move)"
            self.moves_string += "\n" + self.board.display() + "\n"

        if len(position_occurences) >= 3:
            # threefold repetition
            if self.verbose:
                self.moves_string += (
                    f"Draw by repetition! Position occured on moves {position_occurences}.\n"
                )
            return Result.DRAW

        if self.move_number - self.last_action_move >= AUTO_DRAW_MOVECOUNT:
            if self.verbose:
                self.moves_string += f"Automatic draw by {AUTO_DRAW_MOVECOUNT/2}-move rule!\n"
            return Result.DRAW

        next_to_move = self.current_turn.get_opposite()
        move_list: list[Move] = self.board.get_move_list(next_to_move)
        if len(move_list) == 0:
            result = next_to_move.get_opposite().as_result()
            if self.verbose:
                self.moves_string += (
                    f"{result.name} wins! {next_to_move.value} cannot make any moves.\n"
                )
            return result

        return None

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

        for move in self.move_history:
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

    def query_move(self) -> Optional[Result]:
        bot = self.white_bot if self.current_turn == Colour.WHITE else self.black_bot
        assert bot

        move_list = self.board.get_move_list(self.current_turn)
        # TODO: Add a futures thingo to limit each bot to 10 seconds per move or smth
        # from concurrent.futures import ThreadPoolExecutor
        # with ThreadPoolExecutor() as executor:
        #     future = executor.submit(...)
        #     try:
        #         return future.result(timeout=10)
        #     except TimeoutError:
        #         !!!
        chosen_move = bot.play_move(
            PlayMoveInfo(
                board=copy.deepcopy(self.board),
                colour=self.current_turn,
                move_list=move_list.copy(),
                move_history=self.move_history.copy(),
                last_action_move=self.last_action_move,
            )
        )

        if chosen_move not in move_list:
            # Offending player loses by forfeit
            raise IllegalMoveException(
                f"bot: {make_unique_bot_string(bot)} made an illegal move {chosen_move}! Automatic forfeit."
            )

        result = self.execute_move(chosen_move)
        return result

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
        self.white_bot = self.white_tracker.spawn_bot()
        self.black_bot = self.black_tracker.spawn_bot()

        next_move_list = self.board.get_move_list(self.current_turn)
        if len(next_move_list) == 0:
            raise RuntimeError(
                f"Game is already complete (no valid moves for player {self.current_turn.name})!"
            )

        if self.move_number == 0:
            position_occurences = self.board_hashes[self.board.__hash__()]
            position_occurences.append(self.move_number)

        while True:
            try:
                result = self.query_move()
            except IllegalMoveException as e:
                print(e.args)
                result = self.current_turn.get_opposite().as_result()
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
            white_name=make_unique_bot_string(self.white_tracker),
            white_rating=round(self.white_tracker.rating),
            white_kings_made=self.white_kings_made,
            white_num_captures=self.white_num_captures,
            black_name=make_unique_bot_string(self.black_tracker),
            black_rating=round(self.black_tracker.rating),
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
