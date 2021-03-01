"""Requires pandoc and black
"""

import ast
import os
import subprocess

SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))
CSS_PATH1 = "resources/third_party/github-markdown-css/github-markdown.css"
CSS_PATH2 = "resources/markdown-body.css"
CONSTANTS_PY_PATH = os.path.join(SCRIPT_DIR, "../../src/er_constants.py")
CONSTANTS_MD_PATH = os.path.join(SCRIPT_DIR, "../constants.md")
CONSTANTS_HTML_PATH = os.path.join(SCRIPT_DIR, "../constants.html")


class ConstantGroup:
    def __init__(self, doc):
        self.doc = doc
        self.contents = []

    def append(self, item):
        self.contents.append(item)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(doc='{self.doc}' "
            f"contents={self.contents})"
        )


def add_sharps(assign_node):
    out = []
    for target in assign_node.targets:
        if "_SHARP" in target.id:
            out.append(target.id.replace("_SHARP", "#"))
    if out:
        # so output string will end with " = "
        out.append("")
    return " = ".join(out)


def parse(f_contents):
    out = []
    tree = ast.parse(f_contents)
    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            out.append(ConstantGroup(node.value.value))
        elif isinstance(node, ast.Assign):
            out[-1].append(add_sharps(node) + ast.unparse(node))
    return out


def format_constants(constants):
    md_list = []
    for group in constants:
        md_list.append(
            subprocess.run(
                ["pandoc", "-t", "gfm"],
                encoding="utf-8",
                input=group.doc,
                check=True,
                capture_output=True,
            ).stdout
        )
        md_list.append("```")
        md_list.append(
            # removed calls to black because they were not only slow but
            # they (obviously) reformat any lines containing '#' in an undesired
            # way
            # subprocess.run(
            #     ["black", "-"],
            #     encoding="utf-8",
            #     input="\n".join([item for item in group.contents]),
            #     check=True,
            #     capture_output=True,
            # ).stdout
            "\n".join(group.contents)
        )
        md_list.append("```\n")
    with open(CONSTANTS_MD_PATH, "w", encoding="utf-8") as outf:
        outf.write("\n".join(md_list))
    html_content = subprocess.run(
        [
            "pandoc",
            "--standalone",
            "--strip-comments",
            f"--css={CSS_PATH1}",
            f"--css={CSS_PATH2}",
            "-i",
            CONSTANTS_MD_PATH,
            "-t",
            "html",
        ],
        check=True,
        capture_output=True,
    ).stdout.decode()
    # A hack to get github-markdown.css to display
    with open(CONSTANTS_HTML_PATH, "w", encoding="utf-8") as outf:
        outf.write(
            html_content.replace("<body>", '<body class="markdown-body">')
        )


def main():
    with open(CONSTANTS_PY_PATH, "r") as inf:
        f_contents = inf.read()
    constants = parse(f_contents)
    format_constants(constants)


if __name__ == "__main__":
    main()
