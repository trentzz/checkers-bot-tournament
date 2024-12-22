from dataclasses import dataclass
from typing import Optional, Tuple


# TODO: check inside board methods too (smartly and efficiently)
class IllegalMoveException(ValueError):
    """
    The Move object supplied to the Board is not legal in this position.
    """


@dataclass(frozen=True)
class Move:
    start: Tuple[int, int]
    end: Tuple[int, int]
    removed: Optional[Tuple[int, int]]

    def __repr__(self) -> str:
        return f"Move({self.start}, {self.end}, {self.removed})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Move):
            return False
        return self.start == other.start and self.end == other.end and self.removed == other.removed
