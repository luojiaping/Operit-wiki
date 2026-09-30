#!/usr/bin/env bash
# 重新组装并发布评审网站到 gh-pages 分支。
# 每次新条目生成 / 评审状态变化后运行一次即可。
# 用法: bash scripts/deploy_site.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 scripts/build_queue.py --root .

WORK=$(mktemp -d)
git worktree add -q "$WORK" gh-pages
rm -rf "$WORK"/*
cp -r site/* "$WORK"/
mkdir -p "$WORK/data"
cp review-queue.json "$WORK/data/"
[ -d review ] && cp -r review "$WORK/data/" || true
[ -d wiki ] && cp -r wiki "$WORK/data/" || true

cd "$WORK"
git add -A
git -c user.name=luojiaping -c user.email=luojiaping@users.noreply.github.com \
  commit -qm "site: redeploy $(date -u +%Y-%m-%d_%H:%M_UTC)" || true
git push -q origin gh-pages

cd "$ROOT"
git worktree remove --force "$WORK"
echo "deployed -> https://luojiaping.github.io/Operit-wiki/"
