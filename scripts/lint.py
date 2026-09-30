#!/usr/bin/env python3
"""Operit-wiki 机器 lint：阶段 3 全量检查，零 LLM 成本。

任一硬失败即打回阶段 2，不许进入评审。

用法:
    python3 scripts/lint.py --src /path/to/Operit [--wiki wiki] [--review review/batch-01]

检查项:
  1. frontmatter 齐全 (title/module/sources/date)
  2. 所有 file:line 引用真实存在
  3. 引用行 ±5 行内出现断言中的符号名
  4. 无死链（相对链接可解析）
  5. 每页有"来源"小节且非空
  6. 禁用模糊词扫描（可能/大概/似乎/应该/也许）
"""
import argparse
import json
import re
import sys
from pathlib import Path

REF_RE = re.compile(r'`([A-Za-z0-9_\-./]+\.(?:kt|java|xml|gradle|kts|md|py|ts|js)):(\d+)`')
LINK_RE = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
BANNED = ["可能", "大概", "似乎", "应该", "也许", " presumably"]
FRONTMATTER_KEYS = ["title", "module", "sources", "date"]


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


def check_file(path: Path, src: Path, wiki_root: Path, errors, warnings):
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)

    for k in FRONTMATTER_KEYS:
        if k not in fm:
            errors.append(f"{path.name}: frontmatter 缺少 `{k}`")

    # 引用检查
    for m in REF_RE.finditer(text):
        rel, lineno = m.group(1), int(m.group(2))
        target = src / rel
        if not target.exists():
            errors.append(f"{path.name}: 引用文件不存在 `{rel}:{lineno}`")
            continue
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        if lineno < 1 or lineno > len(lines):
            errors.append(f"{path.name}: 引用行号越界 `{rel}:{lineno}`（共 {len(lines)} 行）")
            continue
        # 符号名检查：断言所在句子里的反引号符号应在 ±5 行窗口出现
        line_start = max(0, text.rfind("\n", 0, m.start()) + 1)
        line_end = text.find("\n", m.end())
        claim_line = text[line_start:line_end if line_end > 0 else len(text)]
        symbols = re.findall(r'`([A-Za-z_][A-Za-z0-9_]*)`', claim_line)
        symbols = [s for s in symbols if not s.endswith((".kt", ".java", ".xml"))]
        window = "\n".join(lines[max(0, lineno - 6):lineno + 5])
        for sym in symbols:
            if sym not in window:
                warnings.append(
                    f"{path.name}: `{rel}:{lineno}` ±5 行未见符号 `{sym}`（断言：{claim_line.strip()[:60]}…）"
                )

    # 死链检查（只查相对 .md 链接）
    for m in LINK_RE.finditer(text):
        url = m.group(1)
        if url.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = (path.parent / url.split("#")[0]).resolve()
        if not target.exists():
            errors.append(f"{path.name}: 死链 `{url}`")

    # 来源小节
    if not re.search(r"^#{1,3}\s*(来源|参考|引用)", text, re.M):
        errors.append(f'{path.name}: 缺少"来源"小节')

    # 禁用词
    for w in BANNED:
        if w in text:
            warnings.append(f'{path.name}: 含模糊词"{w}"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Operit 源码仓库根目录")
    ap.add_argument("--dir", required=True, help="待检查的条目目录（如 review/batch-01）")
    ap.add_argument("--out", default="", help="lint 报告输出路径（.md）")
    args = ap.parse_args()

    src = Path(args.src)
    target_dir = Path(args.dir)
    errors, warnings = [], []
    files = sorted(target_dir.glob("*.md"))
    if not files:
        print("no md files found", file=sys.stderr)
        sys.exit(2)

    for f in files:
        check_file(f, src, target_dir, errors, warnings)

    report = ["# Lint 报告", ""]
    report.append(f"- 检查文件：{len(files)}")
    report.append(f"- 硬失败：{len(errors)}")
    report.append(f"- 警告：{len(warnings)}")
    report.append("")
    if errors:
        report.append("## 错误（必须修复）")
        report += [f"- {e}" for e in errors]
        report.append("")
    if warnings:
        report.append("## 警告（建议处理）")
        report += [f"- {w}" for w in warnings]

    report_text = "\n".join(report) + "\n"
    if args.out:
        Path(args.out).write_text(report_text, encoding="utf-8")
    print(report_text)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
