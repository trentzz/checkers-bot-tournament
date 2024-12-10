import os
from dataclasses import dataclass
from datetime import datetime
from typing import IO, Dict, Optional, Type

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.board_start_builder import (
    BoardStartBuilder,
    DefaultBSB,
    LastRowBSB,
)

# BOT TODO: Import your bot here!
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.bots.bot_tracker import BotTracker
from checkers_bot_tournament.bots.copycat import CopyCat
from checkers_bot_tournament.bots.first_mover import FirstMover
from checkers_bot_tournament.bots.greedycat import GreedyCat
from checkers_bot_tournament.bots.random_bot import RandomBot
from checkers_bot_tournament.bots.scaredycat import ScaredyCat
from checkers_bot_tournament.checkers_util import make_unique_bot_string
from checkers_bot_tournament.game import Game
from checkers_bot_tournament.game_result import GameResult, Result


@dataclass
class GameResultStat:
    white_wins: int = 0
    white_draws: int = 0
    white_losses: int = 0

    black_wins: int = 0
    black_draws: int = 0
    black_losses: int = 0


class Controller:
    # BOT TODO: Add your bot mapping here!
    bot_mapping: Dict[str, Type[Bot]] = {
        "RandomBot": RandomBot,
        "FirstMover": FirstMover,
        "ScaredyCat": ScaredyCat,
        "GreedyCat": GreedyCat,
        "CopyCat": CopyCat,
    }

    board_start_builder_mapping: Dict[str, Type[BoardStartBuilder]] = {
        "default": DefaultBSB,
        "last_row": LastRowBSB,
    }

    def __init__(
        self,
        mode: str,
        board_start_builder: str,
        pdn: Optional[str],
        bot_name: Optional[str],
        bot_names: list[str],
        size: int,
        rounds: int,
        verbose: bool,
        output_dir: str,
        export_pdn: bool,
    ):
        self.mode = mode

        self.board_start_builder: BoardStartBuilder = self._get_board_start_builder(
            board_start_builder
        )

        self.pdn = pdn
        self.bot_name = bot_name

        self.bot_list: list[BotTracker] = self._init_bots(bot_names)

        # NOTE: size currently not used
        self.size = size
        self.rounds = rounds
        self.verbose = verbose
        self.output_dir = output_dir
        self.export_pdn = export_pdn

        # Inits for non-params
        # List of rounds, each round being a list of games
        self.games: list[list[Game]] = [[] for _ in range(rounds)]
        self.game_results: list[list[GameResult]] = [[] for _ in range(rounds)]
        self.game_id_counter: int = 0
        self.game_results_folder: Optional[str] = None

        self._init_game_schedule()

    def _init_bots(self, bot_names: list[str]) -> list[BotTracker]:
        unrecognised_bots = []
        bot_list: list[BotTracker] = []
        for bot in bot_names:
            if bot not in Controller.bot_mapping:
                unrecognised_bots.append(bot)

        if unrecognised_bots:
            raise ValueError(f"bots: {', '.join(unrecognised_bots)} entered in CLI not recognised!")

        for idx, bot_name in enumerate(bot_names):
            bot_class = self.bot_mapping[bot_name]
            bot_list.append(BotTracker(bot=bot_class(bot_id=idx)))

        return bot_list

    def _init_game_schedule(self) -> None:
        match self.mode:
            case "all":
                assert self.bot_name is None, "--player should not be set if running on all mode"
                self._init_all_schedule()
            case "one":
                assert self.bot_name, "--player must be set in one mode"
                try:
                    # Special case: we set the bot id to -1 since the list starts at 0
                    # kinda hacky but uh :D
                    bot_class = self.bot_mapping[self.bot_name]
                    hero_bot = BotTracker(bot_class(bot_id=-1))
                except KeyError:
                    raise ValueError(f"bot name {self.bot_name} entered in CLI not recognised!")
                self._init_one_schedule(hero_bot)
            case _:
                raise ValueError(f"mode value {self.mode} not recognised!")

        if self.verbose:
            games_per_round = len(self.games[0])
            total = len(self.games[0]) * self.rounds
            print(f"{len(self.bot_list)} bots registered")
            print(
                f"{games_per_round} double-round-robin games/tourney * {self.rounds} tourneys = {total} games scheduled"
            )

    def _init_all_schedule(self) -> None:
        """
        Schedules all bots against each other, where each pairing plays as both sides in each round
        """
        for rnd in range(self.rounds):
            for id1, bot1 in enumerate(self.bot_list):
                for id2, bot2 in enumerate(self.bot_list):
                    if id1 < id2:
                        self._schedule_pair_game(bot1, bot2, rnd)

    def _init_one_schedule(self, hero_bot: BotTracker) -> None:
        """
        Runs the one bot against all bots in the bot list
        """
        for rnd in range(self.rounds):
            for id2, other in enumerate(self.bot_list):
                self._schedule_pair_game(hero_bot, other, rnd)

    def _schedule_pair_game(self, bot1: BotTracker, bot2: BotTracker, rnd: int) -> None:
        new_game1 = Game(
            bot1,
            bot2,
            Board(self.board_start_builder),
            self._get_new_game_id(),
            rnd,
            self.verbose,
            self.pdn,
        )
        new_game2 = Game(
            bot2,
            bot1,
            Board(self.board_start_builder),
            self._get_new_game_id(),
            rnd,
            self.verbose,
            self.pdn,
        )
        self.games[rnd].append(new_game1)
        self.games[rnd].append(new_game2)

    def _get_new_game_id(self) -> int:
        self.game_id_counter += 1
        return self.game_id_counter

    def _get_board_start_builder(self, board_start_builder: str) -> BoardStartBuilder:
        if board_start_builder not in Controller.board_start_builder_mapping:
            raise ValueError(f"board_state: {board_start_builder} not recognised!")

        board_start_builder_class = Controller.board_start_builder_mapping[board_start_builder]
        return board_start_builder_class(self.size)

    def _create_timestamped_folder(self, prefix: str = "checkers_game_results") -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        folder_name = f"{prefix}_{timestamp}"
        folder_path = os.path.join(self.output_dir, folder_name)

        # Create the folder
        os.makedirs(folder_path, exist_ok=True)
        self.game_results_folder = folder_path

    ###################################
    #  ^^^ Initialising functions ^^^ #
    ###################################

    def run(self) -> None:
        self._create_timestamped_folder()
        for rnd in range(self.rounds):
            for game in self.games[rnd]:
                ev_white = game.white.calculate_ev(game.black)
                ev_black = 1 - ev_white
                
                # Sum of EV score for each player
                # based on all games they will play in this tournaments
                game.white.register_ev(ev_white)
                game.black.register_ev(ev_black)

            for game in self.games[rnd]:
                game_result = game.run()
                self.game_results[rnd].append(game_result)

                match game_result.result:
                    case Result.WHITE:
                        game.white.stats.white_wins += 1
                        game.black.stats.black_losses += 1
                    case Result.BLACK:
                        game.white.stats.white_losses += 1
                        game.black.stats.black_wins += 1
                    case Result.DRAW:
                        game.white.stats.white_draws += 1
                        game.black.stats.black_draws += 1

            self._write_game_results(self.game_results[rnd])

            # Calculate Elo at the end of all matches in a round
            for game, game_result in zip(self.games[rnd], self.game_results[rnd]):
                lookup = {Result.WHITE: 1, Result.BLACK: 0, Result.DRAW: 0.5}

                game.white.register_result(lookup[game_result.result])
                game.black.register_result(1 - lookup[game_result.result])

            for bot in self.bot_list:
                bot.update_rating()

            if self.verbose:
                print(f"Round {rnd} completed")

        if self.verbose:
            print("Tournament completed, writing stats")
        self._write_tournament_results()

    def _write_game_result_summary(self, file: IO, game_result: GameResult) -> None:
        file.write(str(game_result))
        file.write("\n" + "=" * 40 + "\n")

    def _write_game_results(self, game_results: list[GameResult]) -> None:
        assert self.game_results_folder is not None
        game_result_summary_path = os.path.join(self.game_results_folder, "game_result_summary.txt")
        with open(game_result_summary_path, "a", encoding="utf-8") as file:
            for game_result in game_results:
                self._write_game_result_summary(file, game_result)
                if game_result.moves:
                    game_result_moves_path = os.path.join(
                        self.game_results_folder, f"game_{game_result.game_id}.txt"
                    )
                    with open(game_result_moves_path, "w", encoding="utf-8") as moves_file:
                        self._write_game_result_summary(moves_file, game_result)
                        moves_file.write("Moves: \n")
                        moves_file.write(game_result.moves)

                if self.export_pdn:
                    game_result_pdn_path = os.path.join(
                        self.game_results_folder, f"game_{game_result}.pdn"
                    )
                    with open(game_result_pdn_path, "w") as pdn_file:
                        pdn_file.write(game_result.moves_pdn)

    def _write_tournament_result_stats(self, file: IO) -> None:
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

        for bot in self.bot_list:
            stats = bot.stats
            file.write(f"Bot Name: {make_unique_bot_string(bot)} ({round(bot.rating)})\n")
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

    def _write_tournament_results(self) -> None:
        assert self.game_results_folder is not None
        game_result_stats_path = os.path.join(self.game_results_folder, "game_result_stats.txt")

        # game_result_map: Dict[str, GameResultStat] = {}
        # if self.bot_name:
        #     game_result_map[make_unique_bot_string(-1, self.bot_name)] = GameResultStat()
        # for bot in self.bot_list:
        #     game_result_map[make_unique_bot_string(bot)] = GameResultStat()

        # for game in chain.from_iterable(self.games):
        #     game_result = game.game_result
        #     assert game_result

        #     match game_result.result:
        #         case Result.WHITE:
        #             game_result_map[game_result.white_name].white_wins += 1
        #             game_result_map[game_result.black_name].black_losses += 1
        #         case Result.BLACK:
        #             game_result_map[game_result.white_name].white_losses += 1
        #             game_result_map[game_result.black_name].black_wins += 1
        #         case Result.DRAW:
        #             game_result_map[game_result.white_name].white_draws += 1
        #             game_result_map[game_result.black_name].black_draws += 1

        with open(game_result_stats_path, "w", encoding="utf-8") as file:
            self._write_tournament_result_stats(file)
