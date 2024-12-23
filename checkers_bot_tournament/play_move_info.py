from dataclasses import dataclass
from typing import Optional

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour


@dataclass
class PlayMoveInfo:
    board: Board  # represents the current state of the board
    colour: Colour  # the colour the bot has to play
    move_list: list[Move]  # a list of allowable moves
    move_history: list[Move]  # history of the moves played in the game
    last_action_move: int  # last move which an action happened

    # optional field for any bot to return its evaluation of the position
    pos_eval: Optional[float]
