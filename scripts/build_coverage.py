#!/usr/bin/env python3
"""构建 wiki 覆盖进度数据：site/data/coverage.json。

- 全量文件：wiki-work/repo-map.json（3067 文件 / 1402 kt / ~88 万行）
- 已读：出现在任一 review/<batch>/<id>.facts.json 引用（file:line 的 file 部分）
  或 review-queue.json 条目 seed_files 中的文件
- 已审批：已读文件中，归属 status=approved 页面的文件
- 状态：0=未读 1=已读（待审批） 2=已审批

用法: python3 scripts/build_coverage.py --root . [--repo ~/workspace/Operit]
"""
import argparse
import glob
import json
from pathlib import Path


def file_loc(p: Path) -> int:
    try:
        with open(p, "r", encoding="utf-8", errors="strict") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--repo", default=str(Path.home() / "workspace/Operit"))
    args = ap.parse_args()
    root = Path(args.root).resolve()
    repo = Path(args.repo).resolve()

    rmap = json.loads((root / "wiki-work/repo-map.json").read_text(encoding="utf-8"))
    queue = json.loads((root / "review-queue.json").read_text(encoding="utf-8"))

    # 全量文件：path -> module
    all_files: dict[str, str] = {}
    for mod, info in rmap["modules"].items():
        for f in info.get("files", []):
            all_files[f] = mod

    # 每页状态 + seed
    page_status: dict[str, str] = {}
    page_title: dict[str, str] = {}
    seed_of: dict[str, list[str]] = {}
    for e in queue["entries"]:
        pid = e["id"]
        page_status[pid] = e.get("status", "")
        page_title[pid] = e.get("title", pid)
        seed_of[pid] = e.get("seed_files") or []

    # facts 引用 -> {file: [page_ids]}
    ref_pages: dict[str, list[str]] = {}
    for facts_p in glob.glob(str(root / "review/*/*.facts.json")):
        pid = f"{Path(facts_p).parent.name}/{Path(facts_p).name[:-len('.facts.json')]}"
        try:
            facts = json.loads(Path(facts_p).read_text(encoding="utf-8"))
        except Exception:
            continue
        flist = facts if isinstance(facts, list) else facts.get("facts", [])
        for fc in flist:
            ref = fc.get("ref", "")
            fpath = ref.rsplit(":", 1)[0] if ":" in ref else ref
            if fpath:
                ref_pages.setdefault(fpath, [])
                if pid not in ref_pages[fpath]:
                    ref_pages[fpath].append(pid)

    # seed 文件也算已读
    for pid, seeds in seed_of.items():
        for s in seeds:
            ref_pages.setdefault(s, [])
            if pid not in ref_pages[s]:
                ref_pages[s].append(pid)

    files_out = []
    mod_stats: dict[str, dict] = {}
    for mod, info in rmap["modules"].items():
        mod_stats[mod] = {"name": mod, "dir": info.get("dir", mod),
                          "files": 0, "kt_files": 0, "loc": 0,
                          "read_files": 0, "approved_files": 0,
                          "read_loc": 0, "approved_loc": 0}

    totals = {"files": 0, "kt_files": 0, "loc": 0,
              "read_files": 0, "approved_files": 0,
              "read_loc": 0, "approved_loc": 0}

    for fpath, mod in sorted(all_files.items()):
        is_kt = fpath.endswith(".kt")
        loc = file_loc(repo / fpath)
        pages = [p for p in ref_pages.get(fpath, []) if p in page_status]
        status = 0
        cover_page = ""
        if pages:
            approved = [p for p in pages if page_status.get(p) == "approved"]
            status = 2 if approved else 1
            cover_page = (approved or pages)[0]
        ms = mod_stats[mod]
        ms["files"] += 1
        ms["loc"] += loc
        totals["files"] += 1
        totals["loc"] += loc
        if is_kt:
            ms["kt_files"] += 1
            totals["kt_files"] += 1
        if status >= 1:
            ms["read_files"] += 1
            ms["read_loc"] += loc
            totals["read_files"] += 1
            totals["read_loc"] += loc
        if status == 2:
            ms["approved_files"] += 1
            ms["approved_loc"] += loc
            totals["approved_files"] += 1
            totals["approved_loc"] += loc
        files_out.append({"p": fpath, "m": mod, "kt": 1 if is_kt else 0,
                          "loc": loc, "s": status, "page": cover_page})

    cov = {
        "updated": queue.get("updated", ""),
        "source_commit": "dbf71916fae9750cfdc9f9a774f5a0fee56633fb",
        "totals": totals,
        "modules": [mod_stats[m] for m in rmap["modules"]],
        "files": files_out,
    }
    out = root / "site/data/coverage.json"
    out.write_text(json.dumps(cov, ensure_ascii=False), encoding="utf-8")
    t = totals
    print(f"coverage: {t['read_files']}/{t['files']} 文件已读, "
          f"{t['approved_files']}/{t['files']} 已审批, "
          f"{t['read_loc']}/{t['loc']} 行已读 -> {out}")


if __name__ == "__main__":
    main()
