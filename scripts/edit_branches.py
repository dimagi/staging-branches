#!/usr/bin/env python3
"""Add or remove a branch in a staging config YAML file.

Operates on the top-level ``branches:`` list only. Preserves comments and
indentation by editing the file as text rather than reserializing YAML.
"""
import argparse
import re
import sys
from pathlib import Path

TOP_LEVEL_KEY = re.compile(r"^[^\s#]")
BRANCH_ENTRY = re.compile(r"^(\s+)-\s+(\S+)")


def find_branches_section(lines):
    """Return (start, end) indices of the top-level ``branches:`` section.

    ``start`` is the index of the ``branches:`` line itself; ``end`` is the
    first line after the section (the next top-level key, or len(lines)).
    Returns (None, None) if no top-level ``branches:`` is found.
    """
    start = next(
        (i for i, line in enumerate(lines) if line.startswith("branches:")),
        None,
    )
    if start is None:
        return None, None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if TOP_LEVEL_KEY.match(lines[i]):
            end = i
            break
    return start, end


def parse_entries(lines, start, end):
    """Yield (idx, indent, name) for each ``- branch`` entry in (start, end)."""
    for i in range(start + 1, end):
        m = BRANCH_ENTRY.match(lines[i])
        if m:
            yield i, m.group(1), m.group(2)


def load(file):
    return Path(file).read_text().splitlines(keepends=True)


def save(file, lines):
    Path(file).write_text("".join(lines))


def cmd_add(args):
    lines = load(args.file)
    start, end = find_branches_section(lines)
    if start is None:
        sys.exit(f"::error::Could not find 'branches:' key in {args.file}")

    entries = list(parse_entries(lines, start, end))
    if any(name == args.branch for _, _, name in entries):
        print(
            f"::notice::Branch '{args.branch}' already in .branches of "
            f"{args.file}, nothing to add"
        )
        return
    if not entries:
        sys.exit(
            f"::error::No existing branch entries found in .branches of "
            f"{args.file}"
        )

    last_idx, indent, _ = entries[-1]
    new_line = f"{indent}- {args.branch}"
    if args.comment:
        new_line += f"  # {args.comment}"
    new_line += "\n"

    if not lines[last_idx].endswith("\n"):
        lines[last_idx] += "\n"
    lines.insert(last_idx + 1, new_line)
    save(args.file, lines)
    print(f"Added branch '{args.branch}' to {args.file} (after line {last_idx + 1})")


def cmd_remove(args):
    lines = load(args.file)
    start, end = find_branches_section(lines)
    if start is None:
        sys.exit(f"::error::Could not find 'branches:' key in {args.file}")

    target = next(
        (i for i, _, name in parse_entries(lines, start, end) if name == args.branch),
        None,
    )
    if target is None:
        print(
            f"::notice::Branch '{args.branch}' not in .branches of "
            f"{args.file}, nothing to remove"
        )
        return

    del lines[target]
    save(args.file, lines)
    print(f"Removed branch '{args.branch}' from {args.file} (line {target + 1})")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Add a branch to .branches")
    p_add.add_argument("--file", required=True)
    p_add.add_argument("--branch", required=True)
    p_add.add_argument("--comment", default="")
    p_add.set_defaults(func=cmd_add)

    p_remove = sub.add_parser("remove", help="Remove a branch from .branches")
    p_remove.add_argument("--file", required=True)
    p_remove.add_argument("--branch", required=True)
    p_remove.set_defaults(func=cmd_remove)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
