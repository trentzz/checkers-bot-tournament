from datetime import datetime
import os
from typing import Optional, Dict
from dataclasses import dataclass
from checkers_bot_tournament.game import Game
from checkers_bot_tournament.game_result import GameResult
from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.checkers_util import make_unique_bot_string

# BOT TODO: Import your bot here!
from checkers_bot_tournament.bots.random_bot import RandomBot
from checkers_bot_tournament.bots.first_mover import FirstMover

@dataclass
class UniqueBot:
    idx: int
    name: str
    
@dataclass
class GameResultStat:
    white_wins: int
    white_losses: int
    black_wins: int
    black_losses: int

class Controller:
    def __init__(self, mode: str, bot: Optional[str], bot_list: Optional[list[str]], size: int, rounds: int, verbose: bool, output_dir: str):
        self.mode = mode
        self.bot = bot
        self.bot_list = bot_list
        self.size = size
        self.rounds = rounds
        self.verbose = verbose
        self.output_dir = output_dir
        
        # Inits for non-params
        self.game_results: list[GameResult] = []
        self.game_id_counter: int = 0
        self.game_results_folder: str = None
        
        # BOT TODO: Add your bot mapping here!
        self.bot_mapping: Dict[str, Bot] = {
            "RandomBot": RandomBot,
            "FirstMover": FirstMover
        }
        
    def run(self):
        self.create_timestamped_folder()
        match self.mode:
            case "all":
                assert self.bot is None, "--player should not be set if running on all mode"
                self.run_all()
            case "one":
                assert self.bot, "--player must be set in one mode"
                self.run_one()
            case _:
                raise RuntimeError("mode value not recognised!")
            
        self.write_game_results()
        
        
    def create_timestamped_folder(self, prefix: str = "checkers_game_results"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        folder_name = f"{prefix}_{timestamp}"
        folder_path = os.path.join(self.output_dir, folder_name)
        
        # Create the folder
        os.makedirs(folder_path, exist_ok=True)
        
        self.game_results_folder = folder_path
            
    def return_bot_class(self, bot: UniqueBot) -> Bot:
        if bot.name in self.bot_mapping:
            return self.bot_mapping[bot.name](bot.idx)

    def run_all(self):
        """
        Runs all bots against each other
        """
        for idx, bot in enumerate(self.bot_list):
            for idy, other in enumerate(self.bot_list):
                if idx == idy:
                    continue

                self.run_games(UniqueBot(idx, bot), UniqueBot(idy, other))
    
    def run_one(self):
        """
        Runs the one bot against all bots in the bot list
        """
        for idy, other in enumerate(self.bot_list):
            # Special case: we set the bot id to -1 since the list starts at 0
            # kinda hacky but uh :D
            self.run_games(UniqueBot(-1, self.bot), UniqueBot(idy, other))
    
    def run_game(self, white: UniqueBot, black: UniqueBot, game_id: int, game_round: int):
        white_bot = self.return_bot_class(white)
        black_bot = self.return_bot_class(black)
        
        game = Game(white_bot, black_bot, Board(), game_id, game_round, self.verbose)
        game.run()
        self.game_results.append(game.get_game_result())
        
    def get_new_game_id(self):
        self.game_id_counter += 1
        return self.game_id_counter
    
    def run_games(self, bot: UniqueBot, other: UniqueBot):
        for r in range(1, self.rounds + 1):
            self.run_game(bot, other, self.get_new_game_id(), r)
            self.run_game(other, bot, self.get_new_game_id(), r)
            
    def write_game_result_summary(self, file, game: GameResult) -> None:
        # TODO: Format this better
        file.write(f"Game ID: {game.game_id}\n")
        file.write(f"Game Round: {game.game_round}\n")
        file.write("\n")
        
        file.write("Winner Details:\n")
        file.write(f"  Name: {game.winner_name}\n")
        file.write(f"  Colour: {game.winner_colour}\n")
        file.write(f"  Kings Made: {game.winner_kings_made}\n")
        file.write(f"  Number of Captures: {game.winner_num_captures}\n")
        file.write("\n")
        
        file.write("Loser Details:\n")
        file.write(f"  Name: {game.loser_name}\n")
        file.write(f"  Colour: {game.loser_colour}\n")
        file.write(f"  Kings Made: {game.loser_kings_made}\n")
        file.write(f"  Number of Captures: {game.loser_num_captures}\n")
        file.write("\n")
        
        file.write(f"Total Moves: {game.num_moves}\n")
        file.write("=" * 40 + "\n\n")
        
    def write_game_result_stats(self, file, game_stats: Dict[str, GameResultStat]):
        # TODO: Format this better
        file.write("Game Statistics\n")
        file.write("=" * 40 + "\n")
        
        for bot_name, stats in game_stats.items():
            file.write(f"Bot Name: {bot_name}\n")
            file.write(f"  White Wins: {stats.white_wins}\n")
            file.write(f"  White Losses: {stats.white_losses}\n")
            file.write(f"  Black Wins: {stats.black_wins}\n")
            file.write(f"  Black Losses: {stats.black_losses}\n")
            file.write("-" * 40 + "\n")
        
        file.write("=" * 40 + "\n\n")
    
    def write_game_results(self):
        game_result_summary_path = os.path.join(self.game_results_folder, "game_result_summary.txt")
        with open(game_result_summary_path, "w", encoding="utf-8") as file:
            for game in self.game_results:
                self.write_game_result_summary(file, game)
                if game.moves:
                    game_result_moves_path = os.path.join(self.game_results_folder, f"game_{game.game_id}.txt")
                    with open(game_result_moves_path, "w", encoding="utf-8") as moves_file:
                        self.write_game_result_summary(moves_file, game)
                        moves_file.write("Moves: \n")
                        moves_file.write(game.moves)
                
        game_result_stats_path = os.path.join(self.game_results_folder, "game_result_stats.txt")
        
        game_result_map: Dict[str, GameResultStat] = {}
        if self.bot:
            game_result_map[make_unique_bot_string(-1, self.bot)] = GameResultStat(0,0,0,0)
        for idx, name in enumerate(self.bot_list):
            game_result_map[make_unique_bot_string(idx, name)] = GameResultStat(0,0,0,0)

        for game in self.game_results:
            # Add winner
            if game.winner_colour == "WHITE":
                game_result_map[game.winner_name].white_wins += 1
            else:
                game_result_map[game.winner_name].black_wins += 1
            
            # Add loser
            if game.loser_colour == "WHITE":
                game_result_map[game.loser_name].white_losses += 1
            else:
                game_result_map[game.loser_name].black_losses += 1
            
        with open(game_result_stats_path, "w", encoding="utf-8") as file:
            self.write_game_result_stats(file, game_result_map)
