import argparse

from checkers_bot_tournament.controller import Controller


def main():
    parser = argparse.ArgumentParser(description="checkers-board-tournament cli")

    # Mode (required)
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["one", "all"],
        help="Mode of the game: 'one' for one bot against others, 'all' for all bots against each other.",
    )

    parser.add_argument(
        "--board-start",
        type=str,
        choices=["default", "last_row"],
        default="default",
        help="Initial board start (this can be used together with --pdn)",
    )

    parser.add_argument("--pdn", type=str, help="Initialise a game using a PDN")

    parser.add_argument(
        "--bot",
        type=str,
        help="Name or path of the bot to use (required in 'one' mode).",
    )

    parser.add_argument("bot_list", type=str, nargs="+", help="List of bots")

    # Board size
    parser.add_argument("--size", type=int, default=8, help="Size of the board (default: 8).")

    # Number of rounds
    parser.add_argument(
        "--rounds", type=int, default=1, help="Number of rounds to play (default: 1)."
    )

    # Verbose flag
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output.")

    parser.add_argument("--export-pdn", action="store_true", help="Export as pdn output.")

    # Output directory
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save output files (default: .).",
    )

    args = parser.parse_args()

    # Validation: Ensure either `bot` or `bot_list` is provided
    if args.mode == "single" and not args.bot:
        parser.error("--bot is required in single mode.")
    if args.mode == "tournament" and not args.bot_list:
        parser.error("--bot-list is required in tournament mode.")

    if args.rounds < 1:
        parser.error("rounds is required to be an integer >= 1")

    # Create the controller
    controller = Controller(
        mode=args.mode,
        board_start_builder=args.board_start,
        pdn=args.pdn,
        protagonist_bot_name=args.bot,
        bot_names=args.bot_list,
        size=args.size,
        rounds=args.rounds,
        verbose=args.verbose,
        output_dir=args.output_dir,
        export_pdn=args.export_pdn,
    )
    controller.run()
