#!/usr/bin/env python3
"""把 outline-v3.yaml 切成 7 个日批次（tracking/shards/day-N.json）。

规则：
- 排除已有评审条目的 5 个总览页（batch-01 已覆盖，不重做）
- 剩余 111 页按章节顺序切成 7 片（约 16 页/天），尽量不把一章拆太散
- 每片记录 page id/title/module/seed_files/est_lines，便于 worker 领取
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUTLINE = ROOT / "outline" / "outline-v3.yaml"
SHARD_DIR = ROOT / "tracking" / "shards"

# batch-01 已评审的总览页：v3 里保留为总览，不重做
DONE = {"arch-overview", "core-tools", "core-chat", "api-chat", "data-model"}

N_DAYS = 7


def main() -> None:
    o = yaml.safe_load(OUTLINE.read_text(encoding="utf-8"))
    pages = []
    for c in o["chapters"]:
        for p in c["pages"]:
            if p["id"] in DONE:
                continue
            pages.append({
                "id": p["id"],
                "title": p["title"],
                "chapter": c["chapter"],
                "module": p.get("module", ""),
                "est_lines": p.get("est_lines", 0) or 0,
                "seed_files": p.get("seed_files", []),
                "questions": p.get("questions", []),
                "notes": p.get("notes", ""),
            })
    # 连续切分 + 按 est_lines 均衡（DP：把序列分成 7 段，最小化最大段行数）
    n = len(pages)
    lines = [p["est_lines"] for p in pages]
    prefix = [0]
    for x in lines:
        prefix.append(prefix[-1] + x)
    INF = float("inf")
    # dp[k][i] = 前 i 页分成 k 段时的最小最大段和；prev 记录切点
    dp = [[INF] * (n + 1) for _ in range(N_DAYS + 1)]
    prev = [[0] * (n + 1) for _ in range(N_DAYS + 1)]
    dp[0][0] = 0
    for k in range(1, N_DAYS + 1):
        for i in range(k, n + 1):
            for j in range(k - 1, i):
                seg = prefix[i] - prefix[j]
                cand = max(dp[k - 1][j], seg)
                if cand < dp[k][i]:
                    dp[k][i] = cand
                    prev[k][i] = j
    cuts, i = [], n
    for k in range(N_DAYS, 0, -1):
        j = prev[k][i]
        cuts.append((j, i))
        i = j
    cuts.reverse()
    SHARD_DIR.mkdir(parents=True, exist_ok=True)
    shards = []
    for d, (a, b) in enumerate(cuts):
        chunk = pages[a:b]
        if not chunk:
            continue
        total_lines = sum(p["est_lines"] for p in chunk)
        shard = {
            "day": d + 1,
            "pages": chunk,
            "page_count": len(chunk),
            "est_lines": total_lines,
            "status": "pending",
        }
        (SHARD_DIR / f"day-{d + 1}.json").write_text(
            json.dumps(shard, ensure_ascii=False, indent=1), encoding="utf-8")
        shards.append((d + 1, len(chunk), total_lines))
    print(f"{len(pages)} pages -> {len(shards)} shards")
    for d, n, lines in shards:
        print(f"  day-{d}: {n} pages, est. {lines:,} lines")


if __name__ == "__main__":
    main()
