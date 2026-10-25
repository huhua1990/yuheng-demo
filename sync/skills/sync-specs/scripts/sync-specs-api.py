#!/usr/bin/env python3
"""Synchronize versioned Yuheng governance assets into a consumer project."""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


SCRIPT_VERSION = "0.1.0"
MANAGED_DIRS = {
    "yuheng-rules": "governance/rules",
    "yuheng-skills": "governance/skills",
    "ai-knowledge-core": "ai-knowledge-core",
}
MANAGED_FILES = {"yuheng-manifest.yaml": "release/yuheng-manifest.yaml"}
PROTECTED_ROOTS = (
    "docs/specs",
    "docs/plans",
    "docs/verification",
    "business",
    "consumer-overlay",
)
LEGACY_NAMESPACES = ("athena-rules", "athena-skills")


class SyncError(RuntimeError):
    """Raised when a sync would be unsafe or cannot be completed."""


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return {}
    if value in ("true", "false"):
        return value == "true"
    if value in ("null", "~"):
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def load_manifest(path: Path) -> Mapping[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        lines = [
            (len(line) - len(line.lstrip(" ")), line.strip())
            for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]

        def parse_block(index: int, indent: int) -> Tuple[Any, int]:
            is_list = lines[index][1].startswith("- ")
            result: Any = [] if is_list else {}
            while index < len(lines):
                current_indent, content = lines[index]
                if current_indent < indent:
                    break
                if current_indent > indent:
                    raise ValueError("unsupported manifest indentation")
                if is_list:
                    if not content.startswith("- "):
                        raise ValueError("mixed manifest list and mapping")
                    result.append(_parse_scalar(content[2:]))
                    index += 1
                    continue
                if ":" not in content:
                    raise ValueError("invalid manifest mapping")
                key, raw = content.split(":", 1)
                index += 1
                if raw.strip():
                    result[key.strip()] = _parse_scalar(raw)
                elif index < len(lines) and lines[index][0] > indent:
                    child, index = parse_block(index, lines[index][0])
                    result[key.strip()] = child
                else:
                    result[key.strip()] = {}
            return result, index

        if not lines:
            value = {}
        else:
            value, _ = parse_block(0, lines[0][0])
    if not isinstance(value, Mapping):
        raise SyncError("manifest must be an object: " + str(path))
    return value


def _manifest_for_consumer(source_manifest: Path, project_id: Optional[str]) -> str:
    text = source_manifest.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        if not project_id and "legacyNamespaces:" in text:
            return text
        lines = text.rstrip().splitlines()
        if project_id:
            project_start = next(
                (index for index, line in enumerate(lines) if line.strip() == "project:"),
                None,
            )
            if project_start is None:
                lines.extend(
                    ["project:", "  id: {}".format(project_id), "  kind: consumer"]
                )
            else:
                project_end = project_start + 1
                while project_end < len(lines) and (
                    not lines[project_end].strip()
                    or len(lines[project_end]) - len(lines[project_end].lstrip(" ")) > 0
                ):
                    project_end += 1
                project_lines = lines[project_start + 1 : project_end]
                replaced = {"id": False, "kind": False}
                for index, line in enumerate(project_lines):
                    stripped = line.strip()
                    if stripped.startswith("id:"):
                        project_lines[index] = "  id: {}".format(project_id)
                        replaced["id"] = True
                    elif stripped.startswith("kind:"):
                        project_lines[index] = "  kind: consumer"
                        replaced["kind"] = True
                if not replaced["id"]:
                    project_lines.insert(0, "  id: {}".format(project_id))
                if not replaced["kind"]:
                    project_lines.append("  kind: consumer")
                lines[project_start + 1 : project_end] = project_lines
        if "legacyNamespaces:" not in "\n".join(lines):
            lines.extend(
                ["legacyNamespaces:", "  - athena-rules", "  - athena-skills"]
            )
        return "\n".join(lines) + "\n"
    if not isinstance(value, Mapping):
        raise SyncError("manifest must be an object: " + str(source_manifest))
    value = dict(value)
    if project_id:
        value["project"] = {"id": project_id, "kind": "consumer"}
    value.setdefault("legacyNamespaces", list(LEGACY_NAMESPACES))
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _iter_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if path.is_dir():
        for child in sorted(path.rglob("*")):
            if child.is_file():
                yield child


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    for child in _iter_files(path):
        relative = child.relative_to(path if path.is_dir() else child.parent)
        digest.update(str(relative).encode("utf-8"))
        digest.update(child.read_bytes())
    return digest.hexdigest()


def _same_tree(left: Path, right: Path) -> bool:
    if not left.exists() or not right.exists():
        return False
    if left.is_symlink() or right.is_symlink():
        return left.is_symlink() and right.is_symlink() and left.resolve() == right.resolve()
    if left.is_file() or right.is_file():
        return left.is_file() and right.is_file() and left.read_bytes() == right.read_bytes()
    left_files = sorted(p.relative_to(left) for p in left.rglob("*") if p.is_file())
    right_files = sorted(p.relative_to(right) for p in right.rglob("*") if p.is_file())
    if left_files != right_files:
        return False
    return all((left / relative).read_bytes() == (right / relative).read_bytes() for relative in left_files)


def _ensure_safe_target(target: Path) -> None:
    for relative in (*MANAGED_DIRS.keys(), *MANAGED_FILES.keys()):
        path = target / relative
        if path.is_symlink():
            raise SyncError("refusing to replace symlink: " + str(path))


def _snapshot_plan(source: Path, target: Path, project_id: Optional[str]) -> Dict[str, Any]:
    plan: Dict[str, Any] = {"directories": {}, "files": {}, "changes": [], "warnings": []}
    for target_name, source_relative in MANAGED_DIRS.items():
        source_path = source / source_relative
        if not source_path.is_dir():
            raise SyncError("missing source directory: " + str(source_path))
        target_path = target / target_name
        plan["directories"][target_name] = (source_path, target_path)
        if not _same_tree(source_path, target_path):
            plan["changes"].append(target_name)
    for target_name, source_relative in MANAGED_FILES.items():
        source_path = source / source_relative
        if not source_path.is_file():
            raise SyncError("missing source file: " + str(source_path))
        target_path = target / target_name
        plan["files"][target_name] = (source_path, target_path)
        if project_id:
            desired = _manifest_for_consumer(source_path, project_id).encode("utf-8")
            same = target_path.exists() and target_path.read_bytes() == desired
        else:
            same = target_path.exists() and target_path.read_bytes() == source_path.read_bytes()
        if not same:
            plan["changes"].append(target_name)
    for legacy_name in LEGACY_NAMESPACES:
        if (target / legacy_name).exists():
            plan["warnings"].append(
                "legacy namespace retained for read compatibility: " + legacy_name
            )
    return plan


def _atomic_replace(stage: Path, destination: Path) -> None:
    backup: Optional[Path] = None
    if destination.exists() or destination.is_symlink():
        backup = destination.with_name(".{}.backup-{}".format(destination.name, uuid.uuid4().hex))
        os.replace(destination, backup)
    try:
        os.replace(stage, destination)
    except Exception:
        if backup and backup.exists():
            os.replace(backup, destination)
        raise
    if backup:
        if backup.is_dir() and not backup.is_symlink():
            shutil.rmtree(backup)
        else:
            backup.unlink(missing_ok=True)


def _apply_plan(plan: Mapping[str, Any], target: Path, project_id: Optional[str]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    yuheng_dir = target / ".yuheng"
    staging = Path(tempfile.mkdtemp(prefix=".sync-", dir=str(target)))
    try:
        staged: List[Tuple[Path, Path]] = []
        for name, (source_path, destination) in plan["directories"].items():
            stage_path = staging / name
            shutil.copytree(source_path, stage_path, symlinks=True)
            staged.append((stage_path, destination))
        for name, (source_path, destination) in plan["files"].items():
            stage_path = staging / name
            stage_path.parent.mkdir(parents=True, exist_ok=True)
            if name == "yuheng-manifest.yaml" and project_id:
                stage_path.write_text(
                    _manifest_for_consumer(source_path, project_id),
                    encoding="utf-8",
                )
            else:
                shutil.copy2(source_path, stage_path)
            staged.append((stage_path, destination))
        for stage_path, destination in staged:
            _atomic_replace(stage_path, destination)
        report_path = yuheng_dir / "last-sync.json"
        yuheng_dir.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {
                    "scriptVersion": SCRIPT_VERSION,
                    "appliedAt": datetime.now().astimezone().isoformat(),
                    "changes": plan["changes"],
                    "legacyNamespaces": list(LEGACY_NAMESPACES),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def sync_bundle(
    source: Path,
    target: Path,
    mode: str = "check",
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Check, apply, or verify a core governance snapshot."""

    if mode not in {"check", "apply", "verify"}:
        raise ValueError("mode must be check, apply, or verify")
    source = Path(source).resolve()
    target = Path(target).resolve()
    if not source.is_dir():
        raise SyncError("source directory does not exist: " + str(source))
    if mode in {"apply", "verify"}:
        _ensure_safe_target(target)
    effective_project_id = project_id
    if mode in {"check", "verify"} and not effective_project_id:
        target_manifest = target / "yuheng-manifest.yaml"
        if target_manifest.exists():
            try:
                target_value = load_manifest(target_manifest)
            except (OSError, ValueError, SyncError):
                target_value = {}
            target_project = target_value.get("project", {})
            if isinstance(target_project, Mapping) and target_project.get("kind") == "consumer":
                effective_project_id = target_project.get("id")
    plan = _snapshot_plan(source, target, effective_project_id)
    issues: List[str] = []
    if mode == "verify":
        if plan["changes"]:
            issues.append("managed snapshot differs: " + ", ".join(plan["changes"]))
        if not (target / "yuheng-manifest.yaml").exists():
            issues.append("consumer manifest is missing")
    if mode == "apply":
        _apply_plan(plan, target, project_id)
        plan = _snapshot_plan(source, target, project_id)
        if plan["changes"]:
            issues.append("managed snapshot differs after apply: " + ", ".join(plan["changes"]))
    status = "BLOCKED" if issues else "PASS"
    return {
        "status": status,
        "mode": mode,
        "source": str(source),
        "target": str(target),
        "changes": plan["changes"],
        "warnings": plan["warnings"],
        "issues": issues,
        "scriptVersion": SCRIPT_VERSION,
    }


def format_report(report: Mapping[str, Any]) -> str:
    lines = [
        "status: {}".format(report["status"]),
        "mode: {}".format(report.get("mode", "")),
    ]
    for change in report.get("changes", []):
        lines.append("- change: " + change)
    for warning in report.get("warnings", []):
        lines.append("- warning: " + warning)
    for issue in report.get("issues", []):
        lines.append("- error: " + issue)
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="preview changes without modifying files")
    modes.add_argument("--apply", action="store_true", help="atomically apply the managed snapshot")
    modes.add_argument("--verify", action="store_true", help="verify the target without modifying files")
    parser.add_argument("--project-id", default="", help="consumer project id for apply")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    mode = "apply" if args.apply else "verify" if args.verify else "check"
    try:
        report = sync_bundle(
            args.source,
            args.target,
            mode=mode,
            project_id=args.project_id or None,
        )
    except (OSError, SyncError, ValueError) as exc:
        report = {"status": "BLOCKED", "mode": mode, "issues": [str(exc)]}
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.as_json else format_report(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
