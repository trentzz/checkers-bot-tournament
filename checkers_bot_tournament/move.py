from dataclasses import dataclass


# TODO: check inside board methods too (smartly and efficiently)
class IllegalMoveException(ValueError):
    """
    The Move object supplied to the Board is not legal in this position.
    """


@dataclass(frozen=True)
class Move:
    start: tuple[int, int]
    end: tuple[int, int]
    removed: list[tuple[int, int]]

    def get_intermediate_squares(self) -> list[tuple[int, int]]:
        """
        Return the intermediate squares that the piece lands on after each capture
        including reaching the final end position.
        tuples are row, cols
        """
        if not self.removed:
            return [self.end]

        intermediate_positions = []
        current_pos = self.start

        for captured_pos in self.removed:
            r_1, c_1 = current_pos
            r_2, c_2 = captured_pos

            # Landing square is start + twice the vector from start to the captured piece
            next_pos = (r_1 + 2 * (r_2 - r_1), c_1 + 2 * (c_2 - c_1))
            intermediate_positions.append(next_pos)
            current_pos = next_pos

        # By the end, current_pos should match move.end,
        # if the move and removed list are consistent.
        if current_pos != self.end:
            # This might indicate the removed list isn't in a correct capture order
            raise ValueError(
                f"Calculated chain end {current_pos} does not match the move's end position {self.removed}"
            )

        return intermediate_positions

    def __repr__(self) -> str:
        return f"Move({self.start}, {self.end}, {self.removed})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Move):
            return False
        return (
            self.start == other.start
            and self.end == other.end
            and len(self.removed) == len(other.removed)
            and set(self.removed) == set(other.removed)
        )
