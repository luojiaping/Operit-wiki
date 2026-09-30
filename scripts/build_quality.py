#!/usr/bin/env python3
"""聚合各页 quality.json -> site/data/quality.json。

quality.json 是代码走查轨道产物：AI 扫描发现的潜在问题/漏洞，
不进 wiki 正文，待人工逐条评审。字段见 SCHEMA.md §8。
"""
import argparse
import glob
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    queue = json.loads((root / "review-queue.json").read_text(encoding="utf-8"))
    titles = {e["id"]: e.get("title", e["id"]) for e in queue["entries"]}

    findings = []
    for qp in sorted(glob.glob(str(root / "review/*/*.quality.json"))):
        pid = f"{Path(qp).parent.name}/{Path(qp).name[:-len('.quality.json')]}"
        try:
            items = json.loads(Path(qp).read_text(encoding="utf-8"))
        except Exception as ex:
            print(f"WARN: 读 {qp} 失败: {ex}")
            continue
        if not isinstance(items, list):
            print(f"WARN: {qp} 不是数组，已跳过")
            continue
        for i, f in enumerate(items):
            findings.append({
                "id": f"{pid}#{i}",
                "page": pid,
                "page_title": titles.get(pid, pid),
                "severity": f.get("severity", "suggestion"),
                "category": f.get("category", "correctness"),
                "file": f.get("file", ""),
                "line": f.get("line", 0),
                "title": f.get("title", ""),
                "detail": f.get("detail", ""),
                "evidence": f.get("evidence", ""),
                "confidence": f.get("confidence", "medium"),
            })

    totals = {"total": len(findings)}
    for s in ("high", "warning", "suggestion"):
        totals[s] = sum(1 for f in findings if f["severity"] == s)

    out = root / "site/data/quality.json"
    out.write_text(json.dumps({"updated": queue.get("updated", ""),
                               "totals": totals, "findings": findings},
                              ensure_ascii=False), encoding="utf-8")
    print(f"quality: {totals['total']} 条（高危 {totals['high']} / 警告 {totals['warning']} / 建议 {totals['suggestion']}）-> {out}")


if __name__ == "__main__":
    main()
