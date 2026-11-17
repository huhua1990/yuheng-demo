#!/usr/bin/env python3
"""Compare ERP/member business template source with the Demo consumer copy."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalize(module, path, data):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace(
        f"com.yuheng.template.{module}", f"com.yuheng.demo.module.{module}"
    )
    if path.endswith(".java"):
        text = text.replace("jakarta.", "javax.")
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"//[^\n]*", "", text)
        text = re.sub(r"\s+", "", text)
    return text.encode("utf-8")


def template_key(module, relative):
    if relative.startswith("ui/erp/") or relative.startswith("ui/member/"):
        return "ui/views/" + relative[len("ui/"):]
    if relative.startswith("ui/api/"):
        api_path = relative[len("ui/api/"):]
        return "ui/api/" + (api_path if module == "erp" else f"{module}/{api_path}")
    if relative.startswith("resources/"):
        return "backend/resources/" + relative[len("resources/"):]
    return "backend/java/" + relative


def consumer_key(relative):
    if relative.endswith(".java"):
        return "backend/java/" + relative
    return "backend/resources/" + relative


def classify_template_asset(relative):
    if relative.startswith("db/"):
        return "database_migration"
    if relative == "README.md" or relative.endswith(".md"):
        return "documentation"
    if relative.endswith(".http"):
        return "http_example"
    if relative.endswith(".yaml") or relative.endswith(".yml"):
        return "module_configuration"
    return "unclassified"


def audit_module(module, templates_root, consumer_java_root, consumer_resources_root,
                 consumer_ui_root):
    template_root = templates_root / f"template-{module}"
    template_files = {}
    auxiliary = {}
    for path in template_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(template_root).as_posix()
        if relative.startswith("db/"):
            auxiliary[relative] = {
                "kind": classify_template_asset(relative),
                "sha256": digest(path.read_bytes()),
            }
        elif relative.startswith("ui/") and (
            relative.startswith("ui/erp/") or relative.startswith("ui/member/")
            or relative.startswith("ui/api/")
        ):
            template_files[template_key(module, relative)] = path
        elif relative.endswith(".java") and (
            relative.startswith(("controller/", "api/", "convert/", "dal/",
                                 "enums/", "framework/", "mq/", "service/"))
            or relative == "package-info.java"
        ):
            template_files[template_key(module, relative)] = path
        elif relative.startswith("resources/"):
            template_files[template_key(module, relative)] = path
        else:
            auxiliary[relative] = {
                "kind": classify_template_asset(relative),
                "sha256": digest(path.read_bytes()),
            }

    consumer_files = {}
    java_root = consumer_java_root / module
    if java_root.is_dir():
        for path in java_root.rglob("*.java"):
            consumer_files[consumer_key(path.relative_to(java_root).as_posix())] = path
    if module == "erp":
        resource_root = consumer_resources_root
        for path in (resource_root / "mapper/statistics").glob("Erp*StatisticsMapper.xml"):
            consumer_files["backend/resources/mapper/statistics/" + path.name] = path
    ui_root = consumer_ui_root
    for kind, directory in (("views", "views"), ("api", "api")):
        source = ui_root / directory / module
        if source.is_dir():
            for path in source.rglob("*"):
                if path.is_file():
                    consumer_files[f"ui/{kind}/{module}/" + path.relative_to(source).as_posix()] = path

    keys = sorted(template_files.keys() | consumer_files.keys())
    only_template = []
    only_consumer = []
    mismatches = []
    entries = []
    for key in keys:
        source = template_files.get(key)
        target = consumer_files.get(key)
        if source is None:
            only_consumer.append(key)
            continue
        if target is None:
            only_template.append(key)
            continue
        source_bytes = source.read_bytes()
        target_bytes = target.read_bytes()
        source_normalized = normalize(module, key, source_bytes)
        target_normalized = normalize(module, key, target_bytes)
        matched = digest(source_normalized) == digest(target_normalized)
        if not matched:
            mismatches.append(key)
        entries.append({
            "path": key,
            "kind": key.split("/", 1)[0],
            "template_sha256": digest(source_bytes),
            "consumer_sha256": digest(target_bytes),
            "normalized_sha256": digest(source_normalized),
            "normalized_match": matched,
        })

    migration_files = [
        {"path": path, **item} for path, item in sorted(auxiliary.items())
        if item["kind"] == "database_migration"
    ]
    non_migration_assets = [
        {"path": path, **item} for path, item in sorted(auxiliary.items())
        if item["kind"] != "database_migration"
    ]
    result = "PASS" if not only_template and not only_consumer and not mismatches else "DIFF"
    return {
        "result": result,
        "template_source_count": len(template_files),
        "consumer_source_count": len(consumer_files),
        "matched_count": len(entries),
        "only_template": only_template,
        "only_consumer": only_consumer,
        "normalized_mismatches": mismatches,
        "entries": entries,
        "template_database_migrations": migration_files,
        "template_auxiliary_assets": non_migration_assets,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--templates-root", type=Path, default=Path("../yuheng-business-templates"))
    parser.add_argument("--demo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    demo = args.demo_root
    modules = {}
    for module in ("erp", "member"):
        modules[module] = audit_module(
            module,
            args.templates_root,
            demo / "yuheng-demo-server/yuheng-demo-business/src/main/java/com/yuheng/demo/module",
            demo / "yuheng-demo-server/yuheng-demo-business/src/main/resources",
            demo / "yuheng-demo-ui/src",
        )
    document = {
        "comparison": "yuheng-business-templates to yuheng-demo",
        "normalization": [
            "template business package com.yuheng.template.<module> to consumer package com.yuheng.demo.module.<module>",
            "Java comments and whitespace",
            "UTF-8 BOM and line endings",
            "Jakarta/Javax namespace",
            "database migrations and non-runtime auxiliary assets reported separately",
        ],
        "result": "PASS" if all(item["result"] == "PASS" for item in modules.values()) else "DIFF",
        "modules": modules,
    }
    rendered = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    summary = {
        name: {key: module[key] for key in (
            "result", "template_source_count", "consumer_source_count", "matched_count",
            "only_template", "only_consumer", "normalized_mismatches",
        )}
        for name, module in modules.items()
    }
    print(json.dumps(summary, ensure_ascii=False), file=sys.stderr)
    return 0 if document["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
