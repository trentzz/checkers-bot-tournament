from checkers_bot_tournament.piece import Colour


def test_colour():
    white = Colour.WHITE
    black = Colour.BLACK

    assert white.get_opposite() == black
