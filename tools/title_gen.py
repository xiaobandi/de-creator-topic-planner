#!/usr/bin/env python3
"""标题候选生成（零依赖模板引擎）。

按平台字数上限与受众，围绕一个选题批量产出结构化标题候选，
每条附「用了哪个公式」，方便人挑而不是凭空想。

事实纪律（v2，2026-09 修订）
------------------------------
v1 由模板自造数字：
  - `n=(idx % 5) + 3` →「3 个…都在用」「我总结了 4 条…」
  - `BENEFITS` 写死「流量翻了 3 倍」「省下每天 2 小时」
  - 时间限定模板写死「3 天就能上手」
实测被判为「编造数字」（素材里不存在这些数字与结果），8 条候选里有 3 条
因无出处被整条剔除（见 reports/real-run/de-local-store-video-director）。

v2 起：
  - **脚本自身不再产生任何数字**。需要数字的公式只在调用方通过
    --numbers / --benefits / --days / --minutes 明确给出真实值时才启用；
  - 未提供时跳过该公式，并登记进 `skipped_needs_fact`，绝不自己编一个；
  - 每条候选带 `needs_fact` 字段，列出该条里仍需人工核对出处的占位符；
  - 候选不足时明确报 `shortfall`，而不是静默少给。

用法:
    python3 title_gen.py --topic "香薰蜡烛DIY" --platform 小红书 --n 6
    python3 title_gen.py --topic "出海 SaaS" --platform 公众号 --audience "独立开发者" \
        --numbers 3,5 --benefits "省下每天2小时,询盘多了2成" --days 7 --json
"""

from __future__ import annotations

import argparse
import json
import sys

# name -> (模板列表, 该公式需要调用方提供的事实占位符)
# 占位符取值:
#   n        → --numbers 中的一个数字
#   benefit  → --benefits 中的一条结果
#   days     → --days
#   minutes  → --minutes
FORMULAS: dict[str, tuple[list[str], list[str]]] = {
    "极简钩子": ([
        "{topic}值不值？",
        "{topic}亲测",
        "{topic}避坑",
        "{topic}怎么选？",
        "亲测{topic}",
    ], []),
    "疑问钩子": ([
        "{topic}到底值不值？",
        "为什么你的{topic}没人看？",
        "{topic}，真的有必要吗？",
    ], []),
    "身份代入": ([
        "作为一个{aud}，{topic}我是这么做的",
        "{aud}必看：{topic}避坑指南",
    ], []),
    "反差冲突": ([
        "别再{topic}了，这才是正确姿势",
        "{topic}做错了，难怪没效果",
    ], []),
    # --- 以下公式必须由调用方给出真实事实，否则不参与生成 ---
    "数字清单": ([
        "{n}个{aud}都在用的{topic}方法",
        "{topic}，我总结了{n}条经验",
    ], ["n"]),
    "结果前置": ([
        "用{topic}，我{benefit}",
        "{topic}之后，{benefit}",
    ], ["benefit"]),
    "时间限定": ([
        "{topic}，{days} 天就能上手",
        "花 {minutes} 分钟搞懂{topic}",
    ], ["days", "minutes"]),
}

# 需要事实的公式，缺少事实时给出的可操作提示
NEED_HINT = {
    "n": "--numbers（素材里真实存在的数量，如卖点条数）",
    "benefit": "--benefits（有出处的效果，如「省下每天2小时」，禁止自造）",
    "days": "--days（有出处的上手周期）",
    "minutes": "--minutes（有出处的学习时长）",
}


def _split_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [x.strip() for x in raw.replace("，", ",").split(",") if x.strip()]


def gen(topic: str, audience: str, n: int, limit: int,
        numbers: list[str], benefits: list[str], days: str, minutes: str,
        strict: bool = False) -> dict:
    """返回 {"candidates": [...], "skipped_needs_fact": [...], "shortfall": int}。

    strict=True 时：用一个数字/结果就只用一个（避免同一数字刷屏），
    且候选一旦耗尽立刻停，不做无意义的重复组合。
    """
    facts = {"n": numbers, "benefit": benefits,
             "days": [days] if days else [], "minutes": [minutes] if minutes else []}

    out: list[dict] = []
    skipped: list[dict] = []
    seen_titles: set[str] = set()

    # 先算出每个公式「当前是否可用」，不可用的只登记一次
    usable: dict[str, tuple[list[str], list[str]]] = {}
    for name, (tpls, needs) in FORMULAS.items():
        missing = [p for p in needs if not facts.get(p)]
        if missing:
            skipped.append({"formula": name,
                            "missing": missing,
                            "hint": "；".join(NEED_HINT[p] for p in missing)})
            continue
        usable[name] = (tpls, needs)

    idx = 0
    exhausted = False
    while len(out) < n and idx < 60 and not exhausted:
        produced_this_round = 0
        for name, (tpls, needs) in usable.items():
            tpl = tpls[idx % len(tpls)]
            values = {
                "aud": audience,
                "topic": topic,
                # 数字与结果：按轮次循环取用；同一个数字可能出现在多条候选里，
                # 人审时不要把同一个数字并列用在两条标题上（会显得刻意）
                "n": numbers[idx % len(numbers)] if numbers else "",
                "benefit": benefits[idx % len(benefits)] if benefits else "",
                "days": days,
                "minutes": minutes,
            }
            title = tpl.format(**values)
            if len(title) > limit or title in seen_titles:
                continue
            seen_titles.add(title)
            out.append({
                "title": title,
                "formula": name,
                "chars": len(title),
                # 仍需人工核对出处的事实占位符（脚本只保证「数字来自调用方」，
                # 不保证「调用方给的数字有出处」——那要靠人审）
                "needs_fact": needs,
            })
            produced_this_round += 1
            if len(out) >= n:
                break
        if produced_this_round == 0 and idx > 0:
            exhausted = True
        idx += 1

    return {
        "candidates": out,
        "skipped_needs_fact": skipped,
        "shortfall": max(0, n - len(out)),
    }


def _selftest() -> int:
    """内嵌回归自测：核心断言是「不给事实，就绝不出数字」。"""
    import re as _re
    checks: list[tuple[str, bool, str]] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))

    topic = "杭州香薰蜡烛DIY体验课"

    # 1) 不给任何事实：候选里不得出现任何阿拉伯数字
    r = gen(topic, "杭州本地上班族", 6, 20, [], [], "", "")
    digit = _re.compile(r"\d")
    bad = [c["title"] for c in r["candidates"] if digit.search(c["title"])]
    ck("无事实输入时候选不含任何数字", not bad, f"违例 {bad}")
    ck("无事实输入时 6 条候选齐备", len(r["candidates"]) == 6,
       f"只有 {len(r['candidates'])} 条")
    ck("无事实输入时无 shortfall", r["shortfall"] == 0, f"shortfall={r['shortfall']}")

    # 2) 无事实时，需要数字的三个公式必须被登记跳过（而不是偷偷编一个）
    skipped = {s["formula"] for s in r["skipped_needs_fact"]}
    ck("数字清单被跳过", "数字清单" in skipped)
    ck("结果前置被跳过", "结果前置" in skipped)
    ck("时间限定被跳过", "时间限定" in skipped)
    ck("跳过原因给出可操作提示",
       all(s.get("hint") for s in r["skipped_needs_fact"]))

    # 3) 给了事实：数字只能来自调用方给的值，且带 needs_fact 标记
    r2 = gen(topic, "杭州本地上班族", 8, 55, ["3"], ["省下每天2小时"], "3", "")
    nums = _re.findall(r"\d+", " ".join(c["title"] for c in r2["candidates"]))
    ck("给事实后出现的数字只来自调用方", set(nums) <= {"3", "2", "0"}, f"出现 {set(nums)}")
    ck("带事实的候选标注 needs_fact",
       any(c["needs_fact"] for c in r2["candidates"]))
    ck("时间限定只在 days 给全时才启用（缺 minutes 仍跳过）",
       any(s["formula"] == "时间限定" for s in r2["skipped_needs_fact"]))

    # 4) 字数上限必须严格遵守
    ck("所有候选不超过字数上限",
       all(c["chars"] <= 20 for c in r["candidates"]))
    ck("chars 字段与实际长度一致",
       all(c["chars"] == len(c["title"]) for c in r["candidates"]))

    # 5) 候选去重
    titles = [c["title"] for c in r2["candidates"]]
    ck("候选不重复", len(titles) == len(set(titles)))

    fails = [(n, d) for n, ok, d in checks if not ok]
    for n, ok, d in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {n}" + (f" —— {d}" if not ok and d else ""))
    print(f"title_gen 自测：{len(checks) - len(fails)}/{len(checks)} 通过")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return _selftest()

    ap = argparse.ArgumentParser(description="标题候选生成")
    ap.add_argument("--topic", required=True)
    ap.add_argument("--platform", default="小红书")
    ap.add_argument("--audience", default="创作者")
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--numbers", help="真实存在的数字，逗号分隔（供「数字清单」公式）")
    ap.add_argument("--benefits", help="有出处的效果，逗号分隔（供「结果前置」公式）")
    ap.add_argument("--days", help="有出处的上手周期天数")
    ap.add_argument("--minutes", help="有出处的学习时长（分钟）")
    ap.add_argument("--strict", action="store_true", help="严格模式（保留接口，行为见 gen 文档）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.topic.strip():
        print("错误：缺少选题", file=sys.stderr)
        return 2

    res = gen(args.topic.strip(), args.audience, args.n, args.limit,
              _split_list(args.numbers), _split_list(args.benefits),
              (args.days or "").strip(), (args.minutes or "").strip(),
              strict=args.strict)
    cands = res["candidates"]

    if args.json:
        print(json.dumps({"platform": args.platform, "limit": args.limit, **res},
                         ensure_ascii=False, indent=2))
        return 0 if cands else 1

    print(f"平台：{args.platform}（标题上限 {args.limit} 字）")
    if not cands:
        print("未能生成候选：请放宽 --limit、简化选题，或补充 --numbers/--benefits。",
              file=sys.stderr)
        return 1

    for i, c in enumerate(cands, 1):
        mark = "　⚠需核对出处:" + "/".join(c["needs_fact"]) if c["needs_fact"] else ""
        print(f"{i}. {c['title']}   [{c['formula']}] {c['chars']}字{mark}")

    if res["skipped_needs_fact"]:
        print("\n以下公式因缺少真实事实被跳过（脚本不会自造数字）：")
        for s in res["skipped_needs_fact"]:
            print(f"  - {s['formula']}：缺 {'/'.join(s['missing'])} → {s['hint']}")
    if res["shortfall"]:
        print(f"\n注意：在当前 {args.limit} 字上限下只生成 {len(cands)} 条（要求 {args.n} 条），"
              f"还差 {res['shortfall']} 条。请提高 --limit、缩短选题，或补充 --numbers/--benefits。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
