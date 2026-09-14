#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def git_blob(path: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"HEAD:{path}"], text=True
    ).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", nargs="?", default="benchmark/discovery/FREEZE_V1.json")
    args = ap.parse_args()
    manifest = json.loads(Path(args.manifest).read_text())
    mismatches = []
    for path, expected in manifest["files"].items():
        actual = git_blob(path)
        if actual != expected:
            mismatches.append({"path": path, "expected": expected, "actual": actual})
    if mismatches:
        print(json.dumps({"frozen": False, "mismatches": mismatches}, indent=2))
        raise SystemExit(1)
    print(json.dumps({
        "frozen": True,
        "frozen_analyzer_commit": manifest["frozen_analyzer_commit"],
        "files_verified": len(manifest["files"]),
    }, indent=2))


if __name__ == "__main__":
    main()
