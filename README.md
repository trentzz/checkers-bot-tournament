# checkers-bot-tournament

Uhh pretty much the title. Make bots that play checkers, play them against each other :)

## Install

### Prereqs

- Python
- Poetry (Can be installed with `pipx install poetry`)

```bash
cd checkers-bot-tournament
poetry install
poetry run checkers -h
```

## Usage

```bash
poetry run checkers -h

usage: checkers [-h] --mode {one,all} [--board-state {default,last_row}] [--pdn PDN]
                [--bot BOT] [--size SIZE] [--rounds ROUNDS] [--verbose] [--export-pdn]
                [--output-dir OUTPUT_DIR]
                bot_list [bot_list ...]

checkers-board-tournament cli

positional arguments:
  bot_list              List of bots

options:
  -h, --help            show this help message and exit
  --mode {one,all}      Mode of the game: 'one' for one bot against others, 'all' for all
                        bots against each other.
  --board-state {default,last_row}
                        Initial board state (this can be used together with --pdn)
  --pdn PDN             Initialise a game using a PDN
  --bot BOT             Name or path of the bot to use (required in 'one' mode).
  --size SIZE           Size of the board (default: 8).
  --rounds ROUNDS       Number of rounds to play (default: 1).
  --verbose             Enable verbose output.
  --export-pdn          Export as pdn output.
  --output-dir OUTPUT_DIR
                        Directory to save output files (default: .).
```

### Options

There are two ways to initialise a game, with `--board-state` options and a `--pdn` file (they can be used together).

#### Portable Draughts Notation

More information about PDN can be found here:

<https://en.wikipedia.org/wiki/Portable_Draughts_Notation>

To view the checkers games in a UI website:
<https://playcheckers.io/analyze>

#### Outputs

`--verbose` outputs a formatted game with extra information.
`--export-pdn` outputs a pdn file.

### Examples

#### Example 1

Run 2 instances of `RandomBot` and 1 instance of `FirstBot` against each other.

- Enable verbose output (which logs the actual moves for each game)
- Set output directory for the run
- Run one round

```bash
poetry run checkers RandomBot RandomBot FirstMover --mode all --rounds 1 --verbose --output-dir output
```

### Interpreting the Result Summary
The performance of each bot is displayed in `game_result_stats.py` in two ways.
#### Percentage Scores
Each entry breaks down the coarse-grain W/D/L stats for each bot, separated by colour (White/Black/Overall):

```
Game Statistics
============================================================

Bot Name: [0] RandomBot (1319)
------------------------------------------------------------
          Win     Draw    Loss    Overall Score
White     3       4       13      
Black     6       0       14      
Overall   9       4       27      
White     15.0%   20.0%   65.0%   = 25.00%
Black     30.0%   0.0%    70.0%   = 30.00%
Overall   22.5%   10.0%   67.5%   = 27.50%
============================================================
```

#### [Elo Ratings](https://en.wikipedia.org/wiki/Elo_rating_system)
Ratings update throughout the tournament, factoring in the opponent’s rating and the game outcome. A Head-to-Head (H2H) matrix shows how each bot performed against every other bot. [Performance ratings](https://en.wikipedia.org/wiki/Performance_rating_(chess)) (PRs) measure the level of strength the bots played relative to their Elo rating, with (+Δ) or (-Δ) showing over- or under-performance.

```
Head-to-Head Statistics
==================================================================================

                          [1] FirstMover (1309)          [2] GreedyCat (1658)      
----------------------------------------------------------------------------------
[0] RandomBot (1319)        3/2/5  [0] PR:1239 (-Δ)       2/0/8  [0] PR:1418 (+Δ) 
                            Δ:±80  [1] PR:1390 (+Δ)       Δ:±98  [2] PR:1560 (-Δ) 
```

## For Developers

### Adding your own bot

1. Fork the repo and make a branch for your bot
2. Make a new file in the `bots/` folder
3. Make sure it inherits from `Bot` in `base_bot.py`. Have a look at other bots for clarification.
4. Add your bot to `controller.py`. Again have a look at existing implementation for details. You can also search for `# BOT TODO`
5. Make sure the string you use in `Controller` and `get_name()` match
6. Run `poetry install`. See [Usage](#usage) for more details and options.
7. Commit and open a PR to the `add-your-bot-here` branch (select your fork as the source, and this repo as the destination)

### Bot API notes

TODO

### Branches

- `main` contains stable code
- `add-your-bot-here` is effectively the development branch, PR into this branch

I'll promote `add-your-bot-here` to `main` every once in a while (after testing)

### TODO

- Elo system for ranking bots
- Tournament mode
- Benchmark all available bots and add rankings to readme periodically

### Scripts

Poetry is used to manage dependencies and [poethepoet](https://pypi.org/project/poethepoet/) is used to manage custom scripts.

Available development scripts are:

- `poetry run poe format` - Formats the code
- `poetry run poe format_check` - Checks if code is formatted
- `poetry run poe check` - Perform a suite of static checks
- `poetry run poe fix` - Apply formatting and static checks fixes
- `poetry run poe test` - Runs the tests with coverage report

You can run the following command to automatically apply `format` and `check` before each commit and push:

- `poetry run pre-commit install` - Installs pre-commit hooks

### VSCode

For VSCode users, the following extensions are recommended:

- Ruff

## Checkers Rules

Not an exhaustive list:

- If you have the option of capturing a piece, you're forced to (the `move_list` will only contain captures if a capture is available)
- Conditions for a draw are:
  - Repeating the exact position 3 times
  - 40 Moves without a capture or crowning

## Stuff and things

Not an exhaustive list:

- Default size set to an 8x8 board
- Multiple jumps in one go is not currently supported, I'll do it sometime, but bot implementation shouldn't have to change at all to support it.
- The colours of the pieces are "BLACK" and "WHITE" and white always goes first.
- Each round consists of 2 games where the bots swap being black and white.
- The output consists of a folder with two files: `game_result_stats.txt` and `game_result_summary.txt` as well as all the games as `game_X.txt` if `--verbose` was used.
  - `game_result_stats.txt` is the win/loss of each bot
  - `game_result_summary.txt` is the summary of each game

## Contributors

### Main

- trentzz
- donren-leung

### Bots

| Username     | Bots                           |
| ------------ | ------------------------------ |
| trentzz      | RandomBot, FirstMover, CopyCat |
| donren-leung | ScaredyCat, GreedyCat          |

Finally feel free to open an issue if I did something dumb (very likely).
