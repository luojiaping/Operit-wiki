#!/usr/bin/env python3
"""从 GitHub Issues 拉取已批准的教程投稿，生成 site/data/tutorials.json。

投稿流：用户用 .github/ISSUE_TEMPLATE/tutorial.yml 提 issue（自动打 tutorial 标签），
维护者觉得 OK 就加 tutorial-approved 标签，下次部署时本脚本收录进教程区。
与 wiki 评审队列完全独立，不污染 wiki。
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data" / "tutorials.json"
REPO = "luojiaping/Operit-wiki"


def gh_issues():
    out = subprocess.run(
        ["gh", "api", f"repos/{REPO}/issues?state=open&labels=tutorial-approved&per_page=100",
         "--paginate"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout or "[]")


def clean_summary(body: str) -> str:
    if not body:
        return ""
    # 去掉 issue 模板的字段头，取正文前 150 字
    text = re.sub(r"^#{1,3}\s+.*$", "", body, flags=re.M)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:150] + ("…" if len(text) > 150 else "")


def main():
    try:
        issues = gh_issues()
    except Exception as e:
        print(f"WARN: fetch tutorial issues failed: {e}", file=sys.stderr)
        sys.exit(1)
    tutorials = []
    for i in issues:
        if "pull_request" in i:
            continue
        tutorials.append({
            "title": re.sub(r"^\[教程\]\s*", "", i.get("title", "")),
            "summary": clean_summary(i.get("body") or ""),
            "author": (i.get("user") or {}).get("login", ""),
            "date": (i.get("created_at") or "")[:10],
            "url": i.get("html_url", ""),
            "issue": i.get("number"),
        })
    tutorials.sort(key=lambda t: t["date"], reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "tutorials": tutorials,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}: {len(tutorials)} tutorials")


if __name__ == "__main__":
    main()
