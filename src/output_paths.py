"""Where a script may read run results from and write them to.

The original results in results (the runs, the freeze and the
evaluation made up to 17 November 2026) are kept exactly as they are. A new
run writes to a folder named on the command line with --out. That folder must
be under results/corrections/ or outside results altogether.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, "..", "results"))
CORRECTIONS = os.path.join(RESULTS, "corrections")


def argument(flag):
    """The value given after a flag on the command line, or None."""
    if flag in sys.argv:
        position = sys.argv.index(flag)
        if position + 1 < len(sys.argv):
            return sys.argv[position + 1]
    return None


def output_folder():
    """The folder named with --out, after checking it is not one of the original results."""
    folder = argument("--out")
    if folder is None:
        sys.exit("Name an output folder with --out, for example results/corrections/2026-11-18/model")
    folder = os.path.abspath(folder)
    inside_results = folder == RESULTS or folder.startswith(RESULTS + os.sep)
    inside_corrections = folder.startswith(CORRECTIONS + os.sep)
    if inside_results and not inside_corrections:
        sys.exit("Refusing to write into the original results (" + folder + "). "
                 "Use a folder under results/corrections/.")
    os.makedirs(folder, exist_ok=True)
    return folder


def input_folder(flag):
    """The folder named after a flag such as --results; it must exist."""
    folder = argument(flag)
    if folder is None:
        sys.exit("Name the folder to read with " + flag)
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        sys.exit("Folder not found: " + folder)
    return folder


def is_correction(folder):
    return os.path.abspath(folder).startswith(CORRECTIONS + os.sep)
