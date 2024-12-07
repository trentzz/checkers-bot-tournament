import copy
from typing import Optional, Tuple

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.checkers_util import make_unique_bot_string
from checkers_bot_tournament.game_result import GameResult, Result
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour

AUTO_DRAW_MOVECOUNT = 50 * 2


class Game:
    def __init__(
        self,
        white: Bot,
        black: Bot,
        board: Board,
        game_id: int,
        game_round: int,
        verbose: bool,
    ):
        self.white = white
        self.black = black
        self.board = board
        self.game_id = game_id
        self.game_round = game_round
        self.verbose = verbose

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
        self.moves = ""  # if verbose else None

    def make_move(self) -> Tuple[Optional[Move], bool]:
        bot = self.white if self.current_turn == Colour.WHITE else self.black
        move_list: list[Move] = self.board.get_move_list(self.current_turn)

        if len(move_list) == 0:
            result = Result.BLACK if self.current_turn == Colour.WHITE else Result.WHITE
            # TODO: You can add extra information here (and pass it into write_game_result)
            # and GameResult as needed
            self.write_game_result(result)
            return (None, True)

        # TODO: Add a futures thingo to limit each bot to 10 seconds per move or smth
        # from concurrent.futures import ThreadPoolExecutor
        # with ThreadPoolExecutor() as executor:
        #     future = executor.submit(...)
        #     try:
        #         return future.result(timeout=10)
        #     except TimeoutError:
        #         !!!
        move_idx = bot.play_move(
            copy.deepcopy(self.board), self.current_turn, copy.copy(move_list)
        )
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
            self.moves += f"Move {self.move_number}: {self.current_turn}'s turn\n"
            self.moves += f"Moved from {str(move.start)} to {str(move.end)}\n"
            self.moves += "\n" + self.board.display()

        if self.move_number - self.last_action_move >= AUTO_DRAW_MOVECOUNT:
            result = Result.DRAW
            # TODO: You can add extra information here (and pass it into write_game_result)
            # and GameResult as needed

            if self.verbose:
                self.moves += f"Automatic draw by {AUTO_DRAW_MOVECOUNT/2}-move rule!\n"
            self.write_game_result(result)
            return move, True

        self.move_number += 1

        return move, False

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

    def run(self) -> None:
        while True:
            # TODO: Implement chain moves (use is_first_move)
            move, stop = self.make_move()
            if move is None or stop:
                break

            self.swap_turn()

    def write_game_result(self, result: Result) -> None:
        self.game_result = GameResult(
            game_id=self.game_id,
            game_round=self.game_round,
            result=result,
            white_name=make_unique_bot_string(self.white),
            white_kings_made=self.white_kings_made,
            white_num_captures=self.white_num_captures,
            black_name=make_unique_bot_string(self.black),
            black_kings_made=self.black_kings_made,
            black_num_captures=self.black_num_captures,
            num_moves=self.move_number,
            moves=self.moves,
        )

    def get_game_result(self) -> GameResult:
        assert self.game_result is not None
        return self.game_result

    def swap_turn(self) -> None:
        if self.current_turn == Colour.WHITE:
            self.current_turn = Colour.BLACK
        else:
            self.current_turn = Colour.WHITE

        self.is_first_move = True
