import pytest

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.board_start_builder import DefaultBSB
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.bots.bot_tracker import BotTracker
from checkers_bot_tournament.bots.first_mover import FirstMover
from checkers_bot_tournament.game import Game
from checkers_bot_tournament.move import IllegalMoveException, Move
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class MaliciousBot(Bot):
    def play_move(self, info: PlayMoveInfo) -> Move:
        # Try to submit an invalid move
        return Move((1, 0), (4, 5), (5, 3))

    @classmethod
    def _get_name(cls):
        return "MaliciousBot"


def test_malicious_bot_tampering() -> None:
    builder = DefaultBSB()

    # Create a board and populate with pieces
    board = Board(builder)
    game = Game(
        BotTracker(FirstMover, 0, []), BotTracker(MaliciousBot, 1, []), board, 0, 0, True, None
    )

    game2 = Game(
        BotTracker(MaliciousBot, 1, []), BotTracker(FirstMover, 0, []), board, 0, 0, True, None
    )

    game.white_bot = game.white_tracker.spawn_bot()
    game.black_bot = game.black_tracker.spawn_bot()

    # First Mover should make a legal move
    game.query_move()
    game.swap_turn()
    with pytest.raises(IllegalMoveException):
        game.query_move()

    game2.white_bot = game2.white_tracker.spawn_bot()
    game2.black_bot = game2.black_tracker.spawn_bot()
    with pytest.raises(IllegalMoveException):
        game2.query_move()
