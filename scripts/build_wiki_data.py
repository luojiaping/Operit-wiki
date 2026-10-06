#!/usr/bin/env python3
"""生成正式 Wiki 站的数据：site/data/wiki/pages.json。

正式 wiki 不再有"预览/评审中/规划中"之分：每一页都直接嵌入正文。
- 大纲 11 章 116 页：正文取自 review-queue.json 对应条目的 review/<id>.md（去 frontmatter）。
- 附录章追加 8 个不在大纲里的附录页（batch-09 插件系列 6 页 + batch-10 扫尾 1 页 + batch-10 Room 字段规范 1 页）。
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data" / "wiki" / "pages.json"

# 不在大纲里、需要并入附录章的条目（固定阅读顺序）
APPENDIX_EXTRA = [
    "batch-09/appendix-plugin-capabilities",
    "batch-09/appendix-js-package-dev",
    "batch-09/appendix-plugin-contract",
    "batch-09/appendix-plugin-examples",
    "batch-09/appendix-plugin-dev-guide",
    "batch-09/appendix-toolpkg-contract",
    "batch-10/appendix-uncovered-native",
    "batch-10/appendix-room-field-spec",
]

FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.S)


def strip_frontmatter(md: str) -> str:
    return FRONTMATTER_RE.sub("", md, count=1)


def page_from_entry(entry: dict, pid: str, title: str, module: str) -> dict:
    md_path = ROOT / entry["md"]
    md = strip_frontmatter(md_path.read_text(encoding="utf-8")) if md_path.exists() else ""
    updated = ""
    st_path = (ROOT / "review" / entry["id"]).with_suffix(".status.json")
    if st_path.exists():
        try:
            updated = json.loads(st_path.read_text(encoding="utf-8")).get("updated", "")
        except Exception:
            pass
    return {
        "id": pid, "title": title, "module": module, "md": md,
        "updated": updated, "issue": entry.get("issue"),
    }


def main() -> None:
    v3 = ROOT / "outline" / "outline-v3.yaml"
    op = v3 if v3.exists() else (ROOT / "wiki-work" / "outline.yaml")
    outline = yaml.safe_load(op.read_text(encoding="utf-8"))
    queue = json.loads((ROOT / "review-queue.json").read_text(encoding="utf-8"))
    entries = queue.get("entries", [])

    # page_id（去掉 batch 前缀）-> queue entry
    by_page: dict[str, dict] = {}
    by_full: dict[str, dict] = {}
    for e in entries:
        eid = e.get("id", "")
        by_full[eid] = e
        pid = eid.split("/", 1)[1] if "/" in eid else eid
        by_page[pid] = e

    chapters = []
    total = 0
    for ch in outline["chapters"]:
        pages = []
        for p in ch["pages"]:
            pid = p["id"]
            e = by_page.get(pid)
            if e is None:
                continue
            pages.append(page_from_entry(e, pid, p["title"], p["module"]))
            total += 1
        # 附录章：追加大纲之外的附录页
        if ch["chapter"] == "附录":
            for full_id in APPENDIX_EXTRA:
                e = by_full.get(full_id)
                if e is None:
                    continue
                pid = full_id.split("/", 1)[1]
                pages.append(page_from_entry(e, pid, e["title"], e.get("module", "附录")))
                total += 1
        chapters.append({"chapter": ch["chapter"], "pages": pages})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "outline_version": outline.get("version"),
        "counts": {"total": total},
        "chapters": chapters,
    }, ensure_ascii=False), encoding="utf-8")
    print(f"正式 wiki 数据：{OUT}（共 {total} 页）")


if __name__ == "__main__":
    main()
