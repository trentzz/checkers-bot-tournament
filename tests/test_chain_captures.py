import copy

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.board_start_builder import FromPiecesBSB
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour, Piece


def test_simple_capture() -> None:
    """Test when a lone non-chain capture is on the board, that it is the only move."""

    #    0  1  2  3
    # 0     b1
    # 1  b2    w1
    # 2           1
    # 3

    start_B1 = (0, 1)
    start_B2 = (1, 0)
    start_W1 = (1, 2)
    end_B = (2, 3)  # at 1

    piece_list: list[Piece] = [
        Piece(start_B1, Colour.BLACK),
        Piece(start_B2, Colour.BLACK),
        Piece(start_W1, Colour.WHITE),
    ]

    builder = FromPiecesBSB(piece_list)

    # Create a board and populate with pieces
    board = Board(builder)

    moves = board.get_move_list(Colour.BLACK)
    assert len(moves) == 1
    assert moves[0] == Move(start_B1, end_B, [start_W1])

    # Make sure everything is in their correct spots after the capture
    board.move_piece(moves[0])

    assert board.get_piece(start_B1) is None
    assert board.get_piece(start_W1) is None
    end_B_piece = board.get_piece(end_B)
    assert end_B_piece is not None and end_B_piece.colour is Colour.BLACK


def test_simple_capture2() -> None:
    """Test when a lone non-chain capture is on the board, that it is the only move.
    And that bounds are respected."""

    #    0  1  2  3
    # 0     b1
    # 1  w2    w1
    # 2           1
    # 3

    start_B1 = (0, 1)
    start_W1 = (1, 2)
    start_W2 = (1, 0)
    end_B = (2, 3)  # at 1

    piece_list: list[Piece] = [
        Piece(start_B1, Colour.BLACK),
        Piece(start_W1, Colour.WHITE),
        Piece(start_W2, Colour.WHITE),
    ]

    builder = FromPiecesBSB(piece_list)

    # Create a board and populate with pieces
    board = Board(builder)

    moves = board.get_move_list(Colour.BLACK)
    # capturing leftward would be OOB
    assert len(moves) == 1
    assert moves[0] == Move(start_B1, end_B, [start_W1])

    # Make sure everything is in their correct spots after the capture
    board.move_piece(moves[0])

    assert board.get_piece(start_B1) is None
    assert board.get_piece(start_W1) is None
    end_B_piece = board.get_piece(end_B)
    assert end_B_piece is not None and end_B_piece.colour is Colour.BLACK


def test_multiple_pieces_capturing() -> None:
    """Test multiple pieces each with a simple capture option."""
    #    0  1  2  3  4
    # 0        b1
    # 1     w1
    # 2           b2
    # 3        w2
    # 4

    start_B1 = (0, 2)
    start_W1 = (1, 1)
    end_B1 = (2, 0)  # for b1 capturing w1

    start_B2 = (2, 3)
    start_W2 = (3, 2)
    end_B2 = (4, 1)  # for b2 capturing w2

    piece_list: list[Piece] = [
        Piece(start_B1, Colour.BLACK),
        Piece(start_W1, Colour.WHITE),
        Piece(start_B2, Colour.BLACK),
        Piece(start_W2, Colour.WHITE),
    ]

    builder = FromPiecesBSB(piece_list)

    # Create a board and populate with pieces
    board = Board(builder)

    moves = board.get_move_list(Colour.BLACK)

    # Both captures available
    assert len(moves) == 2
    assert Move(start_B1, end_B1, [start_W1]) in moves
    assert Move(start_B2, end_B2, [start_W2]) in moves


#############################
# Chain captures
#############################


def test_chain_captures() -> None:
    """Test a chain capture with only one option"""
    #    0  1  2  3  4  5
    # 0              b1
    # 1           w1
    # 2        ,
    # 3     w2
    # 4  .

    start_B1 = (0, 4)
    start_W1 = (1, 3)
    start_W2 = (3, 1)
    end_B = (4, 0)

    piece_list: list[Piece] = [
        Piece(start_B1, Colour.BLACK),
        Piece(start_W1, Colour.WHITE),
        Piece(start_W2, Colour.WHITE),
    ]

    builder = FromPiecesBSB(piece_list)

    # Create a board and populate with pieces
    board = Board(builder)

    moves = board.get_move_list(Colour.BLACK)
    assert len(moves) == 1
    assert moves[0] == Move(start_B1, end_B, [start_W1, start_W2])

    # Execute the capture and check the board state
    board.move_piece(moves[0])

    assert board.get_piece(start_B1) is None
    assert board.get_piece(start_W1) is None
    assert board.get_piece(start_W2) is None
    end_B_piece = board.get_piece(end_B)
    assert end_B_piece is not None and end_B_piece.colour is Colour.BLACK


def test_chain_captures_multiple_routes() -> None:
    """Test a chain capture with multiple capturing routes."""
    # Board Layout:
    #    0  1  2  3  4  5
    # 0  b1
    # 1     w1
    # 2        ,
    # 3     w2   w3
    # 4  .           ,
    # 5          w4
    # 6        .

    # Coordinate Definitions:
    # Black piece starts at (0, 0)
    # First capture target at (1, 1)
    # After capturing (1,1) to (2,2), two capture options:
    # - Capture (3,1) to (4,0)
    # - Capture (3,3) to (4,4)
    # After capturing (3,3) to (4,4),
    # there is a final forced capture of (5,3) to (6,2)

    start_B = (0, 0)

    first_W = (1, 1)
    second_W2 = (3, 1)
    second_W3 = (3, 3)
    third_W4 = (5, 3)

    end_B1 = (4, 0)
    end_B2 = (6, 2)

    # Define the pieces on the board
    piece_list: list[Piece] = [
        Piece(start_B, Colour.BLACK),
        Piece(first_W, Colour.WHITE),
        Piece(second_W2, Colour.WHITE),
        Piece(second_W3, Colour.WHITE),
        Piece(third_W4, Colour.WHITE),
    ]

    # Build the board
    builder = FromPiecesBSB(piece_list)
    board = Board(builder)

    # Retrieve all possible moves for BLACK
    moves = board.get_move_list(Colour.BLACK)

    # Assert that there are exactly two capturing moves
    assert len(moves) == 2, f"Expected 2 moves, got {len(moves)}"

    # Define the expected moves
    expected_move1 = Move(start_B, end_B1, [first_W, second_W2])
    expected_move2 = Move(start_B, end_B2, [first_W, second_W3, third_W4])

    # Assert that both expected moves are present
    assert expected_move1 in moves, f"Move {expected_move1} not found in moves"
    assert expected_move2 in moves, f"Move {expected_move2} not found in moves"

    board.move_piece(expected_move2)

    # Verify the pieces after the move
    assert board.get_piece(start_B) is None, "Original black piece should be moved"
    assert board.get_piece(first_W) is None, "First white piece should be captured"
    assert board.get_piece(second_W3) is None, "Second white piece should be captured"
    assert board.get_piece(third_W4) is None, "Third white piece should be captured"

    end_B2_piece = board.get_piece(end_B2)
    assert (
        end_B2_piece is not None and end_B2_piece.colour is Colour.BLACK
    ), "Black piece should be at (6, 2)"

    # Ensure other pieces remain unaffected
    assert board.get_piece(second_W2) is not None, "W2 was not supposed to be captured"


def test_diamond_chain_capture() -> None:
    """Test a diamond-shaped two-layer chain capture with two routes leading to the same destination."""
    # Board Layout:
    #    0  1  2  3  4  5  6
    # 0
    # 1
    # 2        b1
    # 3     w1    w3
    # 4  ,           ,
    # 5     w2    w4
    # 6        .

    # Coordinate Definitions:
    # Black piece starts at (2, 2)
    # Path 1:
    #   - Capture w1 at (3, 1), land at (4, 0)
    #   - Capture w2 at (5, 1), land at (6, 2)
    # Path 2:
    #   - Capture w3 at (3, 3), land at (4, 4)
    #   - Capture w4 at (5, 3), land at (6, 2)

    start_B = (2, 2)
    capture_W1 = (3, 1)
    capture_W2 = (5, 1)
    capture_W3 = (3, 3)
    capture_W4 = (5, 3)
    end_position = (6, 2)

    # Define the pieces on the board
    piece_list: list[Piece] = [
        Piece(start_B, Colour.BLACK),
        Piece(capture_W1, Colour.WHITE),
        Piece(capture_W2, Colour.WHITE),
        Piece(capture_W3, Colour.WHITE),
        Piece(capture_W4, Colour.WHITE),
    ]

    # Build the board
    builder = FromPiecesBSB(piece_list)
    board = Board(builder)

    # Retrieve all possible moves for BLACK
    moves = board.get_move_list(Colour.BLACK)

    # Assert that there are exactly two capturing moves
    assert len(moves) == 2, f"Expected 2 capturing moves, got {len(moves)}"

    # Define the expected moves
    expected_move1 = Move(start_B, end_position, [capture_W1, capture_W2])
    expected_move2 = Move(start_B, end_position, [capture_W3, capture_W4])

    # Assert that both expected moves are present
    assert expected_move1 in moves, f"Move {expected_move1} not found in move list"
    assert expected_move2 in moves, f"Move {expected_move2} not found in move list"

    # Execute both moves and verify the board state
    for move in moves:
        board_after_move = copy.deepcopy(board)
        board_after_move.move_piece(move)

        # Verify the original black piece has moved
        assert board_after_move.get_piece(start_B) is None, "Original black piece should be moved"

        # Verify captured white pieces are removed
        for removed_sq in move.removed:
            assert (
                board_after_move.get_piece(removed_sq) is None
            ), f"Captured piece at {removed_sq} should be removed"

        # Verify the black piece is at the destination
        end_piece = board_after_move.get_piece(move.end)
        assert end_piece is not None, f"Black piece should be at {move.end}"
        assert end_piece.colour is Colour.BLACK, "Piece at destination should be black"

        # Ensure no other pieces are incorrectly removed
        remaining_pieces = [
            x for x in [capture_W1, capture_W2, capture_W3, capture_W4] if x not in move.removed
        ]
        for piece_pos in remaining_pieces:
            assert (
                board_after_move.get_piece(piece_pos) is not None
            ), f"Piece at {piece_pos} should remain on the board"

    print("test_diamond_chain_capture passed successfully.")
