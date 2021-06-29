import os
import subprocess

import efficient_rhythms.er_changers as er_changers
import efficient_rhythms.er_classes as er_classes


SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))
OUT_MD_PATH = os.path.join(SCRIPT_DIR, "../../changers.md")
OUT_HTML_PATH = os.path.join(SCRIPT_DIR, "../../changers.html")

NAMES_TO_SKIP = ("marked_by",)  # TODO document and implement
DUMMY_SCORE = er_classes.Score()

CSS_PATH1 = "resources/third_party/github-markdown-css/github-markdown.css"
CSS_PATH2 = "resources/css/markdown-body.css"


# def get_display_if(inst, name):
#     if name in inst.display_if and inst.display_if[name] is not None:
#         out = []
#         for k, v in inst.display_if[name].items():
#             out.append(f"{k} == {v}")
#         return "Only has effect if " + ", ".join(out)
#     return None


def get_default(inst, name):
    return getattr(inst, name)


def category_string(category_list, inst_args, header_text):

    header = f"# {header_text}"
    out = [header]
    for filter_ in category_list:
        inst = getattr(er_changers, filter_)(*inst_args)
        out.append(inst.get_info())
    return "\n\n".join(out)


def get_md():
    categories = (
        (er_changers.FILTERS, (DUMMY_SCORE,), "Filters"),
        (er_changers.TRANSFORMERS, (DUMMY_SCORE,), "Transformers"),
        (er_changers.PROB_CURVES, (), "Probability curves"),
    )
    md_list = [
        category_string(list_, args, name) for (list_, args, name) in categories
    ]
    with open(OUT_MD_PATH, "w", encoding="utf-8") as outf:
        outf.write("\n\n\n".join(md_list))


def get_html():
    html_content = subprocess.run(
        [
            "pandoc",
            "--standalone",
            "--strip-comments",
            f"--css={CSS_PATH1}",
            f"--css={CSS_PATH2}",
            "--toc",
            "--toc-depth=2",
            "-i",
            OUT_MD_PATH,
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


def main():
    get_md()
    get_html()


if __name__ == "__main__":
    main()
