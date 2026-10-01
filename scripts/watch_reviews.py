#!/usr/bin/env python3
"""评审 Issue 批准检测：owner 在评论区发表"通过/批准/LGTM"即自动翻状态。

每 15 分钟由 cron 运行一次。只处理 status=review-pending 且配有 issue 号的条目。
检测到 owner（luojiaping）的新批准评论后：
  1. 把对应 .status.json 改为 approved，并记录 approved_by_comment_id（防重复翻转）
  2. 在 Issue 下留言确认
  3. git commit + push
  4. build_queue.py -> deploy_site.sh（走评审同步铁律）

批准判定（owner 评论正文）：
  - 含"通过"/"批准"/"LGTM"（不区分大小写）=> 批准
  - 但"不通过/没通过/未批准" => 不算；含"需修改"/"打回" => 不算（等 agent 跟进）
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "luojiaping/Operit-wiki"
OWNER = "luojiaping"
QUEUE = ROOT / "review-queue.json"

APPROVE_RE = re.compile(r"通过|批准|LGTM", re.IGNORECASE)
NEG_RE = re.compile(r"(不|没|未)\s*(通过|批准)")
REJECT_RE = re.compile(r"需修改|打回")
# 流水线自己的留言也是用 owner 身份发的，必须排除，否则 watcher 会把
# "critic 独立复验结论通过""v3 重写版已完成并上评审站"等自家留言误判为用户批准。
# 判定：凡带评审页链接（entry.html?id=）或命中流水线前缀的，一律不是用户批准。
PIPELINE_RE = re.compile(
    r"luojiaping\.github\.io/Operit-wiki/entry\.html\?id="
    r"|^(Day |v\d*\s*重写版|✅\s*收到|覆盖率扫尾|已按您的|waifu\s*已补充|评审页已上站|交付更新|大纲已更新)"
)


def sh(*args, check=True):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=check)


def gh_api(path):
    r = sh("gh", "api", path, "--paginate")
    return json.loads(r.stdout or "[]")


def is_approval(body: str) -> bool:
    if not body:
        return False
    if PIPELINE_RE.search(body):
        return False
    if NEG_RE.search(body):
        return False
    if REJECT_RE.search(body):
        return False
    return bool(APPROVE_RE.search(body))


def find_status_file(entry_id: str) -> Path | None:
    for p in (ROOT / "review").rglob("*.status.json"):
        rel = p.relative_to(ROOT / "review").with_suffix("")
        if str(rel) == entry_id or str(rel).replace(".status", "") == entry_id:
            return p
    # fallback: entry_id like batch-02/core-chat
    cand = ROOT / "review" / (entry_id + ".status.json")
    return cand if cand.exists() else None


def main() -> int:
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    entries = queue.get("entries", [])
    flipped = []

    for e in entries:
        if e.get("status") != "review-pending":
            continue
        issue = e.get("issue")
        if not issue:
            continue
        sp = find_status_file(e["id"])
        if not sp:
            print(f"WARN: 找不到 status 文件: {e['id']}", file=sys.stderr)
            continue
        st = json.loads(sp.read_text(encoding="utf-8"))
        if st.get("status") != "review-pending":
            continue
        # 水位线初始化：null/0 表示"回炉后未定位"，必须先以前移到当前最新评论，
        # 否则旧批准评论会被重新误判（2026-10-01 事故：or 0 导致已批准页被反复翻转）。
        # 注意：这里只做内存初始化，不写回文件；真正的批准仍以后续新评论为准。
        seen_id = st.get("approved_by_comment_id") or 0

        try:
            comments = gh_api(f"repos/{REPO}/issues/{issue}/comments")
        except subprocess.CalledProcessError as ex:
            print(f"WARN: Issue #{issue} 评论拉取失败: {ex}", file=sys.stderr)
            continue

        if seen_id == 0 and comments:
            # 回炉/新页尚未定位水位线：前移到最新评论，避免历史评论误触发。
            seen_id = max(c.get("id", 0) for c in comments)
            st["approved_by_comment_id"] = seen_id
            sp.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        hit = None
        for c in comments:
            if c.get("id", 0) <= seen_id:
                continue
            if (c.get("user") or {}).get("login") != OWNER:
                continue
            if is_approval(c.get("body") or ""):
                hit = c
                break

        if not hit:
            continue

        st["status"] = "approved"
        st["approved_by_comment_id"] = hit["id"]
        st["approved_by"] = OWNER
        st["approved_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        st["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        sp.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        flipped.append((e, hit))

        sh("gh", "issue", "comment", str(issue), "--body",
           f"✅ 收到，状态已更新，评审站稍后自动同步。（触发评论：{hit['html_url']}）")

    if not flipped:
        print("no approvals detected")
        return 0

    sh("git", "add", "-A")
    r = sh("git", "diff", "--cached", "--quiet", check=False)
    if r.returncode != 0:
        ids = "、".join(e["id"] for e, _ in flipped)
        sh("git", "commit", "-m", f"评审自动批准（Issue 评论检测）: {ids}")
        sh("git", "push")
    sh("python3", str(ROOT / "scripts" / "build_queue.py"))
    sh("bash", str(ROOT / "scripts" / "deploy_site.sh"))
    print(f"flipped {len(flipped)}: " + "、".join(e["id"] for e, _ in flipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
