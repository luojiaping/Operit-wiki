#!/usr/bin/env python3
"""扫描 Operit-wiki 评审 Issues 中 luojiaping 的新评论，分类为待处理反馈。

只认 login == "luojiaping" 的评论；自动跳过：
  - 审批类（通过/批准/LGTM/同意，含标点变体）-> 由 watch_reviews.py 处理
  - 机器人交付模板（经 owner token 发出，看起来像 luojiaping，实为流水线留言）
输出 JSON: [{issue, comment_id, created_at, body, kind}]
kind: approval | delivery | feedback
水位线: tracking/feedback-watermark.json {last_seen: {issue: comment_id}}
"""
import json, re, subprocess, sys, os

REPO = "luojiaping/Operit-wiki"
WS = os.path.expanduser("~/workspace/Operit-wiki-skeleton")
WM = os.path.join(WS, "tracking", "feedback-watermark.json")

APPROVAL_RE = re.compile(r"^(通过|批准|LGTM|同意)[。．.\s!！]*$", re.IGNORECASE)
APPROVAL_RES = [re.compile(r"已确认[「\"']?通过")]
DELIVERY_RES = [
    re.compile(r"评审页已更新"),
    re.compile(r"评审页已就绪"),
    re.compile(r"交付[：:]"),
    re.compile(r"交付更新"),
    re.compile(r"已上评审站"),
    re.compile(r"旧版已删除回炉"),
    re.compile(r"v3 重写版已完成"),
    re.compile(r"评审材料已上评审站"),
    re.compile(r"大纲已更新"),
    re.compile(r"✅ 收到"),
    re.compile(r"Day \d+ / batch-\d+"),
]

def gh(*args):
    p = subprocess.run(["gh"] + list(args), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[:300])
    return p.stdout

def main():
    q = json.load(open(os.path.join(WS, "review-queue.json")))
    issues = sorted({e["issue"] for e in q["entries"] if e.get("issue")})
    wm = {}
    if os.path.exists(WM):
        wm = json.load(open(WM)).get("last_seen", {})
    out = []
    new_wm = dict(wm)
    for issue in issues:
        try:
            raw = gh("issue", "view", str(issue), "-R", REPO, "--json",
                     "comments", "-q",
                     ".comments[] | [.url, .author.login, .createdAt, .body] | @tsv")
        except RuntimeError as e:
            print(f"warn: issue {issue}: {e}", file=sys.stderr)
            continue
        seen_ts = wm.get(str(issue), "")
        max_ts = seen_ts
        for line in raw.splitlines():
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            url, login, created, body = parts[0], parts[1], parts[2], "\t".join(parts[3:])
            if login != "luojiaping":
                continue
            if created <= seen_ts:
                continue
            max_ts = max(max_ts, created)
            m = re.search(r"#issuecomment-(\d+)", url or "")
            cid = int(m.group(1)) if m else 0
            b = body.strip()
            if APPROVAL_RE.match(b) or any(r.search(b) for r in APPROVAL_RES):
                kind = "approval"
            elif any(r.search(b) for r in DELIVERY_RES):
                kind = "delivery"
            else:
                kind = "feedback"
            if kind == "feedback":
                out.append({"issue": issue, "comment_id": cid,
                            "created_at": created, "body": b})
        if max_ts != seen_ts:
            new_wm[str(issue)] = max_ts
    json.dump({"last_seen": new_wm}, open(WM, "w"), ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
