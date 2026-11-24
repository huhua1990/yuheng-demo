#!/usr/bin/env python3
"""Independently audit ERP and Member Skill initialization in a disposable consumer."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT.parent / "yuheng-business-templates"
MODULES = {
    "erp": "template-update-mapping.example.json",
    "member": "template-member-mapping.example.json",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mapped_sources(mapping: dict) -> dict[str, bytes]:
    result = {}
    for item in mapping["mappings"]:
        source = (TEMPLATES / item["source"]).resolve()
        files = [source] if source.is_file() else sorted(path for path in source.rglob("*") if path.is_file())
        for path in files:
            relative = Path(path.name) if source.is_file() else path.relative_to(source)
            target = (Path(item["target"]) / relative).as_posix()
            content = path.read_bytes()
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                pass
            else:
                for old, new in mapping.get("replacements", []):
                    text = text.replace(old, new)
                content = text.encode("utf-8")
            if target in result:
                raise ValueError(f"duplicate mapped target: {target}")
            result[target] = content
    return result


def run() -> dict:
    template_commit = subprocess.check_output(
        ["git", "-C", str(TEMPLATES), "rev-parse", "HEAD"], text=True
    ).strip()
    modules = {}
    with tempfile.TemporaryDirectory(prefix="yuheng-template-skill-init-audit-") as temporary:
        temporary_root = Path(temporary)
        consumer = temporary_root / "consumer"
        consumer.mkdir()
        subprocess.run(["git", "init", "-q", str(consumer)], check=True)
        (consumer / "README.md").write_text("Disposable Skill initialization audit.\n")

        for module, mapping_file in MODULES.items():
            mapping = json.loads((TEMPLATES / "docs" / mapping_file).read_text(encoding="utf-8"))
            mapping["mappings"] = [
                {
                    "source": item["source"],
                    "target": f"modules/{module}/" + item["target"].split("/", 1)[1],
                }
                for item in mapping["mappings"]
            ]
            mapping_path = temporary_root / f"{module}-mapping.json"
            mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")
            initialized = subprocess.run(
                [
                    "python3", str(TEMPLATES / "tools/template_update.py"),
                    "--template-root", str(TEMPLATES),
                    "--consumer-root", str(consumer),
                    "--mapping", str(mapping_path),
                    "--apply",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if initialized.returncode:
                raise RuntimeError(initialized.stderr or initialized.stdout)

            expected = mapped_sources(mapping)
            actual = {
                path.relative_to(consumer).as_posix(): path.read_bytes()
                for path in (consumer / f"modules/{module}").rglob("*")
                if path.is_file()
            }
            missing = sorted(set(expected) - set(actual))
            extra = sorted(set(actual) - set(expected))
            different = sorted(
                path for path in set(expected) & set(actual)
                if sha256(expected[path]) != sha256(actual[path])
            )
            modules[module] = {
                "mapping": mapping_file,
                "expected_file_count": len(expected),
                "created_file_count": len(actual),
                "missing": missing,
                "extra": extra,
                "byte_different": different,
                "result": "PASS" if not (missing or extra or different) else "FAIL",
            }

    return {
        "result": "PASS" if all(item["result"] == "PASS" for item in modules.values()) else "FAIL",
        "templates_commit": template_commit,
        "consumer_is_disposable_git_project": True,
        "consumer_removed_after_audit": not consumer.exists(),
        "modules": modules,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run()
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
