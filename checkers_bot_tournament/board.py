from typing import Optional, Tuple

from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour, Piece


class Board:
    def __init__(self, size: int = 8):
        self.size = size  # Note that size must always be even
        if size % 2 != 0:
            raise ValueError("Even board sizes only.")

        self.grid: list[list[Optional[Piece]]] = [
            [None for _ in range(self.size)] for _ in range(self.size)
        ]

        self.move_history: list[Move] = []

        self.initialise_pieces()

    def initialise_pieces(self) -> None:
        """
        Initialises pieces on the board. The black pieces are from 0 to (half - 1)
        and the white pieces are from (half - 1) to size. There will always be
        a two row gap between the pieces to start with.
        """

        half = int(self.size / 2)
        # Init black pieces
        for row in range(half - 1):
            for col in range(self.size):
                if (row + col) % 2 == 1:
                    self.grid[row][col] = Piece((row, col), Colour.BLACK)

        # Init white pieces
        for row in range(half + 1, self.size):
            for col in range(self.size):
                if (row + col) % 2 == 1:
                    self.grid[row][col] = Piece((row, col), Colour.WHITE)

    def move_piece(self, move: Move) -> Tuple[bool, bool]:
        """
        Assume move is valid
        (i.e. in bounds, piece exists, vacant destination for normal move, or valid capturing move)

        Returns True if capture or promotion occured, else False
        """
        start_row, start_col = move.start
        end_row, end_col = move.end
        piece = self.grid[start_row][start_col]
        assert piece is not None

        # Perform the move
        self.grid[start_row][start_col] = None
        self.grid[end_row][end_col] = piece
        piece.position = move.end

        # Add move to move_history
        self.move_history.append(move)

        capture = False
        promotion = False

        if move.removed:
            rem_row, rem_col = move.removed
            self.grid[rem_row][rem_col] = None
            capture = True

        # Promote to king
        if (not piece.is_king) and (
            (piece.colour == Colour.WHITE and end_row == 0)
            or (piece.colour == Colour.BLACK and end_row == self.size - 1)
        ):
            piece.is_king = True
            promotion = True

        return (capture, promotion)

    def add_regular_move(self, moves: list[Move], row: int, col: int, dr: int, dc: int):
        end_row, end_col = row + dr, col + dc
        if (
            self.is_within_bounds(end_row, end_col)
            and self.grid[end_row][end_col] is None
        ):
            moves.append(Move((row, col), (end_row, end_col), None))

    def add_capture_move(
        self, moves: list[Move], colour: Colour, row: int, col: int, dr: int, dc: int
    ):
        capture_row, capture_col = row + 2 * dr, col + 2 * dc
        if not self.is_within_bounds(capture_row, capture_col):
            return

        mid_row, mid_col = row + dr, col + dc
        mid_piece: Optional[Piece] = self.grid[mid_row][mid_col]
        valid_capture_move = (
            self.grid[capture_row][capture_col] is None
            and mid_piece is not None
            and mid_piece.colour != colour
        )

        if valid_capture_move:
            moves.append(
                Move(
                    (row, col),
                    (capture_row, capture_col),
                    (mid_row, mid_col),
                )
            )

    def get_move_list(self, colour: Colour) -> list[Move]:
        moves: list[Move] = []

        # Directions for normal pieces
        forward_directions = (
            [(-1, -1), (-1, 1)] if colour == Colour.WHITE else [(1, -1), (1, 1)]
        )
        # Directions for kings (can move in all four diagonals)
        king_directions = forward_directions + [
            (-d[0], -d[1]) for d in forward_directions
        ]

        for row in range(self.size):
            for col in range(self.size):
                piece = self.get_piece((row, col))
                if piece and piece.colour == colour:
                    directions = (
                        king_directions if piece.is_king else forward_directions
                    )

                    for dr, dc in directions:
                        self.add_regular_move(moves, row, col, dr, dc)
                        self.add_capture_move(moves, colour, row, col, dr, dc)

        # Funny rule in checkers, if there is a capture move available, you MUST
        # take it, so here, if there are any capture moves, we filter to only
        # allow captures moves.
        capture_move_available = any([move.removed for move in moves])
        if capture_move_available:
            capture_moves = list(filter(lambda move: move.removed is not None, moves))
            return capture_moves

        # If no capture moves available, return all moves
        return moves

    def is_within_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def get_piece(self, position: Tuple[int, int]) -> Optional[Piece]:
        """Return the piece at a specific position."""
        row, col = position
        return (
            self.grid[row][col]
            if 0 <= row < self.size and 0 <= col < self.size
            else None
        )

    def get_move_history(self) -> list[Move]:
        return self.move_history

    def display_cell(self, cell: Optional[Piece], x: int, y: int) -> str:
        if not cell:
            if (x + y) % 2 == 0:
                return " "
            else:
                return "."

        match (cell.colour, cell.is_king):
            case (Colour.WHITE, False):
                return "w"
            case (Colour.WHITE, True):
                return "W"
            case (Colour.BLACK, False):
                return "b"
            case (Colour.BLACK, True):
                return "B"
            case _:
                raise ValueError("Unexpected piece state encountered.")

    def display(self) -> str:
        # Looks disgusting but yay pythom
        return (
            "\n".join(
                " ".join(self.display_cell(cell, x, y) for x, cell in enumerate(row))
                for y, row in enumerate(self.grid)
            )
            + "\n"
        )
