import os
import time
from dataclasses import dataclass
from datetime import datetime
from multiprocessing import Pool
from queue import Queue
from threading import Thread
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
from checkers_bot_tournament.game_result import GameResult
from checkers_bot_tournament.stat_printing import (
    write_tournament_h2h_stats,
    write_tournament_overall_stats,
)


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
        protagonist_bot_name: Optional[str],
        bot_names: list[str],
        size: int,
        rounds: int,
        verbose: bool,
        output_dir: str,
        export_pdn: bool,
    ):
        self.mode = mode

        # NOTE: size currently not used
        self.size = size
        self.board_start_builder: BoardStartBuilder = self._get_board_start_builder(
            board_start_builder
        )

        self.pdn = pdn
        self.protagonist_bot_name = protagonist_bot_name
        self.protagonist_tracker: Optional[BotTracker] = None

        self.bot_list: list[BotTracker] = self._init_bots(bot_names)

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
        self.write_queue: Queue[Optional[tuple[list[GameResult], int]]] = Queue()
        self.writer_thread = Thread(target=self._writer_worker, daemon=True)

        self._init_game_schedule()

    def _init_bots(self, bot_names: list[str]) -> list[BotTracker]:
        unrecognised_bots = []
        bot_list: list[BotTracker] = []
        for bot in bot_names:
            if bot not in Controller.bot_mapping:
                unrecognised_bots.append(bot)

        if unrecognised_bots:
            raise ValueError(f"bots: {', '.join(unrecognised_bots)} entered in CLI not recognised!")

        idx_bot_names: list[tuple[int, str]] = [
            (idx, bot_name) for idx, bot_name in enumerate(bot_names)
        ]

        unique_bot_names = list(map(lambda x: make_unique_bot_string(x[0], x[1]), idx_bot_names))
        # If selected, player bot (idx -1) needs to be added to the list for other BotTrackers.
        # It will actually get initialised later in _init_game_schedule()
        if self.protagonist_bot_name:
            unique_bot_names.append(make_unique_bot_string(-1, self.protagonist_bot_name))

        for idx, bot_name in idx_bot_names:
            bot_class = self.bot_mapping[bot_name]
            bot_list.append(
                BotTracker(bot_class=bot_class, bot_id=idx, unique_bot_names=unique_bot_names)
            )

        return bot_list

    def _init_game_schedule(self) -> None:
        match self.mode:
            case "all":
                assert (
                    self.protagonist_bot_name is None
                ), "--bot [NAME] should not be set if running on all mode"
                self._init_all_schedule()
            case "one":
                assert self.protagonist_bot_name, "--bot [NAME] must be set in one mode"
                try:
                    # Special case: we set the bot id to -1 since the list starts at 0
                    # kinda hacky but uh :D
                    unique_bot_names = list(map(make_unique_bot_string, self.bot_list))
                    bot_class = self.bot_mapping[self.protagonist_bot_name]
                    self.protagonist_tracker = BotTracker(
                        bot_class=bot_class, bot_id=-1, unique_bot_names=unique_bot_names
                    )
                except KeyError as _:
                    raise ValueError(
                        f"bot name {self.protagonist_bot_name} entered in CLI not recognised!"
                    ) from _
                self._init_one_schedule(self.protagonist_tracker)
            case _:
                raise ValueError(f"mode value {self.mode} not recognised!")

        if self.verbose:
            games_per_round = len(self.games[0])
            total = len(self.games[0]) * self.rounds
            mode_str = "double-round-robin games" if self.mode == "all" else "one-vs-all games"
            print(f"{len(self.bot_list)} bots registered")
            print(
                f"{games_per_round} {mode_str}/tourney * {self.rounds} tourneys = {total} games scheduled"
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

    def _init_one_schedule(self, protagonist_bot: BotTracker) -> None:
        """
        Runs the one bot against all bots in the bot list
        """
        for rnd in range(self.rounds):
            for id2, other in enumerate(self.bot_list):
                self._schedule_pair_game(protagonist_bot, other, rnd)

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
        self.writer_thread.start()
        for rnd in range(self.rounds):
            t0 = time.time()

            with Pool() as pool:
                self.game_results[rnd] = pool.map(Game.run, self.games[rnd])
            # for game in self.games[rnd]:
            #     game_result = game.run()
            #     self.game_results[rnd].append(game_result)

            # Add task of recording all games in the round to writer thread
            self.write_queue.put((self.game_results[rnd], rnd))
            # self._write_game_results(self.game_results[rnd])

            # Calculate Elo at the end of all matches in a round
            for game, game_result in zip(self.games[rnd], self.game_results[rnd]):
                ev_white = game.white_tracker.calculate_ev(game.black_tracker)
                ev_black = 1 - ev_white

                game.white_tracker.register_ev(ev_white)
                game.black_tracker.register_ev(ev_black)

                game.white_tracker.register_game_result(game_result)
                game.black_tracker.register_game_result(game_result)

            for bot in self.bot_list:
                bot.update_rating()
            if self.protagonist_tracker:
                self.protagonist_tracker.update_rating()

            t1 = time.time()
            if self.verbose:
                print(f"Tournament {rnd} completed in {round(t1-t0, 1)} seconds")

        if self.verbose:
            print("All games completed, writing summary stats...")

        # Wait until all write tasks are completed
        self.write_queue.join()
        # Enqueue the sentinel to signal the writer thread to exit
        self.write_queue.put(None)
        self.writer_thread.join()

        self._write_tournament_results()

    def _writer_worker(self) -> None:
        """
        Worker thread that continuously listens to the write_queue and writes game results.
        """
        while True:
            tup = self.write_queue.get()
            if tup is None:
                # Sentinel received, exit the thread
                self.write_queue.task_done()
                break
            game_results, rnd = tup
            self._write_game_results(game_results, rnd)
            self.write_queue.task_done()

    def _write_game_result_summary(self, file: IO, game_result: GameResult) -> None:
        file.write(str(game_result))
        file.write("\n" + "=" * 40 + "\n")

    def _write_game_results(self, game_results: list[GameResult], round_number: int) -> None:
        # Summary for each game
        assert self.game_results_folder is not None
        game_result_summary_path = os.path.join(self.game_results_folder, "game_result_summary.txt")
        with open(game_result_summary_path, "a", encoding="utf-8") as file:
            for game_result in game_results:
                self._write_game_result_summary(file, game_result)

        if not (self.verbose or self.pdn):
            # Nothing else to print out
            return

        # Move by move report for each game if verbose/PDN options selected
        # They both go in round subfolder
        round_subfolder_name = f"round_{round_number}"
        round_folder_path = os.path.join(self.game_results_folder, round_subfolder_name)
        os.makedirs(round_folder_path, exist_ok=True)

        for game_result in game_results:
            white_name = "".join(game_result.white_name.split(" ")[1:])
            black_name = "".join(game_result.black_name.split(" ")[1:])

            if self.verbose:
                game_result_moves_path = os.path.join(
                    round_folder_path,
                    f"game_{game_result.game_id}_{white_name}_{black_name}.txt",
                )
                with open(game_result_moves_path, "w", encoding="utf-8") as moves_file:
                    self._write_game_result_summary(moves_file, game_result)
                    moves_file.write("Moves: \n")
                    moves_file.write(game_result.moves)

            if self.export_pdn:
                game_result_pdn_path = os.path.join(
                    round_folder_path,
                    f"game_{game_result.game_id}_{white_name}_{black_name}.pdn",
                )
                with open(game_result_pdn_path, "w") as pdn_file:
                    pdn_file.write(game_result.moves_pdn)

    def _write_tournament_results(self) -> None:
        assert self.game_results_folder is not None
        game_result_stats_path = os.path.join(self.game_results_folder, "game_result_stats.txt")

        with open(game_result_stats_path, "w", encoding="utf-8") as file:
            write_tournament_overall_stats(
                self.bot_list, file, protagonist_tracker=self.protagonist_tracker
            )
            write_tournament_h2h_stats(
                self.bot_list, file, protagonist_tracker=self.protagonist_tracker
            )
