#!/usr/bin/env python3
"""Run deterministic health checks after a Yuheng consumer sync."""

import argparse
import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


SCRIPT_DIR = Path(__file__).resolve().parent
SYNC_SPEC = importlib.util.spec_from_file_location(
    "yuheng_sync_specs", SCRIPT_DIR / "sync-specs-api.py"
)
SYNC = importlib.util.module_from_spec(SYNC_SPEC)
assert SYNC_SPEC.loader is not None
SYNC_SPEC.loader.exec_module(SYNC)


@dataclass
class CheckReport:
    status: str = "PASS"
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)
        self.status = "BLOCKED"

    def warning(self, message: str) -> None:
        self.warnings.append(message)
        if self.status == "PASS":
            self.status = "WARN"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "evidence": self.evidence,
            "scriptVersion": SYNC.SCRIPT_VERSION,
        }


def run_checks(project_root: Path, expected_project_id: Optional[str] = None) -> CheckReport:
    project_root = Path(project_root).resolve()
    report = CheckReport(evidence=[str(project_root)])
    required = (
        ".yuheng/project.yaml",
        "yuheng-manifest.yaml",
        "yuheng-rules",
        "yuheng-skills",
        "ai-knowledge-core/server",
        "ai-knowledge-core/ui",
        "ai-knowledge-core/data",
        "docs/specs",
        "docs/plans",
        "docs/verification",
        "consumer-overlay",
    )
    for relative in required:
        if not (project_root / relative).exists():
            report.error("required consumer path is missing: " + relative)

    manifest_path = project_root / "yuheng-manifest.yaml"
    if manifest_path.exists():
        try:
            manifest = SYNC.load_manifest(manifest_path)
        except (OSError, ValueError, SYNC.SyncError) as exc:
            report.error("manifest cannot be read: {}".format(exc))
        else:
            project = manifest.get("project", {})
            if expected_project_id and isinstance(project, dict):
                if project.get("id") != expected_project_id:
                    report.error(
                        "manifest project id is {}, expected {}".format(
                            project.get("id"), expected_project_id
                        )
                    )
            if manifest.get("legacyNamespaces") != list(SYNC.LEGACY_NAMESPACES):
                report.warning("manifest does not declare legacy Athena namespaces")
            if not manifest.get("codeVersion"):
                report.error("manifest codeVersion is missing")
            if not manifest.get("governanceVersion"):
                report.error("manifest governanceVersion is missing")
            if not manifest.get("knowledgeVersion"):
                report.error("manifest knowledgeVersion is missing")

    for legacy_name in SYNC.LEGACY_NAMESPACES:
        legacy_path = project_root / legacy_name
        if legacy_path.exists():
            report.warning("legacy namespace retained: " + legacy_name)

    protected = (
        "docs/specs",
        "docs/plans",
        "docs/verification",
        "business",
        "consumer-overlay",
    )
    for relative in protected:
        path = project_root / relative
        if path.is_symlink():
            report.error("protected consumer path must not be a symlink: " + relative)
    return report


def format_report(report: CheckReport) -> str:
    lines = ["status: " + report.status]
    for error in report.errors:
        lines.append("- error: " + error)
    for warning in report.warnings:
        lines.append("- warning: " + warning)
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--project-id", default="")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = run_checks(args.project_root, args.project_id or None)
    payload = report.as_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.as_json else format_report(report))
    return 0 if report.status in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
