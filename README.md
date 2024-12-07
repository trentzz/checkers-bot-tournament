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
```

### Examples

#### Example 1

Run 2 instances of `RandomBot` and 1 instance of `FirstBot` against each other.

- Enable verbose output (which logs the actual moves for each game)
- Set output directory for the run
- Run one round

```bash
poetry run checkers RandomBot RandomBot FirstMover --mode all --rounds 1 --verbose --output-dir output
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
