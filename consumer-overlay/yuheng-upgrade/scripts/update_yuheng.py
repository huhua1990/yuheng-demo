#!/usr/bin/env python3
"""Preview or apply Yuheng dependency versions from a core release manifest."""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional


VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
MANIFEST_FIELDS = {
    "codeVersion": re.compile(r"^(codeVersion:\s*)([^\s#]+)(.*)$", re.MULTILINE),
    "server": re.compile(r"^(  server:\s*)([^\s#]+)(.*)$", re.MULTILINE),
    "ui": re.compile(r"^(\s+ui:\s*)(['\"]?)([^\s'\"#]+)(['\"]?)(.*)$", re.MULTILINE),
}
SERVER_ARTIFACT_RE = re.compile(r"^com\.yuheng:yuheng-server:(.+)$")
UI_ARTIFACT_RE = re.compile(r"^yuheng-ui@(.+)$")


class UpgradeError(Exception):
    pass


def parse_release_manifest(path: Path) -> Dict[str, str]:
    text = path.read_text(encoding="utf-8")
    values: Dict[str, str] = {}
    for field, pattern in MANIFEST_FIELDS.items():
        matches = list(pattern.finditer(text))
        if len(matches) != 1:
            raise UpgradeError("expected exactly one {} field in {}".format(field, path))
        match = matches[0]
        raw = match.group(3) if field == "ui" else match.group(2)
        artifact_pattern = SERVER_ARTIFACT_RE if field == "server" else UI_ARTIFACT_RE if field == "ui" else None
        if artifact_pattern:
            artifact = artifact_pattern.fullmatch(raw)
            if not artifact:
                raise UpgradeError("invalid {} artifact in {}: {}".format(field, path, raw))
            value = artifact.group(1)
        else:
            value = raw
        if not VERSION_RE.fullmatch(value):
            raise UpgradeError("invalid {} version in {}: {}".format(field, path, value))
        values[field] = value
    return values


def replace_once(text: str, pattern: re.Pattern, replacement: str, label: str) -> str:
    updated, count = pattern.subn(replacement, text)
    if count != 1:
        raise UpgradeError("expected exactly one {} field, found {}".format(label, count))
    return updated


def stage_updates(root: Path, versions: Dict[str, str]) -> Dict[Path, str]:
    pom_path = root / "pom.xml"
    package_path = root / "yuheng-demo-ui/package.json"
    manifest_path = root / "yuheng-manifest.yaml"
    pom = pom_path.read_text(encoding="utf-8")
    package = json.loads(package_path.read_text(encoding="utf-8"))
    manifest = manifest_path.read_text(encoding="utf-8")

    pom = replace_once(
        pom,
        re.compile(r"(<yuheng\.version>)([^<]+)(</yuheng\.version>)"),
        lambda m: m.group(1) + versions["server"] + m.group(3),
        "yuheng.version",
    )
    dependencies = package.get("dependencies")
    if not isinstance(dependencies, dict) or "yuheng-ui" not in dependencies:
        raise UpgradeError("package.json is missing dependencies.yuheng-ui")
    package["dependencies"]["yuheng-ui"] = versions["ui"]

    manifest = replace_once(
        manifest,
        MANIFEST_FIELDS["codeVersion"],
        lambda m: m.group(1) + versions["codeVersion"] + m.group(3),
        "consumer codeVersion",
    )
    manifest = replace_once(
        manifest,
        MANIFEST_FIELDS["server"],
        lambda m: m.group(1) + "com.yuheng:yuheng-server:" + versions["server"] + m.group(3),
        "consumer server artifact",
    )
    manifest = replace_once(
        manifest,
        MANIFEST_FIELDS["ui"],
        lambda m: m.group(1) + m.group(2) + "yuheng-ui@" + versions["ui"] + m.group(4) + m.group(5),
        "consumer UI artifact",
    )

    package_text = json.dumps(package, ensure_ascii=False, indent=2) + "\n"
    return {pom_path: pom, package_path: package_text, manifest_path: manifest}

def check_clean_targets(root: Path, paths) -> None:
    result = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--", *[str(p.relative_to(root)) for p in paths]],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise UpgradeError("unable to inspect Git status: " + result.stderr.strip())
    if result.stdout.strip():
        raise UpgradeError("upgrade target files have existing Git changes; review or save them first:\n" + result.stdout.rstrip())


def atomic_write(path: Path, content: str) -> None:
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="consumer repository root (default: current directory)")
    parser.add_argument("--from-manifest", required=True, type=Path, help="core release/yuheng-manifest.yaml")
    parser.add_argument("--apply", action="store_true", help="write the reviewed version changes")
    return parser


def main(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    release_manifest = args.from_manifest.resolve()
    try:
        versions = parse_release_manifest(release_manifest)
        updates = stage_updates(root, versions)
        check_clean_targets(root, updates)
        print("Target versions:")
        print("  codeVersion: {}".format(versions["codeVersion"]))
        print("  yuheng-server: {}".format(versions["server"]))
        print("  yuheng-ui: {}".format(versions["ui"]))
        print("Files:")
        for path in updates:
            print("  {}".format(path.relative_to(root)))
        if not args.apply:
            print("Preview only. Re-run with --apply to write these values.")
            return 0
        for path, content in updates.items():
            atomic_write(path, content)
        print("Applied version updates.")
        return 0
    except (OSError, json.JSONDecodeError, UpgradeError) as exc:
        print("Upgrade stopped: {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
