#!/usr/bin/env python3
"""Build a static route/security inventory for Core System and Infra admin controllers."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


CORE = Path(__file__).resolve().parents[3] / "yuheng-core"
ROOTS = (
    ("system", CORE / "yuheng-module-system/src/main/java/com/yuheng/platform/module/system/controller/admin"),
    ("infra", CORE / "yuheng-module-infra/src/main/java/com/yuheng/platform/module/infra/controller/admin"),
)
MAPPING = re.compile(r"@(Get|Post|Put|Delete|Patch|Request)Mapping\s*(?:\((.*?)\))?", re.S)
CLASS = re.compile(r"\bclass\s+(\w+)")
METHOD = re.compile(r"\bpublic\s+(?:static\s+)?[\w<>?,.\[\] ]+?\s+(\w+)\s*\(")
LITERAL = re.compile(r'"([^"\n]*)"')


def annotation_value(source: str, name: str) -> str:
    match = re.search(rf"@{name}\s*\((.*?)\)", source, re.S)
    if not match:
        return ""
    return " ".join(match.group(1).split())


def scan_controller(area: str, path: Path) -> list[dict[str, str]]:
    source = path.read_text(encoding="utf-8")
    class_match = CLASS.search(source)
    if not class_match:
        return []
    class_prefix = source[:class_match.start()]
    base = annotation_value(class_prefix, "RequestMapping")
    base_paths = LITERAL.findall(base) or [""]
    class_permission = annotation_value(class_prefix, "PreAuthorize")
    class_permit_all = "@PermitAll" in class_prefix
    class_tenant_ignore = "@TenantIgnore" in class_prefix

    matches = list(MAPPING.finditer(source))
    routes: list[dict[str, str]] = []
    for index, mapping in enumerate(matches):
        if mapping.start() < class_match.start():
            continue
        segment_end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        segment = source[mapping.end():segment_end]
        method_match = METHOD.search(segment)
        if not method_match:
            continue
        previous_body_end = source.rfind("}", class_match.end(), mapping.start())
        annotation_start = previous_body_end + 1 if previous_body_end >= 0 else class_match.end()
        annotations = source[annotation_start:mapping.end() + method_match.start()]
        annotation_body = mapping.group(2) or ""
        method_paths = LITERAL.findall(annotation_body) or [""]
        verbs = {
            "Get": "GET", "Post": "POST", "Put": "PUT", "Delete": "DELETE",
            "Patch": "PATCH", "Request": "ANY",
        }
        for base_path in base_paths:
            for method_path in method_paths:
                route = "/".join(part.strip("/") for part in (base_path, method_path) if part.strip("/"))
                routes.append({
                    "area": area,
                    "controller": class_match.group(1),
                    "source": str(path.relative_to(CORE)),
                    "http_method": verbs[mapping.group(1)],
                    "path": "/" + route,
                    "java_method": method_match.group(1),
                    "preauthorize": annotation_value(annotations, "PreAuthorize") or class_permission,
                    "permit_all": str("@PermitAll" in annotations or class_permit_all).lower(),
                    "tenant_ignore": str("@TenantIgnore" in annotations or class_tenant_ignore).lower(),
                    "authentication": "permit-all" if "@PermitAll" in annotations or class_permit_all else "global-auth-required",
                    "permission_source": "method-or-class" if annotation_value(annotations, "PreAuthorize") or class_permission else "none-global-auth-only",
                    "tenant_source": "method-or-class-ignore" if "@TenantIgnore" in annotations or class_tenant_ignore else "tenant-filter-default",
                })
    return routes


def main() -> None:
    routes = [row for area, root in ROOTS for path in sorted(root.glob("**/*Controller.java")) for row in scan_controller(area, path)]
    output = Path(__file__).resolve().parents[2] / "docs/verification/2026-11-11-full-source-migration/controller-security-inventory-20261119"
    output.mkdir(parents=True, exist_ok=True)
    routes.sort(key=lambda row: (row["area"], row["path"], row["http_method"], row["java_method"]))
    summary = {
        "scope": "Core System and Infra admin Controller route annotations",
        "controllers": len({row["source"] for row in routes}),
        "routes": len(routes),
        "routes_with_method_or_class_permission": sum(row["permission_source"] == "method-or-class" for row in routes),
        "permit_all_routes": sum(row["permit_all"] == "true" for row in routes),
        "tenant_ignore_routes": sum(row["tenant_ignore"] == "true" for row in routes),
        "global_auth_only_routes": sum(row["permission_source"] == "none-global-auth-only" and row["permit_all"] == "false" for row in routes),
        "limitations": [
            "Static annotations only; does not evaluate Spring Security runtime matchers or custom expression outcomes.",
            "Does not infer SQL tenant filtering from Mapper/DO relationships or execute requests.",
            "Routes using computed mapping expressions require manual interpretation.",
        ],
    }
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output / "routes.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(routes[0]))
        writer.writeheader()
        writer.writerows(routes)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
