#!/usr/bin/env python3
"""记录文件级阅读状态 -> tracking/read-status.json（Git 跟踪）。

状态只有两种：complete（整文件 100% 读完，有证据）/ partial。
absent = unread；"touched"（被 facts/seed 引用但未证全读）由 build_coverage.py 推导，不存这里。

用法：
  python3 scripts/record_read.py --batch quality-scan-01 --evidence review/batch-01/api-chat.quality.json --files /tmp/list.txt
  python3 scripts/record_read.py --batch batch-02 --evidence review/batch-02/worker-report.md --files /tmp/list2.txt --status partial
"""
import argparse
import datetime
import json
import subprocess
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--repo", default="")
    ap.add_argument("--batch", required=True)
    ap.add_argument("--evidence", required=True, help="证据路径（仓库相对路径），如某页的 .quality.json")
    ap.add_argument("--files", required=True, help="文件清单，每行一个仓库相对路径")
    ap.add_argument("--status", default="complete", choices=["complete", "partial"])
    args = ap.parse_args()
    root = Path(args.root).resolve()
    repo = Path(args.repo).resolve() if args.repo else Path("/home/hatch/workspace/Operit")

    try:
        repo_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                                     capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        repo_commit = "unknown"

    store = root / "tracking" / "read-status.json"
    data = {"repo_commit": repo_commit, "updated": "", "files": {}}
    if store.exists():
        data = json.loads(store.read_text(encoding="utf-8"))

    today = datetime.date.today().isoformat()
    paths = [ln.strip() for ln in Path(args.files).read_text(encoding="utf-8").splitlines() if ln.strip()]
    n_new = 0
    for p in paths:
        fp = repo / p
        lines = sum(1 for _ in fp.open(encoding="utf-8", errors="replace")) if fp.is_file() else 0
        prev = data["files"].get(p, {}).get("status")
        data["files"][p] = {"status": args.status, "batch": args.batch, "date": today,
                            "evidence": args.evidence, "lines": lines}
        if prev != args.status:
            n_new += 1

    data["repo_commit"] = repo_commit
    data["updated"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    store.parent.mkdir(exist_ok=True)
    store.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    n_complete = sum(1 for v in data["files"].values() if v["status"] == "complete")
    print(f"record_read: {args.batch} {args.status} {len(paths)} 个文件（新增/变更 {n_new}），"
          f"累计 complete {n_complete} -> {store}")


if __name__ == "__main__":
    main()
