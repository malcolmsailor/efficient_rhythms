"""Retrieve docstring from settings.py and convert to settings.md

Requires pandoc
"""
import re
import shutil
import subprocess
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)

SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))
CSS_PATH1 = "resources/third_party/github-markdown-css/github-markdown.css"
CSS_PATH2 = "resources/css/markdown-body.css"

# Constants for processing settings.py
SETTINGS_PY_PATH = os.path.join(
    SCRIPT_DIR, "../../../efficient_rhythms/er_settings/settings.py"
)
SETTINGS_MD_PATH = os.path.join(SCRIPT_DIR, "../../settings.md")
SETTINGS_HTML_PATH = os.path.join(SCRIPT_DIR, "../../settings.html")
SETTINGS_N_INTRO_PARAGRAPHS_TO_TRIM = 2
SETTINGS_PREAMBLE = (
    """# Efficient rhythms settings

<!-- This file was auto-generated by """
    + f"{os.path.basename(__file__)} and pandoc from "
    + f"{os.path.basename(SETTINGS_PY_PATH)}"
    + """ -->

"""
)


def get_code_block_replacement(code_block):
    indent_len = len(
        re.search(r"(?P<indent> *)```$", code_block).group("indent")
    )
    indent_pattern = re.compile(r"^" + " " * indent_len, re.MULTILINE)
    return re.sub(indent_pattern, "", code_block)


def get_settings_docstring():
    with open(SETTINGS_PY_PATH, "r") as inf:
        docstring = re.search(
            r'^class ERSettings:\s+"""(.*?)"""',
            inf.read(),
            re.MULTILINE + re.DOTALL,
        )[1]

    docstring = (
        "\n"
        + docstring.split("\n\n", maxsplit=SETTINGS_N_INTRO_PARAGRAPHS_TO_TRIM)[
            SETTINGS_N_INTRO_PARAGRAPHS_TO_TRIM
        ]
    )
    kwarg_pattern = re.compile(r"^ {8}(\w+(, \w+)*):", flags=re.MULTILINE)
    kwargs = [result[0] for result in re.findall(kwarg_pattern, docstring)]
    for kwarg in kwargs:
        pattern = re.compile(f"`{kwarg}`")
        docstring = re.sub(
            pattern, f'<a href="#{kwarg}">`{kwarg}`</a>', docstring
        )
    docstring = re.sub(
        kwarg_pattern, r'- <span id="\1">**`\1`**</span>:', docstring
    )
    # If I add any code blocks, then the following pattern risks matching
    # dictionary keys. In that case I should probably cut out the code blocks
    # earlier and then stitch them back in later.
    subkwarg_pattern = re.compile(r"^ {16}(\"\w+\"):", flags=re.MULTILINE)
    docstring = re.sub(subkwarg_pattern, r"    - `\1`:", docstring)
    subkwarg_pattern2 = re.compile(r"^ {16}(\"\w+\")$", flags=re.MULTILINE)
    docstring = re.sub(subkwarg_pattern2, r"    - `\1`", docstring)
    subheading_pattern = re.compile(
        r"^$\n {4,8}([^\n]+)\n {4,8}=+\n^$", flags=re.MULTILINE
    )
    subheadings = re.findall(subheading_pattern, docstring)
    docstring = re.sub(subheading_pattern, r"\n### \1 \n", docstring)
    for subheading in subheadings:
        pattern = re.compile(
            r'"(' + subheading.replace(" ", r"\s+") + ')"',
            re.IGNORECASE + re.MULTILINE,
        )
        ident = subheading.lower().replace(" ", "-")
        docstring = re.sub(
            pattern, r'"<a href="#' + ident + r'">\1</a>"', docstring
        )
    default_pattern = re.compile(r"^( +)Default: (.*)", flags=re.MULTILINE)
    docstring = re.sub(default_pattern, r"\n\1*Default*: `\2`", docstring)
    paragraph_pattern = re.compile(
        r"^$\n {4,8}( {0,4}\S[^\n]+)\n", flags=re.MULTILINE
    )
    docstring = re.sub(paragraph_pattern, r"\n\1\n", docstring)
    list_level_2_pattern = re.compile(r"^ {16}(- \S.*)", flags=re.MULTILINE)
    docstring = re.sub(list_level_2_pattern, r"\n    \1", docstring)
    docstring = docstring.replace("Keyword args:", "")
    per_voice_pattern = re.compile(
        r'([^"])([pP])er-voice\s+sequence(s?)([^"])', flags=re.MULTILINE
    )
    docstring = re.sub(
        per_voice_pattern,
        r"\1[\2er-voice sequence\3]"
        r"(#note-on-per-voice-sequences-and-other-looping-sequences)\4",
        docstring,
    )
    pitches_pattern = re.compile(
        r"([Ss]ee\s+(also\s+)?the\s+note\s+above\s+on\s+specifying\s+pitches\s+and\s+intervals)",
        flags=re.MULTILINE + re.DOTALL,
    )
    docstring = re.sub(
        pitches_pattern,
        r"[\1](#note-on-specifying-pitches-and-intervals)",
        docstring,
    )
    er_constants_doc_pattern = re.compile(r"docs/constants\.html")
    docstring = re.sub(
        er_constants_doc_pattern,
        r"[docs/constants.html](constants.html)",
        docstring,
    )
    return docstring


def main():
    if not shutil.which("pandoc"):
        raise Exception("pandoc not found, aborting")
    docstring = get_settings_docstring()

    subprocess.run(
        ["pandoc", "-o", SETTINGS_MD_PATH, "-t", "gfm"],
        encoding="utf-8",
        input=SETTINGS_PREAMBLE + docstring,
        check=True,
    )
    html_content = subprocess.run(
        [
            "pandoc",
            "--standalone",
            "--strip-comments",
            f"--css={CSS_PATH1}",
            f"--css={CSS_PATH2}",
            "--toc",
            "-i",
            SETTINGS_MD_PATH,
            "-t",
            "html",
        ],
        check=True,
        capture_output=True,
    ).stdout.decode()
    # A hack to get github-markdown.css to display
    with open(SETTINGS_HTML_PATH, "w", encoding="utf-8") as outf:
        outf.write(
            html_content.replace("<body>", '<body class="markdown-body">')
        )


if __name__ == "__main__":
    main()
