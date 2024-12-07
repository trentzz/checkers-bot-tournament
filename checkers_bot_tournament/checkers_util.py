from typing import overload

from checkers_bot_tournament.bots.base_bot import Bot


@overload
def make_unique_bot_string(idx: int, bot: str) -> str: ...


@overload
def make_unique_bot_string(bot: Bot) -> str: ...


def make_unique_bot_string(*args, **kwargs) -> str:
    """
    This exists because we can have multiple of the same bot playing each other
    so we need a way to differentiate them.
    """
    # Runtime implementation:
    if len(args) == 1 and isinstance(args[0], Bot):
        bot = args[0]
        return f"[{bot.bot_id}] {bot.get_name()}"
    elif len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], str):
        idx, bot_str = args
        return f"[{idx}] {bot_str}"
    else:
        raise TypeError("Invalid arguments to make_unique_bot_string")
