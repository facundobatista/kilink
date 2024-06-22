# Copyright 2024 Facundo Batista
# Licensed under the GPL v3 License
# For further info, check https://github.com/facundobatista/kilink

"""Infrastructure tests."""

import os

import pydocstyle
import pytest
from flake8.api.legacy import get_style_guide


def get_python_filepaths(roots):
    """Retrieve paths of Python files."""
    python_paths = []
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                if filename.endswith(".py"):
                    python_paths.append(os.path.join(dirpath, filename))
    return python_paths


def test_pep8(capsys):
    """Verify all files are nicely styled."""
    python_filepaths = get_python_filepaths(["kilink", "tests"])
    style_guide = get_style_guide()
    report = style_guide.check_files(python_filepaths)

    # if flake8 didn't report anything, we're done
    if report.total_errors == 0:
        return

    # grab on which files we have issues
    out, _ = capsys.readouterr()
    pytest.fail(f"Please fix {report.total_errors} issue(s):\n{''.join(out)}", pytrace=False)


def test_pep257():
    """Verify all files have nice docstrings."""
    python_filepaths = get_python_filepaths(["kilink"])
    to_ignore = {
        "D105",  # Missing docstring in magic method
        "D107",  # Missing docstring in __init__
    }
    to_include = pydocstyle.violations.conventions.pep257 - to_ignore
    errors = list(pydocstyle.check(python_filepaths, select=to_include))

    if errors:
        report = ["Please fix files as suggested by pydocstyle ({:d} issues):".format(len(errors))]
        report.extend(str(e) for e in errors)
        msg = "\n".join(report)
        pytest.fail(msg, pytrace=False)
