import os
import subprocess

SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))

IN_MD_PATH = os.path.join(SCRIPT_DIR, "general_pandoc.md")
OUT_MD_PATH = os.path.join(SCRIPT_DIR, "../general.md")
OUT_HTML_PATH = os.path.join(SCRIPT_DIR, "../general.html")
CSS_PATH1 = "resources/third_party/github-markdown-css/github-markdown.css"
CSS_PATH2 = "resources/markdown-body.css"


def main():
    subprocess.run(
        [
            "pandoc",
            "--strip-comments",
            "-i",
            IN_MD_PATH,
            "-o",
            OUT_MD_PATH,
            "-t",
            "gfm",
        ],
        check=True,
    )
    html_content = subprocess.run(
        [
            "pandoc",
            "--standalone",
            "--strip-comments",
            f"--css={CSS_PATH1}",
            f"--css={CSS_PATH2}",
            "-i",
            IN_MD_PATH,
            "-t",
            "html",
        ],
        check=True,
        capture_output=True,
    ).stdout.decode()
    # A hack to get github-markdown.css to display
    with open(OUT_HTML_PATH, "w", encoding="utf-8") as outf:
        outf.write(
            html_content.replace("<body>", '<body class="markdown-body">')
        )


if __name__ == "__main__":
    main()
