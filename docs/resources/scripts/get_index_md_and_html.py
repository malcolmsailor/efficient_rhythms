import argparse
import collections
import os
import re
import subprocess
import urllib

import get_settings_md_and_html

import efficient_rhythms.er_constants as er_constants
import efficient_rhythms.er_preprocess as er_preprocess

SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))

IN_MD_PATH = os.path.join(SCRIPT_DIR, "../markdown/index_pandoc.md")
OUT_MD_PATH = os.path.join(SCRIPT_DIR, "../../index.md")
OUT_HTML_PATH = os.path.join(SCRIPT_DIR, "../../index.html")
CSS_PATH1 = "resources/third_party/github-markdown-css/github-markdown.css"
CSS_PATH2 = "resources/css/markdown-body.css"

ER_WEB_URL = "http://malcolmsailor.pythonanywhere.com/"
ER_WEB_EXCLUDE = ("choirs",)

ER_LOCAL_URL = "http://127.0.0.1:5000"
TEMP_OUT_MD_PATH = os.path.join(os.environ["HOME"], "tmp/index.md")
TEMP_OUT_HTML_PATH = os.path.join(os.environ["HOME"], "tmp/index.html")


def _contains_quoted_constant(value):
    if isinstance(value, str):
        return value in er_constants.__dict__
    elif isinstance(value, collections.abc.Sequence):
        for subvalue in value:
            if _contains_quoted_constant(subvalue):
                return True
    return False


sequence_re = re.compile(r"^\(.*\)$|^\[.*\]$|^\{.*\}$", re.DOTALL)
quote_re = re.compile(r"'(\w+)'")
# quote_re = re.compile(r"'(\w+)'|\"(\w+)\"")


def _remove_quotes_around_constants(value):
    str_value = str(value)
    if re.match(sequence_re, str_value):
        str_value = str_value[1:-1]
    # I used to check for double-quotes too but Python always encloses
    # list/tuple items in single-quotes so I don't think that's necessary
    matches = re.findall(quote_re, str_value)
    for match in matches:
        if match in er_constants.__dict__:
            str_value = re.sub(f"'{match}'", match, str_value)
    return str_value


def er_web_query(example, er_url):
    settings_files = (
        os.path.join(
            SCRIPT_DIR,
            "../../examples",
            re.sub(r"\d+", "", example) + "_base.py",
        ),
        os.path.join(SCRIPT_DIR, "../../examples", f"{example}.py"),
    )
    merged = er_preprocess.merge_settings(settings_files)

    for name in ER_WEB_EXCLUDE:
        if name in merged:
            del merged[name]
    for name, value in merged.items():
        if isinstance(value, bool):
            merged[name] = "y" if value else "n"
        elif _contains_quoted_constant(value):
            merged[name] = _remove_quotes_around_constants(value)
        elif isinstance(value, (list, tuple, set)):
            merged[name] = str(value)[1:-1]
    query = urllib.parse.urlencode(merged, doseq=False)
    return er_url + "?" + query


def insert_examples(md_content, er_url):
    example_pattern = re.compile(r"EXAMPLE:(\w+)")
    example_matches = re.findall(example_pattern, md_content)
    for example in example_matches:

        svg_path = f"resources/svgs/{example}.svg"
        png_path = f"resources/pngs/{example}_00001.png"
        m4a_path = f"resources/m4as/{example}.m4a"
        web_url = er_web_query(example, er_url)
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
        repl.append(
            f"[Click to open this example in the web app]({web_url})"
            '{target="_blank" rel="noopener noreferrer"}\n'
        )
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
        r'<li><p><span id="\w+"><strong><code>(\w+)</code></strong></span>'
    )
    with open(
        get_settings_md_and_html.SETTINGS_HTML_PATH, "r", encoding="utf-8"
    ) as inf:
        attrs = re.findall(find_attr_pattern, inf.read())
    for attr in attrs:
        attr_pattern = re.compile(fr"`{attr}`")
        md = re.sub(attr_pattern, f"[`{attr}`](settings.html#{attr})", md)
    return md


def make_html(input_md, out_html_path):
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
    with open(out_html_path, "w", encoding="utf-8") as outf:
        outf.write(
            html_content.replace("<body>", '<body class="markdown-body">')
        )


def make_readme(input_md, out_md_path):
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
            out_md_path,
            "-f",
            "markdown",
            "-t",
            "gfm",
        ],
        check=True,
        input=input_md,
        encoding="utf-8",
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()
    return args


def remote_or_local_paths(args):
    if args.local:
        out_html_path = TEMP_OUT_HTML_PATH
        out_md_path = TEMP_OUT_MD_PATH
        er_url = ER_LOCAL_URL
    else:
        out_html_path = OUT_HTML_PATH
        out_md_path = OUT_MD_PATH
        er_url = ER_WEB_URL
    return out_html_path, out_md_path, er_url


def main():
    args = parse_args()
    out_html_path, out_md_path, er_url = remote_or_local_paths(args)
    with open(IN_MD_PATH, "r", encoding="utf-8") as inf:
        input_md = inf.read()
    input_md = insert_examples(input_md, er_url)
    input_md = insert_links(input_md)

    make_html(input_md, out_html_path)
    make_readme(input_md, out_md_path)


if __name__ == "__main__":
    main()
