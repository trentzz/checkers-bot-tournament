import os
from dataclasses import dataclass
from datetime import datetime
from typing import IO, Dict, Optional, Type

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.bots.copycat import CopyCat
from checkers_bot_tournament.bots.first_mover import FirstMover
from checkers_bot_tournament.bots.greedycat import GreedyCat

# BOT TODO: Import your bot here!
from checkers_bot_tournament.bots.random_bot import RandomBot
from checkers_bot_tournament.bots.scaredycat import ScaredyCat
from checkers_bot_tournament.checkers_util import make_unique_bot_string
from checkers_bot_tournament.game import Game
from checkers_bot_tournament.game_result import GameResult, Result


@dataclass
class UniqueBot:
    idx: int
    name: str


@dataclass
class GameResultStat:
    white_wins: int = 0
    white_draws: int = 0
    white_losses: int = 0

    black_wins: int = 0
    black_draws: int = 0
    black_losses: int = 0


class Controller:
    def __init__(
        self,
        mode: str,
        bot: Optional[str],
        bot_list: list[str],
        size: int,
        rounds: int,
        verbose: bool,
        output_dir: str,
    ):
        self.mode = mode
        self.bot = bot

        # NOTE: From design perspective, I think it's better to verify bots at this point
        # using the bot mapping, then keeping a list of bot classes.
        self.bot_list = bot_list
        # NOTE: size currently not used
        self.size = size
        self.rounds = rounds
        self.verbose = verbose
        self.output_dir = output_dir

        # Inits for non-params
        self.game_results: list[GameResult] = []
        self.game_id_counter: int = 0
        # self.game_results_folder: Optional[str] = None

        # BOT TODO: Add your bot mapping here!
        self.bot_mapping: Dict[str, Type[Bot]] = {
            "RandomBot": RandomBot,
            "FirstMover": FirstMover,
            "ScaredyCat": ScaredyCat,
            "GreedyCat": GreedyCat,
            "CopyCat": CopyCat,
        }

    def run(self) -> None:
        self._create_timestamped_folder()
        match self.mode:
            case "all":
                assert (
                    self.bot is None
                ), "--player should not be set if running on all mode"
                self._run_all()
            case "one":
                assert self.bot, "--player must be set in one mode"
                self._run_one(self.bot)
            case _:
                raise ValueError(f"mode value {self.mode} not recognised!")

        self._write_game_results()

    def _create_timestamped_folder(self, prefix: str = "checkers_game_results") -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        folder_name = f"{prefix}_{timestamp}"
        folder_path = os.path.join(self.output_dir, folder_name)

        # Create the folder
        os.makedirs(folder_path, exist_ok=True)

        self.game_results_folder = folder_path

    def _return_bot_class(self, bot: UniqueBot) -> Bot:
        if bot.name in self.bot_mapping:
            bot_class = self.bot_mapping[bot.name]
            return bot_class(bot_id=bot.idx)
        else:
            raise ValueError(f"bot name {bot.name} entered in CLI not recognised!")

    def _run_all(self) -> None:
        """
        Runs all bots against each other
        """
        for idx, bot in enumerate(self.bot_list):
            for idy, other in enumerate(self.bot_list):
                if idx >= idy:
                    continue

                self._run_games(UniqueBot(idx, bot), UniqueBot(idy, other))

    def _run_one(self, bot: str) -> None:
        """
        Runs the one bot against all bots in the bot list
        """
        for idy, other in enumerate(self.bot_list):
            # Special case: we set the bot id to -1 since the list starts at 0
            # kinda hacky but uh :D
            self._run_games(UniqueBot(-1, bot), UniqueBot(idy, other))

    def _run_game(
        self, white: UniqueBot, black: UniqueBot, game_id: int, game_round: int
    ) -> None:
        white_bot = self._return_bot_class(white)
        black_bot = self._return_bot_class(black)

        game = Game(white_bot, black_bot, Board(), game_id, game_round, self.verbose)
        game.run()
        self.game_results.append(game.get_game_result())

    def _get_new_game_id(self) -> int:
        self.game_id_counter += 1
        return self.game_id_counter

    def _run_games(self, bot: UniqueBot, other: UniqueBot) -> None:
        for r in range(1, self.rounds + 1):
            self._run_game(bot, other, self._get_new_game_id(), r)
            self._run_game(other, bot, self._get_new_game_id(), r)

    def _write_game_result_summary(self, file: IO, game: GameResult) -> None:
        file.write(game.result_summary())
        file.write("\n" + "=" * 40 + "\n")

    def _write_game_result_stats(
        self, file: IO, game_stats: Dict[str, GameResultStat]
    ) -> None:
        """
        Writes game result statistics to a file in a structured and readable format.

        The format includes a header row followed by counts and percentages for
        White, Black, and Overall statistics for each bot.

        Shamelessly crafted with ChatGPT :)

        Args:
            file: The file object to write the statistics to.
            game_stats (Dict[str, GameResultStat]): A dictionary mapping bot names to their game statistics.
        """
        file.write("Game Statistics\n")
        file.write("=" * 60 + "\n\n")

        for bot_name, stats in game_stats.items():
            file.write(f"Bot Name: {bot_name}\n")
            file.write("-" * 60 + "\n")

            label_width = 10  # For "White", "Black", "Overall"
            col_width = 8  # For "Win", "Draw", "Loss" columns

            # Print the header row once per bot
            header = f"{'Win':<{col_width}}{'Draw':<{col_width}}{'Loss':<{col_width}}"
            file.write(f"{'':<{label_width}}{header}\n")

            # Compute Overall stats
            overall_wins = stats.white_wins + stats.black_wins
            overall_draws = stats.white_draws + stats.black_draws
            overall_losses = stats.white_losses + stats.black_losses

            # Organize counts for White, Black, and Overall
            counts = {
                "White": (stats.white_wins, stats.white_draws, stats.white_losses),
                "Black": (stats.black_wins, stats.black_draws, stats.black_losses),
                "Overall": (overall_wins, overall_draws, overall_losses),
            }

            # Print absolute counts
            for label, (w, d, l) in counts.items():
                counts_str = f"{w:<{col_width}}{d:<{col_width}}{l:<{col_width}}"
                file.write(f"{label:<{label_width}}{counts_str}\n")

            # Calculate and print percentages
            for label, (w, d, l) in counts.items():
                total_games = w + d + l
                if total_games > 0:
                    win_pct = (w / total_games) * 100
                    draw_pct = (d / total_games) * 100
                    loss_pct = (l / total_games) * 100
                    score_pct = ((w + 0.5 * d) / total_games) * 100
                else:
                    win_pct = draw_pct = loss_pct = score_pct = 0.0

                # Format each percentage including the % sign within the column
                win_str = f"{win_pct:.1f}%"
                draw_str = f"{draw_pct:.1f}%"
                loss_str = f"{loss_pct:.1f}%"
                score_str = f"{score_pct:.2f}%"

                pct_str = (
                    f"{label:<{label_width}}"
                    f"{win_str:<{col_width}}"
                    f"{draw_str:<{col_width}}"
                    f"{loss_str:<{col_width}}"
                    f"= {score_str}"
                )
                file.write(pct_str + "\n")

            file.write("=" * 60 + "\n\n")

    def _write_game_results(self) -> None:
        game_result_summary_path = os.path.join(
            self.game_results_folder, "game_result_summary.txt"
        )
        with open(game_result_summary_path, "w", encoding="utf-8") as file:
            for game in self.game_results:
                self._write_game_result_summary(file, game)
                if game.moves:
                    game_result_moves_path = os.path.join(
                        self.game_results_folder, f"game_{game.game_id}.txt"
                    )
                    with open(
                        game_result_moves_path, "w", encoding="utf-8"
                    ) as moves_file:
                        self._write_game_result_summary(moves_file, game)
                        moves_file.write("Moves: \n")
                        moves_file.write(game.moves)

        game_result_stats_path = os.path.join(
            self.game_results_folder, "game_result_stats.txt"
        )

        game_result_map: Dict[str, GameResultStat] = {}
        if self.bot:
            game_result_map[make_unique_bot_string(-1, self.bot)] = GameResultStat()
        for idx, name in enumerate(self.bot_list):
            game_result_map[make_unique_bot_string(idx, name)] = GameResultStat()

        for game in self.game_results:
            # Add winner
            if game.result == Result.WHITE:
                game_result_map[game.white_name].white_wins += 1
                game_result_map[game.black_name].black_losses += 1
            elif game.result == Result.BLACK:
                game_result_map[game.white_name].white_losses += 1
                game_result_map[game.black_name].black_wins += 1
            else:
                game_result_map[game.white_name].white_draws += 1
                game_result_map[game.black_name].black_draws += 1

        with open(game_result_stats_path, "w", encoding="utf-8") as file:
            self._write_game_result_stats(file, game_result_map)
