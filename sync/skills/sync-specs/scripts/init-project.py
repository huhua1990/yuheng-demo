#!/usr/bin/env python3
"""Initialize a Yuheng consumer project from a local core snapshot."""

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, Optional


SCRIPT_DIR = Path(__file__).resolve().parent
SYNC_PATH = SCRIPT_DIR / "sync-specs-api.py"
SYNC_SPEC = importlib.util.spec_from_file_location("yuheng_sync_specs", SYNC_PATH)
SYNC = importlib.util.module_from_spec(SYNC_SPEC)
assert SYNC_SPEC.loader is not None
SYNC_SPEC.loader.exec_module(SYNC)


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def init_project(source: Path, target: Path, project_id: str) -> Dict[str, Any]:
    target = Path(target).resolve()
    target.mkdir(parents=True, exist_ok=True)
    for relative in (
        "docs/specs",
        "docs/plans",
        "docs/verification",
        "consumer-overlay",
    ):
        (target / relative).mkdir(parents=True, exist_ok=True)

    sync_report = SYNC.sync_bundle(
        Path(source),
        target,
        mode="apply",
        project_id=project_id,
    )
    if sync_report["status"] != "PASS":
        return sync_report

    _write_if_missing(
        target / ".yuheng/project.yaml",
        "projectId: {}\nkind: consumer\nscriptVersion: {}\n"
        "governanceNamespace: yuheng\nlegacyNamespaces:\n"
        "  - athena-rules\n  - athena-skills\n".format(
            project_id, SYNC.SCRIPT_VERSION
        ),
    )
    _write_if_missing(
        target / "docs/verification/governance-sync/README.md",
        "# Governance sync evidence\n\n"
        "Use `sync-specs-api.py --check`, `--apply` and `--verify`. "
        "This directory is consumer-owned and is never overwritten by sync.\n",
    )
    _write_if_missing(
        target / "README.md",
        "# {}\n\nThis is a Yuheng consumer project.\n\n"
        "Core governance is synchronized into `yuheng-rules/`, "
        "`yuheng-skills/` and `ai-knowledge-core/`.\n".format(project_id),
    )
    return sync_report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = init_project(args.source, args.target, args.project_id)
    except (OSError, SYNC.SyncError, ValueError) as exc:
        result = {"status": "BLOCKED", "issues": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
