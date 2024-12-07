from typing import Optional, Tuple


class Move:
    def __init__(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        removed: Optional[Tuple[int, int]],
    ):
        self.start = start
        self.end = end
        self.removed = removed
