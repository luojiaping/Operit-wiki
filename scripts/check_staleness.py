#!/usr/bin/env python3
"""检查评审页相对 source_commit 是否过期。

原理：每页 .status.json 记录 source_repo / source_commit（抓取事实时源码仓库
的 commit）。本脚本对每页的 seed_files 执行
    git diff --name-only <source_commit>..HEAD
变更的 seed 文件再映射回 <id>.facts.json 里引用了该文件的 facts，
输出需要重核的事实清单。

用法:
    python3 scripts/check_staleness.py --root .
    python3 scripts/check_staleness.py --root . --operit-repo ~/workspace/Operit

约定：
- status.json 里的 "source_repo" 取值 "operit" 或 "wiki"，缺失则判为 UNKNOWN。
- seed_files 为空的页无法自动检查，判为 UNKNOWN 并说明原因。
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def git_diff_names(repo: Path, base: str) -> list[str] | None:
    """返回 base..HEAD 之间变更的文件（repo 相对路径）。repo 不是 git 仓库则返回 None。"""
    r = subprocess.run(
        ["git", "-C", str(repo), "diff", "--name-only", f"{base}..HEAD"],
        capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return [l.strip() for l in r.stdout.splitlines() if l.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="wiki 骨架仓库根目录")
    ap.add_argument("--operit-repo", default=str(Path.home() / "workspace/Operit"))
    ap.add_argument("--json", action="store_true", help="输出 JSON 而不是人类可读报告")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    repos = {
        "operit": Path(args.operit_repo).resolve(),
        "wiki": root,
    }
    queue = json.loads((root / "review-queue.json").read_text(encoding="utf-8"))

    diff_cache: dict[tuple[str, str], list[str] | None] = {}
    report = []
    for e in queue["entries"]:
        pid = e["id"]
        batch = pid.split("/")[0]
        stem = pid.split("/")[1]
        status_p = root / "review" / batch / f"{stem}.status.json"
        item = {"id": pid, "verdict": "UNKNOWN", "detail": "", "stale_files": [], "stale_facts": []}
        if not status_p.exists():
            item["detail"] = "缺少 .status.json"
            report.append(item)
            continue
        st = json.loads(status_p.read_text(encoding="utf-8"))
        repo_name = st.get("source_repo")
        base = st.get("source_commit")
        if not repo_name or not base:
            item["detail"] = "未记录 source_repo/source_commit"
            report.append(item)
            continue
        repo = repos.get(repo_name)
        if repo is None or not (repo / ".git").exists():
            item["detail"] = f"source_repo={repo_name} 无法定位 git 仓库"
            report.append(item)
            continue
        seeds: list[str] = e.get("seed_files") or []
        if not seeds:
            item["detail"] = "seed_files 为空，无法自动检查（需人工确认）"
            report.append(item)
            continue
        key = (repo_name, base)
        if key not in diff_cache:
            diff_cache[key] = git_diff_names(repo, base)
        changed = diff_cache[key]
        if changed is None:
            item["detail"] = f"git diff 失败（base={base[:8]} 可能不存在于该仓库）"
            report.append(item)
            continue
        # seed 可能是仓库相对路径；用后缀匹配变更文件
        stale_seeds = [s for s in seeds if any(c == s or c.endswith("/" + s) for c in changed)]
        if not stale_seeds:
            item["verdict"] = "OK"
            item["detail"] = f"相对 {base[:8]}，{len(seeds)} 个 seed 文件无变更"
            report.append(item)
            continue
        item["verdict"] = "STALE"
        item["stale_files"] = stale_seeds
        facts_p = root / "review" / batch / f"{stem}.facts.json"
        if facts_p.exists():
            facts = json.loads(facts_p.read_text(encoding="utf-8"))
            flist = facts if isinstance(facts, list) else facts.get("facts", [])
            for i, fc in enumerate(flist):
                ref = fc.get("ref", "")
                fpath = ref.rsplit(":", 1)[0] if ":" in ref else ref
                if any(s == fpath or s.endswith("/" + fpath) or fpath.endswith("/" + s)
                       for s in stale_seeds):
                    item["stale_facts"].append({"index": i, "ref": ref,
                                               "fact": fc.get("fact", "")[:80]})
        item["detail"] = (f"相对 {base[:8]} 有 {len(stale_seeds)} 个 seed 文件变更，"
                          f"命中 {len(item['stale_facts'])} 条 facts 需重核")
        report.append(item)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        n_ok = sum(1 for r in report if r["verdict"] == "OK")
        n_stale = sum(1 for r in report if r["verdict"] == "STALE")
        n_unk = len(report) - n_ok - n_stale
        print(f"共 {len(report)} 页：OK {n_ok} / STALE {n_stale} / UNKNOWN {n_unk}\n")
        for r in report:
            print(f"[{r['verdict']}] {r['id']}: {r['detail']}")
            for f in r["stale_files"]:
                print(f"    seed 变更: {f}")
            for fc in r["stale_facts"][:10]:
                print(f"    fact#{fc['index']} [{fc['ref']}] {fc['fact']}")
            if len(r["stale_facts"]) > 10:
                print(f"    ...还有 {len(r['stale_facts']) - 10} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
