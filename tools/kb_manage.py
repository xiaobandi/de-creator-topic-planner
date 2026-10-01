#!/usr/bin/env python3
"""轻量知识库 CRUD（零依赖，JSON 落盘）。

为「选题知识库」「FAQ 库」「人设语气库」「商品知识库」提供统一的最小操作：
add / update / tag / list / search / export，保证资产以文本形式可版本化。

v2 修订（2026-09）
------------------
v1 的 docstring 承诺有 `tag` 子命令，但 argparse 里**没有实现**，照文档敲会报
「invalid choice: 'tag'」；同类的「标签分隔符」问题：v1 只按半角逗号切分，
用户很自然写「出海，工具」（全角逗号）会被当成一个标签。
v2 起：补上 `tag` 子命令（给已有条目追加标签，不覆盖原标签），并把标签
分隔符统一为半角/全角逗号、分号、顿号均可。

用法:
    python3 kb_manage.py --db topic_kb.json add --title "AI 出海踩坑" --tags 出海,工具 --weight 3
    python3 kb_manage.py --db topic_kb.json tag --title "AI 出海踩坑" --tags 复盘
    python3 kb_manage.py --db topic_kb.json search --query 出海
    python3 kb_manage.py --db topic_kb.json list --top 5
    python3 kb_manage.py --db topic_kb.json export --out topic_kb.md
    python3 kb_manage.py --selftest
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

_TAG_SPLIT = re.compile(r"[,，;；、\s]+")


def split_tags(raw: str | None) -> list[str]:
    """标签分隔符统一：半角/全角逗号、分号、顿号、空白都算分隔符。"""
    if not raw:
        return []
    return [t.strip() for t in _TAG_SPLIT.split(raw) if t.strip()]


def load(db: Path) -> dict:
    if db.exists():
        return json.loads(db.read_text(encoding="utf-8"))
    return {"meta": {"created": date.today().isoformat()}, "items": []}


def save(db: Path, data: dict) -> None:
    data["meta"]["updated"] = date.today().isoformat()
    db.parent.mkdir(parents=True, exist_ok=True)
    db.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_add(db: Path, a) -> int:
    data = load(db)
    if any(i["title"] == a.title for i in data["items"]):
        print(f"已存在同名条目：{a.title}（用 update 修改）", file=sys.stderr)
        return 1
    data["items"].append({
        "title": a.title, "tags": split_tags(a.tags),
        "weight": a.weight, "note": a.note or "",
        "created": date.today().isoformat(), "used_count": 0,
    })
    save(db, data)
    print(f"已写入 {a.title}（当前 {len(data['items'])} 条）")
    return 0


def cmd_tag(db: Path, a) -> int:
    """给已有条目**追加**标签（不覆盖原有标签）。"""
    data = load(db)
    add = split_tags(a.tags)
    if not add:
        print("错误：--tags 为空", file=sys.stderr)
        return 2
    for i in data["items"]:
        if i["title"] == a.title:
            cur = list(i.get("tags", []))
            added = [t for t in add if t not in cur]
            i["tags"] = cur + added
            save(db, data)
            print(f"已给 {a.title} 追加标签 {'/'.join(added) or '（无新增）'}"
                  f"，当前标签 {'/'.join(i['tags'])}")
            return 0
    print(f"未找到 {a.title}", file=sys.stderr)
    return 1


def cmd_update(db: Path, a) -> int:
    data = load(db)
    for i in data["items"]:
        if i["title"] == a.title:
            if a.weight is not None:
                i["weight"] = a.weight
            if a.tags:
                i["tags"] = split_tags(a.tags)
            if a.used:
                i["used_count"] = i.get("used_count", 0) + 1
            if a.note:
                i["note"] = a.note
            save(db, data)
            print(f"已更新 {a.title}")
            return 0
    print(f"未找到 {a.title}", file=sys.stderr)
    return 1


def cmd_list(db: Path, a) -> int:
    data = load(db)
    items = sorted(data["items"], key=lambda x: (-(x.get("weight") or 0), x["title"]))
    if a.tag:
        items = [i for i in items if a.tag in i.get("tags", [])]
    if a.top:
        items = items[: a.top]
    for i in items:
        tags = ",".join(i.get("tags", []))
        print(f"[权重{i.get('weight',0)}] {i['title']}  #{tags}  用过{i.get('used_count',0)}次")
    print(f"\n共 {len(items)} / {len(data['items'])} 条")
    return 0


def cmd_search(db: Path, a) -> int:
    data = load(db)
    q = a.query
    hit = [i for i in data["items"]
           if q in i["title"] or q in (i.get("note") or "") or any(q in t for t in i.get("tags", []))]
    for i in hit:
        print(f"- {i['title']}（权重{i.get('weight',0)}）{i.get('note','')}")
    print(f"\n命中 {len(hit)} 条")
    return 0 if hit else 1


def cmd_export(db: Path, a) -> int:
    data = load(db)
    lines = ["# 知识库导出", f"\n> {date.today().isoformat()}　共 {len(data['items'])} 条\n"]
    for i in sorted(data["items"], key=lambda x: -(x.get("weight") or 0)):
        lines.append(f"- **{i['title']}**　权重 {i.get('weight',0)}　标签 {'/'.join(i.get('tags',[]))}")
        if i.get("note"):
            lines.append(f"  - {i['note']}")
    text = "\n".join(lines)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"已导出 {a.out}")
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="轻量知识库 CRUD")
    ap.add_argument("--db", default="kb.json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add"); p.add_argument("--title", required=True)
    p.add_argument("--tags", default=""); p.add_argument("--weight", type=int, default=1)
    p.add_argument("--note", default=""); p.set_defaults(fn=cmd_add)

    p = sub.add_parser("update"); p.add_argument("--title", required=True)
    p.add_argument("--weight", type=int); p.add_argument("--tags")
    p.add_argument("--used", action="store_true"); p.add_argument("--note")
    p.set_defaults(fn=cmd_update)

    p = sub.add_parser("tag"); p.add_argument("--title", required=True)
    p.add_argument("--tags", required=True); p.set_defaults(fn=cmd_tag)

    p = sub.add_parser("list"); p.add_argument("--tag"); p.add_argument("--top", type=int)
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("search"); p.add_argument("--query", required=True); p.set_defaults(fn=cmd_search)
    p = sub.add_parser("export"); p.add_argument("--out"); p.set_defaults(fn=cmd_export)
    return ap


def _selftest() -> int:
    """内嵌回归自测：核心断言是「docstring 承诺的子命令真的存在」「标签分隔符容错」。"""
    import tempfile
    checks: list[tuple[str, bool, str]] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))

    ap = build_parser()
    sub_actions = [a for a in ap._actions if isinstance(a, argparse._SubParsersAction)]
    names = set(sub_actions[0].choices) if sub_actions else set()

    # 1) docstring 里承诺的子命令必须真的存在（v1 的 `tag` 就是只在文档里）
    doc = (__doc__ or "")
    head = doc.split("用法:")[0]
    m = re.search(r"操作：\s*([a-z/ \u4e00-\u9fff]+)", head)
    if m:
        for cmd in [x.strip() for x in m.group(1).split("/") if x.strip()]:
            ck(f"docstring 承诺的子命令 {cmd} 已实现", cmd in names, f"实际 {sorted(names)}")
    for cmd in ("add", "update", "tag", "list", "search", "export"):
        ck(f"子命令 {cmd} 存在", cmd in names)

    # 2) 标签分隔符容错（全角逗号 / 顿号 / 分号 / 空格）
    ck("半角逗号", split_tags("a,b") == ["a", "b"])
    ck("全角逗号", split_tags("出海，工具") == ["出海", "工具"])
    ck("顿号", split_tags("出海、工具") == ["出海", "工具"])
    ck("分号", split_tags("出海;工具") == ["出海", "工具"])
    ck("空值", split_tags("") == [] and split_tags(None) == [])

    # 3) tag 是追加而不是覆盖
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "kb.json"

        class A:  # 简易命名空间
            pass
        a = A(); a.title = "T"; a.tags = "出海，工具"; a.weight = 3; a.note = ""
        ck("add 返回 0", cmd_add(db, a) == 0)
        data = json.loads(db.read_text(encoding="utf-8"))
        ck("add 后标签正确", data["items"][0]["tags"] == ["出海", "工具"],
           f"实际 {data['items'][0]['tags']}")
        ck("add 拒绝重复标题", cmd_add(db, a) == 1)

        b = A(); b.title = "T"; b.tags = "复盘,工具"
        ck("tag 返回 0", cmd_tag(db, b) == 0)
        data = json.loads(db.read_text(encoding="utf-8"))
        ck("tag 追加且不重复", data["items"][0]["tags"] == ["出海", "工具", "复盘"],
           f"实际 {data['items'][0]['tags']}")

        c = A(); c.title = "不存在"; c.tags = "x"
        ck("tag 未命中返回 1", cmd_tag(db, c) == 1)

    fails = [(n, d) for n, ok, d in checks if not ok]
    for n, ok, d in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {n}" + (f" —— {d}" if not ok and d else ""))
    print(f"kb_manage 自测：{len(checks) - len(fails)}/{len(checks)} 通过")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return _selftest()

    args = build_parser().parse_args()
    return args.fn(Path(args.db).expanduser(), args)


if __name__ == "__main__":
    sys.exit(main())
