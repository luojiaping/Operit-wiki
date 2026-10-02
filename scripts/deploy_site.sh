#!/usr/bin/env bash
# 重新组装并发布评审网站到 gh-pages 分支。
# 每次新条目生成 / 评审状态变化后运行一次即可。
# 用法: bash scripts/deploy_site.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 scripts/build_queue.py --root .

# Wiki 预览数据 + 知识图谱 + 覆盖进度（失败不阻断部署，保留上次产物）
python3 scripts/build_wiki_data.py || echo "WARN: build_wiki_data.py failed, keep old pages.json"
python3 scripts/build_graph.py || echo "WARN: build_graph.py failed, keep old graph"
python3 scripts/build_coverage.py --root . || echo "WARN: build_coverage.py failed, keep old coverage.json"
python3 scripts/build_quality.py --root . || echo "WARN: build_quality.py failed, keep old quality.json"

WORK=$(mktemp -d)
git worktree add -q "$WORK" gh-pages
rm -rf "$WORK"/*
cp -r site/* "$WORK"/
# 静态资源加版本号：根治浏览器/CDN 缓存导致的老版本残留（只改发布副本，不动源码）
V=$(git -C "$ROOT" rev-parse --short HEAD)
grep -rl 'style\.css' "$WORK" --include="*.html" | xargs -r sed -E -i "s|style\.css(\?v=[^\"' ]*)?|style.css?v=$V|g"
# .nojekyll：关闭 Jekyll 处理，否则 .md 文件会被转成 .html 导致原路径 404
touch "$WORK/.nojekyll"
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
