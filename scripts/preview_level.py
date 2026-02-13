#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from psld.preview import preview_level_json  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Path to a level .json")
    ap.add_argument("--view", default="mask", choices=["mask", "idx"])
    ns = ap.parse_args(argv)
    sys.stdout.write(preview_level_json(ns.path, view=ns.view))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
