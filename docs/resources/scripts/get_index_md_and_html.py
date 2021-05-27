import os
import re
import subprocess

import get_settings_md_and_html

SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))

IN_MD_PATH = os.path.join(SCRIPT_DIR, "../markdown/index_pandoc.md")
OUT_MD_PATH = os.path.join(SCRIPT_DIR, "../../index.md")
OUT_HTML_PATH = os.path.join(SCRIPT_DIR, "../../index.html")
CSS_PATH1 = "resources/third_party/github-markdown-css/github-markdown.css"
CSS_PATH2 = "resources/css/markdown-body.css"


def insert_examples(md_content):
    example_pattern = re.compile(r"EXAMPLE:(\w+)")
    example_matches = re.findall(example_pattern, md_content)
    for example in example_matches:
        svg_path = f"resources/svgs/{example}.svg"
        png_path = f"resources/pngs/{example}_00001.png"
        m4a_path = f"resources/m4as/{example}.m4a"
        repl = [
            f'<span id="{example}">**Example:**'
            f" `docs/examples/{example}.py`</span><br>"
        ]
        if os.path.exists(os.path.join(SCRIPT_DIR, "../..", svg_path)):
            repl.append(f'![\1 notation]({svg_path}){{class="notation"}}\n')
        # We insert some styling inline so it will show up on github (hopefully)
        if os.path.exists(os.path.join(SCRIPT_DIR, "../..", png_path)):
            repl.append(
                f"![\1 piano roll]({png_path})"
                '{class="piano_roll" style="max-height: 300px"}\n'
            )
        if os.path.exists(os.path.join(SCRIPT_DIR, "../..", m4a_path)):
            repl.append(f"![\1 audio]({m4a_path})\n")
        md_content = re.sub(
            fr"\bEXAMPLE:{example}\b", "".join(repl), md_content
        )

    example_ref_pattern = re.compile(r"REF:(\w+)")
    example_ref_repl = r'<a href="#\1">`docs/examples/\1.py`</a>'
    md_content = re.sub(example_ref_pattern, example_ref_repl, md_content)
    return md_content


def insert_links(md):
    # we could also parse efficient_rhythms/er_settings.py to get the attributes of the
    #   ERSettings object, but it seems easier to just do a regex search
    #   on the documentation as follows
    find_attr_pattern = re.compile(
        '<li><p><span id="\w+"><strong><code>(\w+)</code></strong></span>'
    )
    with open(
        get_settings_md_and_html.SETTINGS_HTML_PATH, "r", encoding="utf-8"
    ) as inf:
        attrs = re.findall(find_attr_pattern, inf.read())
    for attr in attrs:
        attr_pattern = re.compile(fr"`{attr}`")
        md = re.sub(attr_pattern, f"[`{attr}`](settings.html#{attr})", md)
    return md


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
    input_md = insert_links(input_md)

    make_html(input_md)
    make_readme(input_md)


if __name__ == "__main__":
    main()
