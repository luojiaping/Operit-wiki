#!/usr/bin/env python3
"""生成 Wiki 预览页的数据：site/data/wiki/pages.json。

每页状态：
  已发布  wiki/<id>.md 存在
  评审中  review-queue.json 中有关联该 id 的条目
  规划中  其余（正文为大纲占位 stub，仅含 outline.yaml 确定性字段）
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data" / "wiki" / "pages.json"


def stub_md(info: dict) -> str:
    lines = [
        f"# {info['title']}",
        "",
        f"> 状态：规划中｜章节：{info['chapter']}｜模块：{info['module']}",
        "",
        "本页正文尚未生成。以下为大纲规划的覆盖范围（来自 outline.yaml）：",
        "",
        "## 计划覆盖的问题",
        "",
    ]
    lines += [f"- {q}" for q in info.get("questions", [])]
    lines += ["", "## 种子文件", ""]
    lines += [f"- `{s}`" for s in info.get("seed_files", [])]
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    outline = yaml.safe_load((ROOT / "wiki-work" / "outline.yaml").read_text(encoding="utf-8"))
    queue = json.loads((ROOT / "review-queue.json").read_text(encoding="utf-8"))
    review_ids = {e.get("page_id") for e in queue.get("entries", []) if e.get("page_id")}

    chapters = []
    counts = {"published": 0, "review": 0, "planned": 0}
    for ch in outline["chapters"]:
        pages = []
        for p in ch["pages"]:
            pid = p["id"]
            wiki_md = ROOT / "wiki" / f"{pid}.md"
            if wiki_md.exists():
                status, md = "published", wiki_md.read_text(encoding="utf-8")
                counts["published"] += 1
            elif pid in review_ids:
                status, md = "review", stub_md({**p, "chapter": ch["chapter"]})
                counts["review"] += 1
            else:
                status, md = "planned", stub_md({**p, "chapter": ch["chapter"]})
                counts["planned"] += 1
            pages.append({
                "id": pid, "title": p["title"], "module": p["module"],
                "status": status, "md": md,
            })
        chapters.append({"chapter": ch["chapter"], "pages": pages})

    outline_status = queue["entries"][0]["status"] if queue.get("entries") else "none"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "outline_version": outline.get("version"),
        "outline_status": outline_status,
        "counts": counts,
        "chapters": chapters,
    }, ensure_ascii=False), encoding="utf-8")
    print(f"wiki 预览数据：{OUT}（已发布 {counts['published']} / 评审中 "
          f"{counts['review']} / 规划中 {counts['planned']}）")


if __name__ == "__main__":
    main()
