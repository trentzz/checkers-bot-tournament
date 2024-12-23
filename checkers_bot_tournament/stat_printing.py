from math import inf
from typing import IO, Optional

from checkers_bot_tournament.bots.bot_tracker import BotTracker
from checkers_bot_tournament.checkers_util import compute_performance_rating, make_unique_bot_string


def write_tournament_overall_stats(
    bot_list: list[BotTracker], file: IO, protagonist_tracker: Optional[BotTracker] = None
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
    protagonist_name = (
        f" for {make_unique_bot_string(protagonist_tracker)}" if protagonist_tracker else ""
    )
    file.write(f"Game Statistics{protagonist_name}\n")
    file.write("=" * 60 + "\n\n")

    for bot in bot_list:
        stats = bot.stats
        file.write(
            f"{'Against ' if protagonist_tracker else ''}Bot Name: {make_unique_bot_string(bot)} ({round(bot.rating)})\n"
        )
        file.write("-" * 60 + "\n")

        label_width = 10  # For "White", "Black", "Overall"
        col_width = 8  # For "Win", "Draw", "Loss" columns

        # Print the header row once per bot
        header = f"{'Win':<{col_width}}{'Draw':<{col_width}}{'Loss':<{col_width}}{'Overall Score':<{col_width}}"
        file.write(f"{'':<{label_width}}{header}\n")

        # Organize counts for White, Black, and Overall
        # For protagonist mode: you can just flip wins/losses & white/black
        if not protagonist_tracker:
            counts = {
                "White": (stats.white_wins, stats.white_draws, stats.white_losses),
                "Black": (stats.black_wins, stats.black_draws, stats.black_losses),
                "Overall": (stats.total_wins, stats.total_draws, stats.total_losses),
            }
        else:
            counts = {
                "White": (stats.black_losses, stats.black_draws, stats.black_wins),
                "Black": (stats.white_losses, stats.white_draws, stats.white_wins),
                "Overall": (stats.total_losses, stats.total_draws, stats.total_wins),
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


def write_tournament_h2h_stats(
    bot_list: list[BotTracker], file: IO, protagonist_tracker: Optional[BotTracker] = None
) -> None:
    """
    Writes head-to-head (H2H) statistics in a 2D matrix form.

    For each pair of distinct bots (i, j), we show the combined W/D/L results
    from i's perspective vs j (regardless of color) in the top half of the matrix
    (where j > i). The diagonal and lower half remain blank to avoid duplication.

    Also, calculates a performance rating based on the final ratings of the opponent
    and the score achieved, and shows the difference between that performance rating
    and the bot's own rating.
    """
    file.write("Head-to-Head Statistics\n")
    file.write("=" * 100 + "\n\n")

    # Prepare headers
    # We'll print a matrix where rows and columns are bots
    # Column headers: each opponent bot
    if protagonist_tracker:
        bot_list.append(protagonist_tracker)
    max_name_len = max(len(make_unique_bot_string(bot)) for bot in bot_list)
    name_col_width = max_name_len + 8  # some padding for rating
    cell_width = max(30, name_col_width)  # width for each cell to display W/D/L and PerfRating

    # Print top header row
    file.write(" " * name_col_width)  # empty space for the left top corner
    for bot in bot_list[1:]:
        bot_str = make_unique_bot_string(bot)
        file.write(f"{bot_str} ({round(bot.rating)})".center(cell_width))
    file.write("\n")
    file.write("-" * (name_col_width + (len(bot_list) - 1) * cell_width) + "\n")

    # Print each row
    for i, row_bot in enumerate(bot_list):
        row_str = f"{make_unique_bot_string(row_bot)} ({round(row_bot.rating)})"

        # We'll build two lines for each row:
        # line1: from row bot perspective (with W/D/L)
        # line2: from column bot perspective (just PR and diff)
        line1 = f"{row_str:<{name_col_width}}"
        line2 = " " * name_col_width  # second line aligned under columns

        for j, col_bot in enumerate(bot_list[1:], start=1):
            if i == j:
                # Diagonal: no self matches
                cell_top = " " * 1 + "x" * (cell_width - 2) + " " * 1
                cell_bottom = " " * 1 + "x" * (cell_width - 2) + " " * 1
            elif j < i:
                # Lower half: leave blank
                cell_top = " " * 1 + "-" * (cell_width - 2) + " " * 1
                cell_bottom = " " * 1 + "-" * (cell_width - 2) + " " * 1
            else:
                # Top half: show stats
                row_bot_name = make_unique_bot_string(row_bot)
                row_bot_id = row_bot.bot_id

                col_bot_name = make_unique_bot_string(col_bot)
                col_bot_id = col_bot.bot_id

                # Row perspective stats: row_bot vs col_bot
                stat_row_vs_col = row_bot.h2h_stats[col_bot_name]
                w_rc = stat_row_vs_col.total_wins
                d_rc = stat_row_vs_col.total_draws
                l_rc = stat_row_vs_col.total_losses

                # Column perspective stats: col_bot vs row_bot
                stat_col_vs_row = col_bot.h2h_stats[row_bot_name]
                w_cr = stat_col_vs_row.total_wins
                d_cr = stat_col_vs_row.total_draws
                l_cr = stat_col_vs_row.total_losses

                if (w_rc + d_rc + l_rc) == 0:
                    # No games played between these bots
                    cell_top = "N/A".center(cell_width)
                    cell_bottom = "N/A".center(cell_width)
                else:
                    # Compute performance ratings
                    # From row bot perspective
                    perf_rc, diff_rc = compute_performance_rating(
                        w_rc, d_rc, l_rc, row_bot.rating, col_bot.rating
                    )

                    # From col bot perspective
                    perf_cr, diff_cr = compute_performance_rating(
                        w_cr, d_cr, l_cr, col_bot.rating, row_bot.rating
                    )

                    def float_to_str(f: float) -> str:
                        if f == inf:
                            return "∞"
                        elif f == -inf:
                            return "-∞"
                        else:
                            return str(round(f))

                    perf_rc_str = float_to_str(perf_rc)
                    perf_cr_str = float_to_str(perf_cr)
                    diff_cr_str = float_to_str(abs(diff_cr))

                    # wdl-11----> id-8--->perf-9-->
                    # BA987654321_87654321987654321
                    # XXX/XXX/XXX [XX] PR:XXXX (+Δ)
                    #      ±Δ=XXX [XX] PR:XXXX (-Δ)
                    # BA987654321_87654321987654321
                    # delta-11--> id-8--->perf-9-->
                    # ------- 29 characters ------>

                    if perf_rc is not None and diff_rc is not None:
                        wdl_str = f"{w_rc}/{d_rc}/{l_rc}"
                        row_bot_id_str = f"[{row_bot_id}] PR:"
                        perf_row_str = f"{perf_rc_str} ({'+' if diff_rc > 0 else '-'}Δ)"

                        wdl_formatted = f"{wdl_str:>11}"
                        perf_formatted_row = f"{row_bot_id_str:>8}{perf_row_str:>9}"
                        cell_top = f"{wdl_formatted} {perf_formatted_row}".ljust(cell_width)
                    else:
                        cell_top = "N/A".center(cell_width)

                    if perf_cr is not None and diff_cr is not None:
                        delta_pr_str = f"Δ:±{diff_cr_str}"
                        col_bot_id_str = f"[{col_bot_id}] PR:"
                        perf_col_str = f"{perf_cr_str} ({'+' if diff_cr > 0 else '-'}Δ)"

                        perf_formatted_row = f"{col_bot_id_str:>8}{perf_col_str:>9}"
                        cell_bottom = f"{delta_pr_str:>11} {perf_formatted_row}".ljust(cell_width)
                    else:
                        cell_bottom = "N/A".center(cell_width)

            line1 += cell_top
            line2 += cell_bottom

        # Print the two lines for this row
        file.write(line1 + "\n")
        file.write(line2 + "\n" * 2)

    file.write("=" * 100 + "\n\n")
