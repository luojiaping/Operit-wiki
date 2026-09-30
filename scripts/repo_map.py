#!/usr/bin/env python3
"""阶段 0：repo map 生成器（纯确定性，零 LLM 写作）。

幂等：输出只取决于仓库当前状态，可重复运行，结果按 key 排序。

用法:
    python3 scripts/repo_map.py --repo ~/workspace/Operit --out wiki-work

产物:
    wiki-work/repo-map.json   模块分组 + 文件清单 + 符号索引
    wiki-work/dep-graph.json  模块级依赖边 + 文件级边（采样，注明方法）
    wiki-work/modules.md      人类可读的模块概览（职责只引 README/build.gradle 注释）
"""
import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {
    ".git", "build", ".gradle", "node_modules", ".idea", ".cxx",
    "dist", "out", "captures", ".kotlin", "generated",
}

PACKAGE_RE = re.compile(r"^package\s+([A-Za-z_][\w.]*)")
IMPORT_RE = re.compile(r"^import\s+([A-Za-z_][\w.]*)")
ANNOT_RE = r"(?:@[A-Za-z_][\w.]*(?:\([^)\n]*\))?\s+)*"
MOD_RE = r"(?:(?:public|internal|private|protected|open|abstract|final|inline|expect|actual|external|const|operator|infix|tailrec|suspend|override|lateinit)\s+)*"
DECL_RE = re.compile(
    r"^" + ANNOT_RE + MOD_RE
    + r"((?:data|sealed|enum|annotation|value)\s+)?"
    + r"(class|interface|object|fun|val|var|typealias)"
    + r"(?:\s*<[^>\n]*>)?"
    + r"\s+(`?[A-Za-z_][A-Za-z0-9_]*`?)"
)
INCLUDE_RE = re.compile(r'include\(\s*":([^"]+)"\s*\)')
PROJECTDIR_RE = re.compile(r'project\(\s*":([^"]+)"\s*\)\.projectDir\s*=\s*file\(\s*"([^"]+)"\s*\)')

README_NAMES = ["README.md", "README.zh-CN.md", "README.zh_CN.md", "readme.md"]


def parse_settings_modules(repo: Path):
    """从 settings.gradle.kts 解析 include() 与 projectDir 映射（事实来源）。"""
    text = (repo / "settings.gradle.kts").read_text(encoding="utf-8", errors="replace")
    project_dirs = dict(PROJECTDIR_RE.findall(text))
    modules = {}
    for name in INCLUDE_RE.findall(text):
        modules[name] = project_dirs.get(name, name)
    return modules


def iter_files(repo: Path):
    """遍历仓库，跳过生成目录。返回 (relpath, is_dir_skipped_count)。"""
    skipped = 0
    for p in sorted(repo.rglob("*")):
        rel = p.relative_to(repo)
        if any(part in SKIP_DIRS for part in rel.parts):
            skipped += 1
            continue
        if p.is_file():
            yield rel.as_posix()
    return skipped


def is_binary(path: Path) -> bool:
    """含 NUL 字节即判为二进制（git 同款启发式）。"""
    try:
        with open(path, "rb") as fh:
            return b"\x00" in fh.read(8192)
    except OSError:
        return True


def extract_kt(text: str):
    """提取 package / imports / 顶层声明。返回 (package, imports, symbols)。"""
    package, imports, symbols = "", [], []
    for i, line in enumerate(text.splitlines(), start=1):
        s = line.strip()
        if not s or s.startswith("//"):
            continue
        m = PACKAGE_RE.match(line)
        if m:
            package = m.group(1)
            continue
        m = IMPORT_RE.match(line)
        if m:
            imports.append(m.group(1))
            continue
        m = DECL_RE.match(line)
        if m:
            prefix, kind, name = m.group(1), m.group(2), m.group(3).strip("`")
            full_kind = (prefix.strip() + " " + kind) if prefix else kind
            symbols.append({"name": name, "kind": full_kind, "line": i})
    return package, imports, symbols


def duty_line(mod_dir: Path):
    """职责描述：只从模块 README 或 build.gradle 注释取，找不到返回 None。"""
    for rn in README_NAMES:
        rp = mod_dir / rn
        if rp.exists():
            for line in rp.read_text(encoding="utf-8", errors="replace").splitlines():
                t = line.strip().lstrip("#").strip()
                if t and not t.startswith(("<", "!", "[")):
                    return f"（{rn}）{t}"
    for bn in ("build.gradle.kts", "build.gradle"):
        bp = mod_dir / bn
        if bp.exists():
            # 只取文件头部注释块（第一行非空非注释行之前），避免误取引文内的技术备注
            header = []
            for line in bp.read_text(encoding="utf-8", errors="replace").splitlines():
                t = line.strip()
                if not t:
                    continue
                if t.startswith("//"):
                    header.append(t[2:].strip())
                else:
                    break
            header = [c for c in header if c]
            if header and sum(len(c) for c in header) >= 8:
                return f"（{bn} 头部注释）{' '.join(header)[:200]}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    modules = parse_settings_modules(repo)
    # 模块目录按路径长度倒序，用于最长前缀匹配
    mod_items = sorted(modules.items(), key=lambda kv: -len(kv[1]))

    all_files = []
    skipped = 0
    for p in sorted(repo.rglob("*")):
        rel = p.relative_to(repo)
        if any(part in SKIP_DIRS for part in rel.parts):
            skipped += 1
            continue
        if p.is_file():
            all_files.append(rel.as_posix())

    def classify(rel: str):
        for name, d in mod_items:
            if rel == d or rel.startswith(d + "/"):
                return name
        return "unassigned"

    mod_files = {}
    for rel in all_files:
        mod_files.setdefault(classify(rel), []).append(rel)

    repo_map = {"modules": {}}
    pkg_of_module = {}   # module -> set(packages)
    sym_index = {}       # (package, name) -> file relpath
    file_imports = {}    # relpath -> [imports]
    zero_decl = 0
    kt_total = 0

    for mod in list(modules) + (["unassigned"] if "unassigned" in mod_files else []):
        files = sorted(mod_files.get(mod, []))
        symbols, loc, loc_nb, kt_files, bin_files = [], 0, 0, 0, 0
        pkgs = set()
        for rel in files:
            fp = repo / rel
            if is_binary(fp):
                bin_files += 1
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            lines = text.splitlines()
            loc += len(lines)
            loc_nb += sum(1 for l in lines if l.strip())
            if rel.endswith(".kt"):
                kt_files += 1
                kt_total += 1
                package, imports, syms = extract_kt(text)
                if package:
                    pkgs.add(package)
                file_imports[rel] = imports
                if not syms:
                    zero_decl += 1
                for s in syms:
                    s["file"] = rel
                    symbols.append(s)
                    if package:
                        sym_index[(package, s["name"])] = rel
        pkg_of_module[mod] = pkgs
        symbols.sort(key=lambda s: (s["file"], s["line"]))
        repo_map["modules"][mod] = {
            "dir": modules.get(mod, ""),
            "files": files,
            "file_count": len(files),
            "binary_files": bin_files,
            "kt_files": kt_files,
            "loc": loc,
            "loc_nonblank": loc_nb,
            "symbols": symbols,
            "symbol_count": len(symbols),
        }

    zero_ratio = zero_decl / kt_total if kt_total else 0.0
    repo_map["meta"] = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "repo": str(repo),
        "skip_dirs": sorted(SKIP_DIRS),
        "skipped_paths": skipped,
        "total_files": len(all_files),
        "kt_files": kt_total,
        "zero_decl_files": zero_decl,
        "zero_decl_ratio": round(zero_ratio, 4),
        "settings_modules": modules,
    }
    (out / "repo-map.json").write_text(
        json.dumps(repo_map, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")

    # ---- dep-graph.json ----
    def resolve_import(imp: str):
        best, best_len = None, -1
        for mod, pkgs in pkg_of_module.items():
            for pkg in pkgs:
                if imp == pkg or imp.startswith(pkg + "."):
                    # import 的是 pkg.SimpleName 形式
                    rest = imp[len(pkg):].lstrip(".")
                    if "." not in rest and len(pkg) > best_len:
                        best, best_len = (mod, pkg, rest), len(pkg)
        return best

    mod_edges = Counter()
    for rel, imports in file_imports.items():
        src_mod = classify(rel)
        for imp in imports:
            r = resolve_import(imp)
            if r and r[0] != src_mod:
                mod_edges[(src_mod, r[0])] += 1

    # 文件级边：采样——每模块按路径排序取前 40 个 kt 文件
    SAMPLE_PER_MODULE = 40
    sampled_files = []
    for mod in repo_map["modules"]:
        kts = sorted(f for f in mod_files.get(mod, []) if f.endswith(".kt"))[:SAMPLE_PER_MODULE]
        sampled_files.extend(kts)
    file_edges = []
    for rel in sampled_files:
        for imp in file_imports.get(rel, []):
            if "." not in imp:
                continue
            pkg, _, simple = imp.rpartition(".")
            target = sym_index.get((pkg, simple))
            if target and target != rel:
                file_edges.append({"from": rel, "to": target, "import": imp})
    file_edges.sort(key=lambda e: (e["from"], e["to"]))

    dep_graph = {
        "meta": {
            "module_edges_note": "边权重 = import 语句条数（package 前缀映射到模块）",
            "file_edges_sampled": True,
            "file_edges_sample_method": (
                f"每模块按路径排序取前 {SAMPLE_PER_MODULE} 个 .kt 文件，共 "
                f"{len(sampled_files)} 个文件；import 经 (package, SimpleName) 解析到定义文件"
            ),
            "file_edges_sampled_files": len(sampled_files),
        },
        "module_edges": [
            {"from": a, "to": b, "weight": w}
            for (a, b), w in sorted(mod_edges.items(), key=lambda kv: -kv[1])
        ],
        "file_edges": file_edges,
    }
    (out / "dep-graph.json").write_text(
        json.dumps(dep_graph, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")

    # ---- modules.md ----
    lines = ["# Operit 仓库模块概览", "",
             "> 由 scripts/repo_map.py 自动生成。职责描述只引用模块 README 或 build.gradle 注释，",
             '> 找不到的如实标注"未知，需人工确认"，不做推测。', ""]
    for mod in list(modules) + (["unassigned"] if "unassigned" in mod_files else []):
        m = repo_map["modules"][mod]
        lines.append(f"## {mod}")
        lines.append("")
        lines.append(f"- 路径：`{m['dir'] or '（无，散落文件）'}`")
        lines.append(f"- 文件数：{m['file_count']}（其中 .kt {m['kt_files']}，二进制 {m['binary_files']}）")
        lines.append(f"- 代码行数：{m['loc_nonblank']}（非空行）/ {m['loc']}（总行）")
        lines.append(f"- 顶层符号数：{m['symbol_count']}")
        # 主要子目录：按文件数 top 6
        sub = Counter()
        base = (m["dir"] + "/") if m["dir"] else ""
        for f in m["files"]:
            rest = f[len(base):] if base and f.startswith(base) else f
            parts = rest.split("/")
            sub[parts[0] if len(parts) > 1 else "(根)"] += 1
        top = ", ".join(f"`{k}`({v})" for k, v in sub.most_common(6))
        lines.append(f"- 主要子目录：{top if top else '—'}")
        d = duty_line(repo / m["dir"]) if m["dir"] else None
        lines.append(f"- 职责：{d if d else '未知，需人工确认'}")
        lines.append("")
    (out / "modules.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- 控制台统计 ----
    print(f"modules: {list(repo_map['modules'].keys())}")
    print(f"total_files={len(all_files)} kt_files={kt_total} "
          f"symbols={sum(m['symbol_count'] for m in repo_map['modules'].values())}")
    print(f"zero_decl_files={zero_decl} ratio={zero_ratio:.2%}")
    print(f"module_edges={len(dep_graph['module_edges'])} "
          f"file_edges(sampled)={len(file_edges)}")


if __name__ == "__main__":
    main()
