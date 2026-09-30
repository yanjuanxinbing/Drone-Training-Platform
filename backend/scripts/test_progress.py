"""Reproduce the best_duration_seconds bug in save_progress.

`/api/scenarios/{slug}/progress` is the only writer. Its best-time logic
latched on the FIRST recorded run and never updated again, so a user could
never improve the time shown on /account/progress.

These tests call the real endpoint function (not a copy of its logic) against
a temp data file, so a fix has to change the endpoint itself.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import backend.api.scenarios as api  # noqa: E402
from backend.schemas.scenario import ProgressSave  # noqa: E402

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {label}  {detail}")
    if not cond:
        FAILURES.append(label)


USER = {"phone": "15500000000"}


def run_case(tmpdir):
    """Redirect progress persistence at a temp file.

    `FileReader/Writer` join a bare filename onto `db/data/`, so an absolute
    path is not usable here — the read/write helpers are stubbed instead.
    That keeps the real `save_progress` body under test.
    """
    store: dict = {}
    path = os.path.join(tmpdir, "progress.json")

    def _read(_filename=None, subdir="data"):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _write(content=None, _filename=None, subdir="data"):
        # Called as `_save_progress(data)`, i.e. one positional arg.
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f)

    orig_read, orig_write = api._load_progress, api._save_progress
    api._load_progress = _read
    api._save_progress = _write
    store["_restore"] = lambda: (
        setattr(api, "_load_progress", orig_read),
        setattr(api, "_save_progress", orig_write),
    )
    return store, path


def _save(slug, score, dur, completed=True):
    return api.save_progress(
        slug,
        ProgressSave(scenario_slug=slug, score=score,
                     duration_seconds=dur, completed=completed),
        user=USER,
    )


def test_first_run_records():
    print("first run")
    with tempfile.TemporaryDirectory() as d:
        store, _ = run_case(d)
        try:
            e = _save("urban", 80, 120)
        finally:
            store["_restore"]()
        check("first run stores duration", e.best_duration_seconds == 120, e.best_duration_seconds)
        check("attempts = 1", e.attempts == 1, e.attempts)
        check("completed", e.completed is True, e.completed)


def test_slower_run_does_not_overwrite():
    print("slower second run must not win best time")
    with tempfile.TemporaryDirectory() as d:
        store, _ = run_case(d)
        try:
            _save("urban", 80, 120)
            e = _save("urban", 70, 300)
        finally:
            store["_restore"]()
        check("best time stays 120", e.best_duration_seconds == 120, e.best_duration_seconds)
        check("best score stays 80", e.best_score == 80, e.best_score)
        check("attempts = 2", e.attempts == 2, e.attempts)


def test_faster_run_improves_best_time():
    print("faster second run MUST become the new best time")
    with tempfile.TemporaryDirectory() as d:
        store, _ = run_case(d)
        try:
            _save("urban", 80, 120)
            e = _save("urban", 95, 60)
        finally:
            store["_restore"]()
        check("best time improves to 60", e.best_duration_seconds == 60, e.best_duration_seconds)
        check("best score improves to 95", e.best_score == 95, e.best_score)


def test_zero_duration_guard():
    print("zero duration must not become best time")
    with tempfile.TemporaryDirectory() as d:
        store, _ = run_case(d)
        try:
            e = _save("urban", 80, 0)
            e2 = _save("urban", 90, 90)
            e3 = _save("urban", 95, 0)
        finally:
            store["_restore"]()
        check("zero does not stick", e.best_duration_seconds == 0, e.best_duration_seconds)
        check("real duration then records", e2.best_duration_seconds == 90, e2.best_duration_seconds)
        check("zero does not erase best", e3.best_duration_seconds == 90, e3.best_duration_seconds)


def test_scenarios_are_independent():
    print("per-scenario isolation")
    with tempfile.TemporaryDirectory() as d:
        store, _ = run_case(d)
        try:
            _save("urban", 80, 100)
            e = _save("forest", 70, 200)
            u = _save("urban", 80, 300)
        finally:
            store["_restore"]()
        check("forest keeps its own time", e.best_duration_seconds == 200, e.best_duration_seconds)
        check("urban unaffected by forest", u.best_duration_seconds == 100, u.best_duration_seconds)


def test_persistence():
    print("value survives a reload from disk")
    with tempfile.TemporaryDirectory() as d:
        store, path = run_case(d)
        try:
            _save("urban", 80, 120)
            _save("urban", 95, 60)
        finally:
            store["_restore"]()
        with open(path, encoding="utf-8") as f:
            stored = json.load(f)
        rec = stored[USER["phone"]]["urban"]
        check("disk holds 60", rec["best_duration_seconds"] == 60, rec)
        check("disk holds attempts 2", rec["attempts"] == 2, rec)


if __name__ == "__main__":
    for fn in [test_first_run_records, test_slower_run_does_not_overwrite,
               test_faster_run_improves_best_time, test_zero_duration_guard,
               test_scenarios_are_independent, test_persistence]:
        fn()
        print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("all best-time tests pass")
