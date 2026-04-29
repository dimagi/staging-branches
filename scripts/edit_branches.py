#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["ruamel.yaml"]
# ///
"""Add or remove a branch in the top-level ``branches:`` list of a staging config."""
import argparse
from pathlib import Path

from ruamel.yaml import YAML


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Add a branch to .branches")
    p_add.add_argument("file")
    p_add.add_argument("branch")
    p_add.add_argument("--comment", default="")
    p_add.set_defaults(func=cmd_add)

    p_remove = sub.add_parser("remove", help="Remove a branch from .branches")
    p_remove.add_argument("file")
    p_remove.add_argument("branch")
    p_remove.set_defaults(func=cmd_remove)

    args = parser.parse_args()
    args.func(args)


def cmd_add(args):
    yaml, data, indent = load(args.file)
    branches = data["branches"]
    if args.branch in branches:
        notice(f"Branch '{args.branch}' already in .branches of {args.file}")
        return
    branches.append(args.branch)
    if args.comment:
        column = indent + len(f"- {args.branch}") + 2
        branches.yaml_add_eol_comment(args.comment, len(branches) - 1, column=column)
    yaml.dump(data, Path(args.file))
    print(f"Added branch '{args.branch}' to {args.file}")


def cmd_remove(args):
    yaml, data, _ = load(args.file)
    branches = data["branches"]
    if args.branch not in branches:
        notice(f"Branch '{args.branch}' not in .branches of {args.file}")
        return
    branches.remove(args.branch)
    yaml.dump(data, Path(args.file))
    print(f"Removed branch '{args.branch}' from {args.file}")


def load(path):
    """Open the YAML, matching ruamel's output indent to the file's existing style."""
    yaml = YAML()
    yaml.preserve_quotes = True
    data = yaml.load(Path(path))
    indent = data["branches"].lc.col
    yaml.indent(mapping=indent, sequence=indent, offset=indent)
    return yaml, data, indent


def notice(msg):
    print(f"::notice::{msg}, nothing to do")


if __name__ == "__main__":
    main()
