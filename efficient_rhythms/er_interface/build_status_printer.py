import math


from .. import er_misc_funcs
from .. import er_shell_constants

from .cli import line_width


class BuildStatusPrinter:
    _spin_segments = "|/-\\"
    ip_header_strs = [
        "No pcs",
        "No pitches",
        "M interval",
        "Parallels",
        "Alternates",
        "Repeats",
        "Loops",
    ]
    ip_col_width = max(len(item) for item in ip_header_strs)
    vl_header_strs = [
        "Range",
        "H interval",
        "Dissonant",
        "M interval",
        "Parallels",
    ]
    vl_col_width = max(len(item) for item in vl_header_strs)

    def _get_header(self, er):
        attempt_digits = math.ceil(math.log10(er.voice_leading_attempts))
        attempt_num_str = f"{{:>{attempt_digits}}}/{er.voice_leading_attempts} "
        ip_digits = math.ceil(math.log10(er.initial_pattern_attempts))
        ip_num_str = f"{{:>{ip_digits}}}/{er.initial_pattern_attempts} "
        self._total_header_fmt_str = (
            f"Building pattern: overall attempt {attempt_num_str}"
        )
        self._ip_header_fmt_str = f"Initial pattern attempt {ip_num_str}"

    def __init__(self, er):
        # We hope that the user doesn't change the window width too much during
        # building!
        self.line_width = line_width()
        self._get_header(er)
        self.ip_n_cols = min(
            math.floor(self.line_width / (self.ip_col_width + 2)),
            len(self.ip_header_strs),
        )
        self.ip_header_strs = self.ip_header_strs[: self.ip_n_cols]
        self.vl_n_cols = min(
            math.floor(self.line_width / (self.vl_col_width + 2)),
            len(self.vl_header_strs),
        )
        self.vl_header_strs = self.vl_header_strs[: self.vl_n_cols]
        self.spin_i = -1
        self.total_attempt_count = 0
        self.ip_attempt_count = 0
        self.initial_print()

    def increment_ip_attempt(self):
        self.ip_attempt_count += 1

    def increment_total_attempt_count(self):
        self.total_attempt_count += 1
        self.print_header()

    def reset_ip_attempt_count(self):
        self.ip_attempt_count = 0

    @property
    def _spinning_line(self):
        self.spin_i += 1
        return self._spin_segments[self.spin_i % 4]

    @property
    def header(self):
        return er_misc_funcs.make_header(
            self._total_header_fmt_str.format(self.total_attempt_count),
            fill_char="=",
            bold=True,
        )

    def spin(self):
        print(f"\r{self._spinning_line} ", end="")

    @staticmethod
    def _table(subhead, colheads, n_cols, col_width, *vals):
        return "\n".join(
            [
                er_misc_funcs.make_header(
                    subhead,
                    fill_char="-",
                    bold=False,
                    indent=4,
                ),
                er_misc_funcs.make_table(
                    [
                        colheads,
                        [
                            "{} ({})".format(val[0], val[1])
                            for val in vals[:n_cols]
                        ],
                    ],
                    divider="",
                    borders=False,
                    col_width=col_width,
                ),
            ]
        )

    def ip_table(self, vals):
        return self._table(
            self._ip_header_fmt_str.format(self.ip_attempt_count),
            self.ip_header_strs,
            self.ip_n_cols,
            self.ip_col_width,
            *vals,
        )

    def vl_table(self, vals):
        return self._table(
            "Voice-leading dead-ends: ",
            self.vl_header_strs,
            self.vl_n_cols,
            self.vl_col_width,
            *vals,
        )

    def voice_leading_status(self, *vals):
        print(er_shell_constants.START_OF_PREV_LINE * 3, end="")
        print(self.vl_table(vals))
        assert (
            self.vl_table(vals).count("\n") == 2
        ), 'self.vl_table(vals).count("\n") != 2'
        self.spin()

    def initial_pattern_status(self, *vals):
        print(er_shell_constants.START_OF_PREV_LINE * 6, end="")
        print(
            self.ip_table(vals), end=er_shell_constants.START_OF_NEXT_LINE * 4
        )
        self.spin()

    def print_header(self):
        print(er_shell_constants.START_OF_PREV_LINE * 7, end="")
        print(self.header, end=er_shell_constants.START_OF_NEXT_LINE * 7)

    def initial_print(self):
        print("")
        print(self.header)
        print(self.ip_table([(0, 0) for _ in range(self.ip_n_cols)]))
        print(self.vl_table([(0, 0) for _ in range(self.vl_n_cols)]))

    @staticmethod
    def success():
        print(
            "\r"
            + er_shell_constants.BOLD_TEXT
            + "Success!"
            + er_shell_constants.RESET_TEXT,
            end="\n\n",
        )
