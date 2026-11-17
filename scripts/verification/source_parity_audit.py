#!/usr/bin/env python3
"""Compare migrated Core System/Infra main sources with the local upstream tree."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


MODULES = {
    "system": ("yuheng-module-system", "yudao-module-system"),
    "infra": ("yuheng-module-infra", "yudao-module-infra"),
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def relative_key(path, root):
    key = path.relative_to(root).as_posix()
    return key.replace("java/com/yuheng/platform/", "java/cn/iocoder/yudao/")


def normalize(path, data):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("com.yuheng.platform", "cn.iocoder.yudao")
    if path.endswith(".java"):
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"//[^\n]*", "", text)
        text = text.replace("jakarta.", "javax.")
        text = re.sub(r"\s+", "", text)
    return text.encode("utf-8")


def files_by_key(root, migrated):
    result = {}
    for path in root.rglob("*"):
        if path.is_file():
            key = relative_key(path, root) if migrated else path.relative_to(root).as_posix()
            result[key] = path
    return result


def audit_module(name, core_root, upstream_root):
    core_files = files_by_key(core_root, True)
    upstream_files = files_by_key(upstream_root, False)
    only_core = sorted(core_files.keys() - upstream_files.keys())
    only_upstream = sorted(upstream_files.keys() - core_files.keys())
    entries = []
    mismatches = []
    for key in sorted(core_files.keys() & upstream_files.keys()):
        core_data = core_files[key].read_bytes()
        upstream_data = upstream_files[key].read_bytes()
        core_normalized = normalize(key, core_data)
        upstream_normalized = normalize(key, upstream_data)
        same = sha256(core_normalized) == sha256(upstream_normalized)
        entries.append({
            "path": key,
            "kind": "java" if key.endswith(".java") else "resource",
            "core_sha256": sha256(core_data),
            "upstream_sha256": sha256(upstream_data),
            "normalized_sha256": sha256(core_normalized),
            "normalized_match": same,
        })
        if not same:
            mismatches.append(key)
    java_count = sum(entry["kind"] == "java" for entry in entries)
    result = {
        "file_count_core": len(core_files),
        "file_count_upstream": len(upstream_files),
        "java_count": java_count,
        "resource_count": len(entries) - java_count,
        "only_core": only_core,
        "only_upstream": only_upstream,
        "normalized_mismatches": mismatches,
        "entries": entries,
    }
    result["result"] = "PASS" if not only_core and not only_upstream and not mismatches else "DIFF"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-root", type=Path, default=Path("../yuheng-core"))
    parser.add_argument("--upstream-root", type=Path, default=Path("../ruoyi-vue-pro"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    modules = {}
    for name, (core_module, upstream_module) in MODULES.items():
        core_root = args.core_root / core_module / "src/main"
        upstream_root = args.upstream_root / upstream_module / "src/main"
        if not core_root.is_dir() or not upstream_root.is_dir():
            parser.error(f"missing source roots for {name}: {core_root} / {upstream_root}")
        modules[name] = audit_module(name, core_root, upstream_root)

    document = {
        "result": "PASS" if all(m["result"] == "PASS" for m in modules.values()) else "DIFF",
        "normalization": [
            "path prefix java/com/yuheng/platform/ to java/cn/iocoder/yudao/",
            "Java package prefix and jakarta/javax namespace",
            "Java comments and whitespace",
            "UTF-8 BOM and line endings",
            "resource package prefix and line endings",
        ],
        "modules": modules,
    }
    rendered = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    print(json.dumps({name: {k: module[k] for k in (
        "result", "file_count_core", "java_count", "resource_count",
        "only_core", "only_upstream", "normalized_mismatches")
    } for name, module in modules.items()}, ensure_ascii=False), file=sys.stderr)
    return 0 if document["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
