"""The JSON lines on standard output are UTF-8 on every OS (core/logs.py)."""

from __future__ import annotations

import io
import json
import sys
from collections.abc import Iterator

import pytest

from walmart_headless.core import logs


@pytest.fixture(autouse=True)
def _restore() -> Iterator[None]:
    yield
    logs.configure(sys.stdout)


def test_lines_are_utf8_whatever_the_streams_code_page() -> None:
    # Release 1.3.1: on Windows a redirected standard output used the ANSI code page (cp1252), so the offline
    # reprocessing logs of 2026-10-27 held "Food \x9b Fresh Fruits" (not UTF-8) in 26 lines, and a line with a
    # character outside the code page raised UnicodeEncodeError, which the writer took for a closed stream:
    # the line was lost without a trace.
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp1252", newline="\n")
    logs.configure(stream)
    logs.log("INFO", "PAGE_COLLECTED", message="Food › Fresh Fruits: result page 1")
    logs.log("INFO", "PAGE_COLLECTED", message="Fresh Strawberries, 8.8 oz 🍓 (22.4 ¢/oz)")
    stream.flush()
    lines = raw.getvalue().decode("utf-8").splitlines()
    assert [json.loads(x)["message"] for x in lines] == [
        "Food › Fresh Fruits: result page 1",
        "Fresh Strawberries, 8.8 oz 🍓 (22.4 ¢/oz)",
    ]


def test_a_closed_stream_never_stops_a_run() -> None:
    stream = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    logs.configure(stream)
    stream.close()
    logs.log("INFO", "RUN_RUNNING", message="still running")  # nothing raised
