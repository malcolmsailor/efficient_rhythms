import os
import re
import subprocess

SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))

IN_MD_PATH = os.path.join(SCRIPT_DIR, "index_pandoc.md")
OUT_MD_PATH = os.path.join(SCRIPT_DIR, "../index.md")
OUT_HTML_PATH = os.path.join(SCRIPT_DIR, "../index.html")
CSS_PATH1 = "resources/third_party/github-markdown-css/github-markdown.css"
CSS_PATH2 = "resources/markdown-body.css"

# TODO links to settings wherever they are mentioned


def insert_examples(md_content):
    example_pattern = re.compile(r"EXAMPLE:(\w+)")
    # We insert some styling inline so it will show up on github (hopefully)
    example_repl = (
        r'<span id="\1">**Example:** `docs/examples/\1.py`</span><br>'
        + r'![\1 notation](resources/svgs/\1.svg){class="notation"}\n'
        + r"![\1 piano roll](resources/pngs/\1_00001.png)"
        + r'{class="piano_roll" style="max-height: 300px"}\n'
        + r"![\1 audio](resources/m4as/\1.m4a)\n"
    )
    example_ref_pattern = re.compile(r"REF:(\w+)")
    example_ref_repl = r'<a href="#\1">`docs/examples/\1.py`</a>'
    md_content = re.sub(example_pattern, example_repl, md_content)
    md_content = re.sub(example_ref_pattern, example_ref_repl, md_content)
    return md_content


def make_html(input_md):
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


def make_readme(input_md):
    def replace_html_links(md_content):
        html_link = re.compile(r"\(([\w/]+).html")
        html_link_repl = r"\(docs/\1.md"
        return re.sub(html_link, html_link_repl, md_content)

    def update_paths(md_content):
        resources_path = re.compile(r"\(resources/")
        resources_path_repl = r"\(docs/resources/"
        return re.sub(resources_path, resources_path_repl, md_content)

    input_md = replace_html_links(input_md)
    input_md = update_paths(input_md)
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


def main():
    with open(IN_MD_PATH, "r", encoding="utf-8") as inf:
        input_md = inf.read()
    input_md = insert_examples(input_md)

    make_html(input_md)
    make_readme(input_md)


if __name__ == "__main__":
    main()
