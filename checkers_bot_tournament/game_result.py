import inspect
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class Result(Enum):
    WHITE = auto()
    BLACK = auto()
    DRAW = auto()


@dataclass
class GameResult:
    game_id: int
    game_round: int

    result: Result

    white_name: str
    white_kings_made: int
    white_num_captures: int

    black_name: str
    black_kings_made: int
    black_num_captures: int

    num_moves: int
    # This is quite chunky (it stores every move and board state) so it's optional
    moves: Optional[str]

    def result_summary(self) -> str:
        match self.result:
            case Result.DRAW:
                # Arbitrarily White is player 1
                player1_stats = self.white_summary("White Player Details:")
                player2_stats = self.black_summary("Black Player Details:")
            case Result.WHITE:
                player1_stats = self.white_summary("Winner Details:")
                player2_stats = self.black_summary("Loser Details:")
            case Result.BLACK:
                player1_stats = self.black_summary("Winner Details:")
                player2_stats = self.white_summary("Loser Details:")

        string = inspect.cleandoc(f"""
        Game ID: {self.game_id}
        Game Round: {self.game_round}
        Winner: {self.winner_name if self.winner_name else 'Drawn Game'}
        Total Moves: {self.num_moves}

        {player1_stats}
        {player2_stats}
        """)

        return string

    def white_summary(self, header: str) -> str:
        string = f"""{header}
            Name: {self.white_name}
            Colour: White
            Kings Made: {self.white_kings_made}
            Number of Captures: {self.white_num_captures}"""
        return string

    def black_summary(self, header: str) -> str:
        string = f"""{header}
            Name: {self.black_name}
            Colour: Black
            Kings Made: {self.black_kings_made}
            Number of Captures: {self.black_num_captures}"""
        return string

    @property
    def winner_name(self) -> Optional[str]:
        match self.result:
            case Result.DRAW:
                return None
            case Result.WHITE:
                return self.white_name
            case Result.BLACK:
                return self.black_name

    @property
    def loser_name(self) -> Optional[str]:
        match self.result:
            case Result.DRAW:
                return None
            case Result.WHITE:
                return self.black_name
            case Result.BLACK:
                return self.white_name
