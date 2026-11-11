#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["ruamel.yaml"]
# ///
"""Add or remove a branch in the ``branches:`` list of commcare-connect-staging.yml.

Connect version of edit_branches.py, used by add-connect-branch.yml and remove-connect-branch.yml.
Differences: the file is fixed, `add --before` inserts the entry above an existing one, and
`remove` keeps the commented-out lines below the removed entry.
"""
import argparse
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import CommentMark
from ruamel.yaml.tokens import CommentToken

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "commcare-connect-staging.yml"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help=argparse.SUPPRESS)  # for testing
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Add a branch to .branches")
    p_add.add_argument("branch")
    p_add.add_argument("--comment", default="")
    p_add.add_argument("--before", default="", help="Insert just before this branch instead of at the end")
    p_add.set_defaults(func=cmd_add)

    p_remove = sub.add_parser("remove", help="Remove a branch from .branches")
    p_remove.add_argument("branch")
    p_remove.set_defaults(func=cmd_remove)

    args = parser.parse_args()
    args.func(args)


def cmd_add(args):
    yaml, data, indent = load(args.file)
    branches = data["branches"]
    if args.branch in branches:
        notice(f"Branch '{args.branch}' already in .branches of {args.file.name}")
        return
    if args.before:
        if args.before not in branches:
            raise SystemExit(f"::error::Branch '{args.before}' not in .branches of {args.file.name}")
        index = branches.index(args.before)
        branches.insert(index, args.branch)
    else:
        index = len(branches)
        branches.append(args.branch)
    if args.comment:
        column = indent + len(f"- {args.branch}") + 2
        branches.yaml_add_eol_comment(args.comment, index, column=column)
    yaml.dump(data, args.file)
    position = f"before '{args.before}'" if args.before else "at the end"
    print(f"Added branch '{args.branch}' to {args.file.name} {position}")


def cmd_remove(args):
    yaml, data, _ = load(args.file)
    branches = data["branches"]
    # Connect's rebuild-staging.yml only rebuilds on a push to the trunk while it is listed
    trunk = data.get("trunk", "main")
    if args.branch == trunk:
        raise SystemExit(f"::error::'{trunk}' is the trunk and can't be removed from {args.file.name}")
    if args.branch not in branches:
        notice(f"Branch '{args.branch}' not in .branches of {args.file.name}")
        return
    remove_keeping_comment_lines(branches=branches, index=branches.index(args.branch))
    yaml.dump(data, args.file)
    print(f"Removed branch '{args.branch}' from {args.file.name}")


def remove_keeping_comment_lines(*, branches, index):
    """Remove an entry without losing the comment lines below it.

    ruamel stores full-line comments (such as commented-out branches) as part of the
    comment on the entry above them, so deleting that entry would delete them too.
    Move those lines onto the previous entry instead.
    """
    token = (branches.ca.items.get(index) or [None])[0]
    _, _, following_lines = token.value.partition("\n") if token else ("", "", "")
    del branches[index]
    if not following_lines:
        return
    if index == 0:
        branches.ca.comment = branches.ca.comment or [None, []]
        branches.ca.comment[1].append(CommentToken(following_lines, CommentMark(0), None))
        return
    previous = (branches.ca.items.get(index - 1) or [None])[0]
    if previous:
        previous.value += following_lines
    else:
        branches.ca.items[index - 1] = [CommentToken("\n" + following_lines, CommentMark(0), None), None, None, None]


def load(path):
    """Open the YAML, matching ruamel's output indent to the file's existing style."""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096  # don't wrap long branch+comment lines
    data = yaml.load(path)
    indent = data["branches"].lc.col
    yaml.indent(mapping=indent, sequence=indent, offset=indent)
    return yaml, data, indent


def notice(msg):
    print(f"::notice::{msg}, nothing to do")


if __name__ == "__main__":
    main()
