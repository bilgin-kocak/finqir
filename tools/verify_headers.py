#!/usr/bin/env python3
# This file is derived from Qiskit Finance for use in FinQIR.
#
# (C) Copyright IBM 2020, 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Utility script to verify derived and new FinQIR headers."""

import argparse
import multiprocessing
import os
import sys
import re

# regex for character encoding from PEP 263
pep263 = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)")


def discover_files(code_paths, exclude_folders):
    """Find all .py, .pyx, .pxd files in a list of trees"""
    out_paths = []
    for path in code_paths:
        if os.path.isfile(path):
            out_paths.append(path)
        else:
            for directory in os.walk(path):
                dir_path = directory[0]
                for folder in exclude_folders:
                    if folder in directory[1]:
                        directory[1].remove(folder)
                for subfile in directory[2]:
                    if (
                        subfile.endswith(".py")
                        or subfile.endswith(".pyx")
                        or subfile.endswith(".pxd")
                    ):
                        out_paths.append(os.path.join(dir_path, subfile))
    return out_paths


def validate_header(file_path):
    """Validate the header for a single file"""
    project_lines = {
        "# This code is part of a Qiskit project.\n",
        "# This file is derived from Qiskit Finance for use in FinQIR.\n",
        "# This file is part of FinQIR.\n",
    }
    license_lines = {
        "# This code is licensed under the Apache License, Version 2.0. You may\n",
        "# obtain a copy of this license in the LICENSE.txt file in the root directory\n",
        "# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.\n",
    }
    with open(file_path, encoding="utf8") as code_file:
        lines = code_file.readlines()

    for line in lines[:2]:
        if pep263.match(line):
            return file_path, False, "Unnecessary encoding specification (PEP 263, 3120)"

    try:
        start = next(index for index, line in enumerate(lines[:5]) if line in project_lines)
    except StopIteration:
        return file_path, False, "Project header not found in first 5 lines"

    if start + 2 >= len(lines) or not lines[start + 2].startswith("# (C) Copyright "):
        return file_path, False, "Header copyright line not found"
    if not license_lines.issubset(set(lines[start + 3 : start + 12])):
        return file_path, False, "Apache-2.0 license notice is incomplete"
    return file_path, True, None


def _main():
    default_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "finqir"
    )
    parser = argparse.ArgumentParser(description="Check file headers.")
    parser.add_argument(
        "paths",
        type=str,
        nargs="*",
        default=[default_path],
        help="Paths to scan; by default uses ../finqir from the script",
    )
    args = parser.parse_args()
    files = discover_files(args.paths, exclude_folders=[])
    with multiprocessing.Pool() as pool:
        res = pool.map(validate_header, files)
    failed_files = [x for x in res if x[1] is False]
    if len(failed_files) > 0:
        for failed_file in failed_files:
            sys.stderr.write(f"{failed_file[0]} failed header check because:\n")
            sys.stderr.write(f"{failed_file[2]}\n\n")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    _main()
