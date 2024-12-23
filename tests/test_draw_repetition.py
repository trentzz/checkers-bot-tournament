from checkers_bot_tournament.board import Board
from checkers_bot_tournament.board_start_builder import FromPiecesBSB
from checkers_bot_tournament.bots.bot_tracker import BotTracker
from checkers_bot_tournament.bots.first_mover import FirstMover  # We won't actually use the bot
from checkers_bot_tournament.game import Game, Result
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour, Piece


# Define a helper function to execute moves
def execute_move(
    game: Game, move: Move, colour_to_move_ptr: list[Colour], expect_draw: bool
) -> None:
    """
    Executes a move for the given colour and asserts its validity.
    """
    colour_to_move = colour_to_move_ptr[0]
    available_moves = game.board.get_move_list(colour_to_move)
    assert move in available_moves, (
        f"Move from {move.start} to {move.end} not found in available moves for {colour_to_move}.\n"
        f"Available moves: {available_moves}"
    )

    result = game.execute_move(move)
    assert (result == Result.DRAW) == expect_draw

    colour_to_move_ptr[0] = colour_to_move.get_opposite()


def test_simple_shuffle() -> None:
    """
    Test when two opposite kings shuffle from one square to another
    black b1 to b2 and w1 to w2. For simplicity we enter into the repetition
    from w0
    """
    #    0  1  2  3  4
    # 0     b1
    # 1  b2          w0
    # 2           w1
    # 3        w2

    # Define shuffle positions
    b1 = (0, 1)
    b2 = (1, 0)
    w0 = (1, 4)
    w1 = (2, 3)
    w2 = (3, 2)

    start_B = b1
    start_W = w0

    piece_list: list[Piece] = [
        Piece(start_B, Colour.BLACK, is_king=True),
        Piece(start_W, Colour.WHITE, is_king=True),
    ]

    builder = FromPiecesBSB(piece_list)

    # Create a board and populate with pieces
    board = Board(builder)
    game = Game(
        BotTracker(FirstMover, 0, []), BotTracker(FirstMover, 1, []), board, 0, 0, True, None
    )

    # make move object w0 to w1
    # assert moving to w1 is valid (it's in the moves list)
    # 1. move to w1
    # 2. start shuffling both kings between positions 1 and 2
    # the 3rd time the position where it is black to move
    # and the pieces are at b1 and w1, draw by repetition will occur.
    plan = [
        Move(start_W, w1, None),
        # b1w1 position once
        Move(b1, b2, None),
        Move(w1, w2, None),
        Move(b2, b1, None),
        Move(w2, w1, None),
        # b1w1 position twice
        Move(b1, b2, None),
        Move(w1, w2, None),
        Move(b2, b1, None),
        # Move(w2, w1, None),
        # position thrice after this move
    ]

    drawing_move = Move(w2, w1, None)

    # Execute the shuffle moves
    colour_to_move_ptr = [Colour.WHITE]
    for move in plan:
        execute_move(game, move, colour_to_move_ptr, False)

    execute_move(game, drawing_move, colour_to_move_ptr, True)


def test_simple_shuffle2() -> None:
    """
    Test repeating positions are nonconsecutive. W goes back to w0 once.

    When two opposite kings shuffle from one square to another
    black b1 to b2 and w1 to w2. For simplicity we enter into the repetition
    from w0.
    """
    #    0  1  2  3  4
    # 0     b1
    # 1  b2          w0
    # 2           w1
    # 3        w2

    # Define shuffle positions
    b1 = (0, 1)
    b2 = (1, 0)
    w0 = (1, 4)
    w1 = (2, 3)
    w2 = (3, 2)

    start_B = b1
    start_W = w0

    piece_list: list[Piece] = [
        Piece(start_B, Colour.BLACK, is_king=True),
        Piece(start_W, Colour.WHITE, is_king=True),
    ]

    builder = FromPiecesBSB(piece_list)

    # Create a board and populate with pieces
    board = Board(builder)
    game = Game(
        BotTracker(FirstMover, 0, []), BotTracker(FirstMover, 1, []), board, 0, 0, True, None
    )

    # make move object w0 to w1
    # assert moving to w1 is valid (it's in the moves list)
    # 1. move to w1
    # 2. start shuffling both kings between positions 1 and 2
    # the 3rd time the position where it is black to move
    # and the pieces are at b1 and w1, draw by repetition will occur.
    plan = [
        Move(start_W, w1, None),
        # b1w1 position once
        Move(b1, b2, None),
        Move(w1, w2, None),
        Move(b2, b1, None),
        Move(w2, w1, None),
        # b1w1 position twice
        Move(b1, b2, None),
        Move(w1, w0, None),
        Move(b2, b1, None),
        # Move(w0, w1, None),
        # position thrice after this move
    ]

    drawing_move = Move(w0, w1, None)

    # Execute the shuffle moves
    colour_to_move_ptr = [Colour.WHITE]
    for move in plan:
        execute_move(game, move, colour_to_move_ptr, False)

    execute_move(game, drawing_move, colour_to_move_ptr, True)


def test_simple_shuffle3() -> None:
    """
    Test we're not just throwing repetition on any 6 different moves.
    Start from wY, go wX then to w0, then we are back to case 1.
    (In the meantime black shuffles between b1 and b2)

    When two opposite kings shuffle from one square to another
    black b1 to b2 and w1 to w2. For clarity, we enter into the repetition
    from w0.
    """
    #    0  1  2  3  4  5  6
    # 0     b1
    # 1  b2          w0
    # 2           w1    wX
    # 3        w2          wY

    # Define shuffle positions
    b1 = (0, 1)
    b2 = (1, 0)
    w0 = (1, 4)
    w1 = (2, 3)
    w2 = (3, 2)
    wX = (2, 5)
    wY = (3, 6)

    start_B = b1
    start_W = wY

    piece_list: list[Piece] = [
        Piece(start_B, Colour.BLACK, is_king=True),
        Piece(start_W, Colour.WHITE, is_king=True),
    ]

    builder = FromPiecesBSB(piece_list)

    # Create a board and populate with pieces
    board = Board(builder)
    game = Game(
        BotTracker(FirstMover, 0, []), BotTracker(FirstMover, 1, []), board, 0, 0, True, None
    )

    # 1. make way to w1
    # 2. start shuffling both kings between positions 1 and 2
    # the 3rd time the position where it is black to move
    # and the pieces are at b1 and w1, draw by repetition will occur.

    plan = [
        Move(start_W, wX, None),  # 1 White: wY -> wX
        Move(start_B, b2, None),  # 2 Black: b1 -> b2
        Move(wX, w0, None),  # 3 White: wX -> w0
        Move(b2, b1, None),  # 4 Black: b2 -> b1
        Move(w0, w1, None),  # 5
        # b1w1 position once
        Move(b1, b2, None),  # 6
        Move(w1, w2, None),  # 7
        Move(b2, b1, None),  # 8
        Move(w2, w1, None),  # 9
        # b1w1 position twice
        Move(b1, b2, None),  # 10
        Move(w1, w2, None),  # 11
        Move(b2, b1, None),  # 12
    ]

    drawing_move = Move(w2, w1, None)

    # Execute the shuffle moves
    colour_to_move_ptr = [Colour.WHITE]
    for move in plan:
        execute_move(game, move, colour_to_move_ptr, False)

    execute_move(game, drawing_move, colour_to_move_ptr, True)
