from typing import Optional, Tuple

from checkers_bot_tournament.board_start_builder import BoardStartBuilder
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour, Piece

Grid = list[list[Optional[Piece]]]


class Board:
    def __init__(self, board_start_builder: BoardStartBuilder, size: int = 8):
        self.size = size  # Note that size must always be even
        if size % 2 != 0:
            raise ValueError("Even board sizes only.")

        self.grid: Grid = board_start_builder.build()

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
        if self.is_within_bounds(end_row, end_col) and self.grid[end_row][end_col] is None:
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

    def is_valid_move(self, colour: Colour, move: Move) -> bool:
        return move in self.get_move_list(colour)

    def get_move_list(self, colour: Colour) -> list[Move]:
        moves: list[Move] = []

        # Directions for normal pieces
        forward_directions = [(-1, -1), (-1, 1)] if colour == Colour.WHITE else [(1, -1), (1, 1)]
        # Directions for kings (can move in all four diagonals)
        king_directions = forward_directions + [(-d[0], -d[1]) for d in forward_directions]

        for row in range(self.size):
            for col in range(self.size):
                piece = self.get_piece((row, col))
                if piece and piece.colour == colour:
                    directions = king_directions if piece.is_king else forward_directions

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
        return self.grid[row][col] if 0 <= row < self.size and 0 <= col < self.size else None

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

    def _to_bitboards(self):
        """
        Since there are 4 piece types + blank, this are 3 bits of information per square.
        Note also, player to move is not required:

        Although you play checkers only on the black squares, if you turn your head around,
        it's a chessboard, in that for non-capturing moves you are going from one colour to another.
        Your opponent moves into a 'dark' square, then you move into a 'dark square,
        then 'light' and 'light' and so on.

        That's all to say, as far as I know, there is no triangulation/way to lose a move
        to your opponent with a king (of course, any man move is not reversible since they
        go forwards only.) Would love to be proven wrong though!!

        So we convert the board into three bitboards:
        - white_pieces: bits set where white pieces are located
        - black_pieces: bits set where black pieces are located
        - kings: bits set where kings are located

        Board indexing (row major):
        index = row * size + col
        """
        white_pieces = 0
        black_pieces = 0
        kings = 0

        # There are only 32 squares in a checkerboard, you can use 32 bit
        # but oh well 64 bit integers will be tad slower
        for r in range(self.size):
            for c in range(self.size):
                piece = self.grid[r][c]
                if piece is not None:
                    index = r * self.size + c
                    bit = 1 << index
                    if piece.colour == Colour.WHITE:
                        white_pieces |= bit
                    else:
                        black_pieces |= bit
                    if piece.is_king:
                        kings |= bit
        return white_pieces, black_pieces, kings

    def __hash__(self):
        return hash(self._to_bitboards())

    def __eq__(self, other):
        if not isinstance(other, Board):
            return False
        return self._to_bitboards() == other._to_bitboards()
