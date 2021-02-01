import os
import re
import subprocess

SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))

IN_MD_PATH = os.path.join(SCRIPT_DIR, "general_pandoc.md")
OUT_MD_PATH = os.path.join(SCRIPT_DIR, "../general.md")
OUT_HTML_PATH = os.path.join(SCRIPT_DIR, "../general.html")
CSS_PATH1 = "resources/third_party/github-markdown-css/github-markdown.css"
CSS_PATH2 = "resources/markdown-body.css"

# TODO links to settings wherever they are mentioned

# PIANO_ROLL_STYLING = "max-height: 300px"
#
#
# def insert_styling(md_content):
#
#     piano_roll_pattern = re.compile(r'(class="piano_roll")')
#     md_content = re.sub(
#         piano_roll_pattern, r"\1 " + f'style="{PIANO_ROLL_STYLING}"', md_content
#     )
#     return md_content


EXAMPLE_PATTERN = re.compile(r"EXAMPLE:(\w+)")
# We insert some styling inline so it will show up on github (hopefully)
EXAMPLE_REPL = (
    r'<span id="\1">**Example:** `docs/examples/\1.py`</span><br>'
    + r'![\1 notation](resources/svgs/\1.svg){class="notation"}\n'
    + r"![\1 piano roll](resources/pngs/\1_00001.png)"
    + r'{class="piano_roll" style="max-height: 300px"}\n'
    + r"![\1 audio](resources/m4as/\1.m4a)\n"
)
EXAMPLE_REF_PATTERN = re.compile(r"REF:(\w+)")
EXAMPLE_REF_REPL = r'<a href="#\1">`docs/examples/\1.py`</a>'


def insert_examples(md_content):
    md_content = re.sub(EXAMPLE_PATTERN, EXAMPLE_REPL, md_content)
    md_content = re.sub(EXAMPLE_REF_PATTERN, EXAMPLE_REF_REPL, md_content)
    return md_content


def main():
    with open(IN_MD_PATH, "r", encoding="utf-8") as inf:
        input_md = inf.read()
    input_md = insert_examples(input_md)
    # input_md = insert_styling(input_md)

    subprocess.run(
        [
            "pandoc",
            "--strip-comments",
            "--toc",
            "-o",
            OUT_MD_PATH,
            "-f",
            "markdown",
            "-t",
            "gfm",
        ],
        check=True,
        input=input_md,
        encoding="utf-8",
    )
    html_content = subprocess.run(
        [
            "pandoc",
            "--standalone",
            "--strip-comments",
            f"--css={CSS_PATH1}",
            f"--css={CSS_PATH2}",
            "--toc",
            "-f",
            "markdown",
            "-t",
            "html",
        ],
        check=True,
        capture_output=True,
        input=input_md,
        encoding="utf-8",
    ).stdout
    # A hack to get github-markdown.css to display
    with open(OUT_HTML_PATH, "w", encoding="utf-8") as outf:
        outf.write(
            html_content.replace("<body>", '<body class="markdown-body">')
        )


if __name__ == "__main__":
    main()
