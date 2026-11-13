"""Tests for scripts/edit_connect_branches.py.

Run with: uv run pytest
"""
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "edit_connect_branches.py"

SAMPLE = dedent("""\
    trunk: main
    name: autostaging  # name of the branch to build
    branches:  # list of branches to merge into final branch
      - main
      - first # Ann Nov 1
      # - old-one # Bob Oct 1
      - second
      # - old-two # Cat Oct 2
      - third  # Dan Nov 3
    submodules:
""")


@pytest.fixture
def sample(tmp_path):
    path = tmp_path / "commcare-connect-staging.yml"
    path.write_text(SAMPLE)
    return path


def run(path, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--file", str(path), *args],
        capture_output=True,
        text=True,
    )


def replace_lines(text, *, old, new):
    """Return ``text`` with the line ``old`` swapped for ``new`` (which may be several lines or empty)."""
    old_line = old + "\n"
    assert old_line in text
    return text.replace(old_line, new, 1)


# add


def test_add_appends_with_comment(sample):
    result = run(sample, "add", "new", "--comment", "Eve Nov 9")

    assert result.returncode == 0
    assert result.stdout == "Added branch 'new' to commcare-connect-staging.yml at the end\n"
    expected = replace_lines(SAMPLE, old="  - third  # Dan Nov 3", new="  - third  # Dan Nov 3\n  - new  # Eve Nov 9\n")
    assert sample.read_text() == expected


def test_add_appends_without_comment(sample):
    run(sample, "add", "new")

    expected = replace_lines(SAMPLE, old="  - third  # Dan Nov 3", new="  - third  # Dan Nov 3\n  - new\n")
    assert sample.read_text() == expected


def test_add_before_inserts_above_named_branch(sample):
    result = run(sample, "add", "new", "--before", "second", "--comment", "Eve Nov 9")

    assert result.returncode == 0
    assert result.stdout == "Added branch 'new' to commcare-connect-staging.yml before 'second'\n"
    expected = replace_lines(SAMPLE, old="  - second", new="  - new  # Eve Nov 9\n  - second\n")
    assert sample.read_text() == expected


def test_add_before_missing_branch_fails(sample):
    result = run(sample, "add", "new", "--before", "nope")

    assert result.returncode == 1
    assert "::error::Branch 'nope' not in .branches" in result.stderr
    assert sample.read_text() == SAMPLE


def test_add_existing_branch_is_noop(sample):
    result = run(sample, "add", "second", "--comment", "again")

    assert result.returncode == 0
    assert result.stdout.startswith("::notice::Branch 'second' already in .branches")
    assert sample.read_text() == SAMPLE


def test_add_matches_four_space_indent(tmp_path):
    path = tmp_path / "f.yml"
    path.write_text("branches:\n    - main\n    - a  # x\n")

    run(path, "add", "b", "--comment", "y")

    assert path.read_text() == "branches:\n    - main\n    - a  # x\n    - b  # y\n"


# remove


@pytest.mark.parametrize(
    "branch, line",
    [
        ("first", "  - first # Ann Nov 1"),
        ("second", "  - second"),
        ("third", "  - third  # Dan Nov 3"),
    ],
)
def test_remove_deletes_only_that_line(sample, branch, line):
    result = run(sample, "remove", branch)

    assert result.returncode == 0
    assert result.stdout == f"Removed branch '{branch}' from commcare-connect-staging.yml\n"
    assert sample.read_text() == replace_lines(SAMPLE, old=line, new="")


def test_remove_keeps_comment_lines_when_previous_entry_has_no_comment(tmp_path):
    path = tmp_path / "f.yml"
    path.write_text("branches:\n  - main\n  - a  # x\n  # - old\n  - b\n")

    run(path, "remove", "a")

    assert path.read_text() == "branches:\n  - main\n  # - old\n  - b\n"


def test_remove_first_entry_keeps_comment_lines(tmp_path):
    path = tmp_path / "f.yml"
    path.write_text("trunk: other\nbranches:\n  - a  # x\n  # - old\n  - b\n")

    run(path, "remove", "a")

    assert path.read_text() == "trunk: other\nbranches:\n  # - old\n  - b\n"


@pytest.mark.parametrize(
    "header, trunk",
    [
        ("trunk: main\n", "main"),
        ("trunk: develop\n", "develop"),
        ("", "main"),  # trunk defaults to main
    ],
)
def test_remove_trunk_fails(tmp_path, header, trunk):
    path = tmp_path / "f.yml"
    original = f"{header}branches:\n  - {trunk}\n  - a\n"
    path.write_text(original)

    result = run(path, "remove", trunk)

    assert result.returncode == 1
    assert f"::error::'{trunk}' is the trunk" in result.stderr
    assert path.read_text() == original


def test_remove_missing_branch_is_noop(sample):
    result = run(sample, "remove", "nope")

    assert result.returncode == 0
    assert result.stdout.startswith("::notice::Branch 'nope' not in .branches")
    assert sample.read_text() == SAMPLE


def test_remove_commented_out_branch_is_noop(sample):
    result = run(sample, "remove", "old-one")

    assert result.returncode == 0
    assert sample.read_text() == SAMPLE


# real file


def test_add_then_remove_restores_real_file(tmp_path):
    path = tmp_path / "commcare-connect-staging.yml"
    shutil.copy(src=REPO / "commcare-connect-staging.yml", dst=path)
    original = path.read_text()

    run(path, "add", "tmp/test-branch", "--comment", "Test Nov 11")
    assert path.read_text() != original
    run(path, "remove", "tmp/test-branch")

    assert path.read_text() == original
