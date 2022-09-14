#!/bin/env python3

"""Logic for comparing modification times of glob-matched files."""

# TODO allow directories as outputs. See:
# https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#directories-as-outputs
# May need to flag dirs explicitly, e.g. "DIR:foo.*".
# Directory mod-times update on read, so need to write a timestamp file to the directory?


import os
import re
import logging
from pathlib import Path
from typing import List


# In case of comma in file paths: "a,b\,c" -> ["a", "b\,c"]
DELIM = re.compile(r'(?<!\\),')


def time_globber(pathglobs: str) -> List[float]:
    """Match a comma-delimited list of path globs and return file mod-times."""
    mtimes = []
    for glob in DELIM.split(pathglobs):
        pglob = Path(glob.strip())
        logging.debug(f"Glob {pglob}")
        if not pglob.is_absolute():
            raise Exception(f"{pglob} is not an absolute path")
        for fpath in pglob.parent.glob(pglob.name):
            if not fpath.is_file():
                logging.debug(f"Ignoring non-file {fpath}")
                continue
            logging.debug(f"  matched {fpath.name}")
            mtimes.append(fpath.stat().st_mtime)
    return mtimes


def outdated(input_globs: str, output_globs: str) -> bool:
    """Return True if any input is newer than any output."""
    intimes = time_globber(input_globs)
    logging.debug(f"Input times: {intimes}")
    outtimes = time_globber(output_globs)
    logging.debug(f"Ouput times: {outtimes}")
    if not intimes:
        # No input data.
        return False
    if not outtimes:
        # No output data.
        return True
    return max(intimes) > min(outtimes)


def file_globber(pathglobs: str) -> List[float]:
    """Match a comma-delimited list of path globs and return file mod-times."""
    files = []
    for glob in DELIM.split(pathglobs):
        pglob = Path(glob.strip())
        logging.debug(f"Glob {pglob}")
        if not pglob.is_absolute():
            raise Exception(f"{pglob} is not an absolute path")
        for fpath in pglob.parent.glob(pglob.name):
            if not fpath.is_file():
                logging.debug(f"Ignoring non-file {fpath}")
                continue
            logging.debug(f"  matched {fpath.name}")
            files.append(fpath)
    return files


def delete_files(globs: str) -> None:
    """Delete matched files."""
    for fpath in file_globber(globs):
        os.unlink(fpath)
