from .. import er_misc_funcs

from .changers import ChangeFuncError


def apply(score, changers):
    if not changers:
        return None

    print("Applying:")
    # changed is True if at least one changer applied without error
    changed = False

    score = score.copy()
    for changer in changers.values():
        print(f"    {changer.pretty_name}... ", end="")
        try:
            changer.apply(score)
            print("done.")
            changed = True
        except ChangeFuncError as err:
            # CHANGER_TODO are ChangeFuncErrors also bugs? Should they be caught below?
            print("ERROR!")
            print(
                er_misc_funcs.add_line_breaks(
                    err.args[0], indent_width=8, indent_type="all"
                )
            )
            input(
                er_misc_funcs.add_line_breaks(
                    "Press enter to continue",
                    indent_width=12,
                    indent_type="all",
                )
            )

    return score if changed else None
