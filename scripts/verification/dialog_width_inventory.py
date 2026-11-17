#!/usr/bin/env python3
"""Inventory System/Infra compat Dialog calls that inherit the default width."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DIALOG_TAG = re.compile(r"<Dialog\b([\s\S]*?)>")
WIDTH_ATTRIBUTE = re.compile(r"(?<![\w-])(?:[:]|v-bind:)?width\s*=")


def inventory(core: Path) -> dict:
    root = core / "yuheng-ui/compat/views"
    component = core / "yuheng-ui/compat/components/Dialog/src/Dialog.vue"
    if not root.is_dir() or not component.is_file():
        raise FileNotFoundError("Core compat views or Dialog component not found")
    component_text = component.read_text(encoding="utf-8")
    match = re.search(r"width:\s*propTypes\.oneOfType\(\[String,\s*Number\]\)\.def\('([^']+)'\)", component_text)
    if not match:
        raise ValueError("Cannot identify Dialog default width; review the component before using this inventory")

    result = {"default_width": match.group(1), "areas": {}}
    for area in ("system", "infra"):
        groups: dict[str, list[dict]] = {"inherited": [], "explicit": []}
        for path in sorted((root / area).rglob("*.vue")):
            text = path.read_text(encoding="utf-8")
            for tag in DIALOG_TAG.finditer(text):
                key = "explicit" if WIDTH_ATTRIBUTE.search(tag.group(1)) else "inherited"
                groups[key].append({
                    "file": str(path.relative_to(core)),
                    "line": text.count("\n", 0, tag.start()) + 1,
                })
        result["areas"][area] = groups
    result["limitations"] = (
        "Static source inventory only: each entry needs runtime and viewport verification; "
        "dynamic components, wrappers, and attributes forwarded through v-bind are not resolved."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", type=Path, default=Path(__file__).resolve().parents[3] / "yuheng-core")
    args = parser.parse_args()
    print(json.dumps(inventory(args.core), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
