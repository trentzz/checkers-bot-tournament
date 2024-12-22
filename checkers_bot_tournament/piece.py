from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple

from checkers_bot_tournament.game_result import Result


class Colour(Enum):
    WHITE = auto()
    BLACK = auto()

    def get_opposite(self) -> "Colour":
        if self == Colour.WHITE:
            return Colour.BLACK
        elif self == Colour.BLACK:
            return Colour.WHITE

    def as_result(self) -> Result:
        if self == Colour.WHITE:
            return Result.WHITE
        elif self == Colour.BLACK:
            return Result.BLACK


@dataclass
class Piece:
    position: Tuple[int, int]
    colour: Colour
    is_king: bool = False
