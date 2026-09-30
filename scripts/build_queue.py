#!/usr/bin/env python3
"""扫描 review/ 下的待评审条目，生成 review-queue.json（网站数据源）。

条目状态来源：同目录 <entry>.status.json（无则默认为 review-pending）。
status.json 格式: {"status": "review-pending|needs-changes|approved",
                   "issue": 12, "summary": "...", "critic": "通过",
                   "refs_valid": "42/42"}

用法:
    python3 scripts/build_queue.py [--root .]
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

STATUS_DEFAULT = "review-pending"


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end < 0:
        return {}
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root)
    review_dir = root / "review"

    entries = []
    for md in sorted(review_dir.glob("*/*.md")):
        if md.name.endswith((".facts.json", ".lint.md", ".critic.md")):
            continue
        batch = md.parent.name
        entry_id = md.stem
        text = md.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)

        status_path = md.with_suffix(".status.json")
        meta = {}
        if status_path.exists():
            meta = json.loads(status_path.read_text(encoding="utf-8"))

        facts_path = md.with_suffix(".facts.json")
        facts_count = 0
        if facts_path.exists():
            try:
                facts_count = len(json.loads(facts_path.read_text(encoding="utf-8")))
            except Exception:
                pass

        seed_files = []
        m = re.search(r"^#{1,3}\s*(来源|参考|引用)\s*$", text, re.M)
        if m:
            section = text[m.end():]
            seed_files = re.findall(r'`([^`]+?\.(?:kt|java|xml|gradle|kts))`', section[:2000])

        title = fm.get("title", entry_id)
        entries.append({
            "id": f"{batch}/{entry_id}",
            "batch": batch,
            "title": title,
            "module": fm.get("module", ""),
            "status": meta.get("status", STATUS_DEFAULT),
            "issue": meta.get("issue"),
            "issue_title": f"[评审] {title}",
            "md": f"review/{batch}/{md.name}",
            "facts": f"review/{batch}/{facts_path.name}" if facts_path.exists() else "",
            "lint": f"review/{batch}/{entry_id}.lint.md",
            "seed_files": seed_files[:12],
            "facts_count": facts_count,
            "refs_valid": meta.get("refs_valid", ""),
            "critic": meta.get("critic", ""),
            "summary": meta.get("summary", ""),
            "updated": meta.get("updated", ""),
        })

    queue = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "entries": entries,
    }
    out = root / "review-queue.json"
    out.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}: {len(entries)} entries")


if __name__ == "__main__":
    main()
