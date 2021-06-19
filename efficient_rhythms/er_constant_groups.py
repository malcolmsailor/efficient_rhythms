import ast
from collections import namedtuple
import os
import re
import types

SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))
CONSTANTS_PY_PATH = os.path.join(SCRIPT_DIR, "er_constants.py")

header_re = re.compile(r"^# (.*) constants$", re.MULTILINE)

# parsing the source in this way seems a little hacky but it works perfectly
# ok and I can't see an easier way of doing it.


ERConstant = namedtuple("ERConstant", ["name", "value"])


def format_group_name(name):
    return re.sub("[- ]", "_", name).lower()


numpy_re = re.compile(r"np.array\((.*)\)")


def format_value(node_value):
    try:
        val = ast.unparse(node_value)
    except AttributeError:
        # we're in Python <= 3.8, before ast.unparse was introduced
        # TODO document this, add to requirements
        import astunparse

        val = astunparse.unparse(node_value)
    m = re.match(numpy_re, val)
    if m:
        return m.group(1)
    return val


def parse(f_contents):
    out = {}
    by_name = {}
    tree = ast.parse(f_contents)
    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            m = re.search(header_re, node.value.value)
            if m:
                current_group_name = format_group_name(m.group(1))
                out[current_group_name] = []
        elif isinstance(node, ast.Assign):
            name = node.targets[0].id
            value = format_value(node.value)
            constant = ERConstant(name, value)
            out[current_group_name].append(constant)
            by_name[name] = constant
    return types.MappingProxyType(out), types.MappingProxyType(by_name)


def get_constant_groups():
    with open(CONSTANTS_PY_PATH, "r") as inf:
        py_contents = inf.read()
    return parse(py_contents)


CONSTANT_GROUPS, CONSTANTS_BY_NAME = get_constant_groups()
