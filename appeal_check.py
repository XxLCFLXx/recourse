#!/usr/bin/env python3
"""
appeal_check.py — 判决记录的最小校验器 (v0.1)

配套《可上诉性 v0.1》。它只做一件事：拒绝那些"看起来有记录、
实际上无法上诉"的判决。

用法:
    python appeal_check.py              # 跑内置自测
    python appeal_check.py rec.json     # 校验一个文件（或 JSON 数组）
"""

import json
import sys
from datetime import datetime

REQUIRED = [
    "id", "at", "actor", "principal", "scope", "verdict", "grounds",
    "counterfactual", "appeal_to", "appeal_until", "revoke", "status",
]

STATUS = {"open", "under_review", "upheld", "overturned", "final"}

# 上诉对象必须是一个"可以被找到并追究"的东西。
# 这些词听起来像, 但它们不是地址。
CONCEPTS = {
    "使命", "历史", "大局", "人民", "社会", "公共利益", "用户",
    "the mission", "history", "society", "public interest",
    "stakeholders", "the team", "system", "algorithm", "model",
    "n/a", "none", "tbd",
}


def _addr_ok(v: str) -> bool:
    """一个可用的地址: 含 @ 或 /, 且不是概念词。"""
    if not isinstance(v, str) or not v.strip():
        return False
    if v.strip().lower() in CONCEPTS:
        return False
    return ("@" in v) or ("/" in v)


def check(rec: dict) -> list[str]:
    errs: list[str] = []

    # 1. 必填
    for f in REQUIRED:
        if f not in rec or rec[f] in (None, "", [], {}):
            errs.append(f"E_MISSING: 缺字段 '{f}'")

    if errs:
        return errs  # 结构不全, 后面的检查没有意义

    # 2. I2 可归因 —— 责任人和上诉对象必须是地址, 不是概念
    if not _addr_ok(rec["principal"]):
        errs.append(
            f"E_CONCEPT: principal='{rec['principal']}' 不是可追究的地址 "
            f"(需要具体的人, 不是角色/概念)"
        )
    if not _addr_ok(rec["appeal_to"]):
        errs.append(
            f"E_CONCEPT: appeal_to='{rec['appeal_to']}' 不是可追究的地址 "
            f"(上诉对象不能是概念)"
        )

    # 3. I1 可中断 —— 必须有撤销句柄, 且 overturned 必须能落地
    if not rec["revoke"]:
        errs.append("E_UNREVOCABLE: 没有 revoke 句柄, I1/I3 无法满足")
    if rec["status"] == "overturned" and not rec["revoke"]:
        errs.append("E_DEAD_END: 已改判但无撤销句柄, 状态是假的")

    # 4. 状态合法
    if rec["status"] not in STATUS:
        errs.append(f"E_STATUS: 未知状态 '{rec['status']}'")

    # 5. 理由必须存在, 且有来源
    grounds = rec["grounds"]
    if not isinstance(grounds, list) or not grounds:
        errs.append("E_NO_GROUNDS: grounds 为空")
    else:
        for i, g in enumerate(grounds):
            if not isinstance(g, dict) or not g.get("claim"):
                errs.append(f"E_GROUND: grounds[{i}] 缺 claim")
            elif not g.get("source"):
                errs.append(f"E_GROUND: grounds[{i}] 缺 source (无法追溯)")

        # 6. 全是"模型认为"的, 不算可检验来源
        if all(str(g.get("source", "")).startswith("model:") for g in grounds):
            errs.append(
                "W_OPAQUE: 全部理由来源都是模型自身('model:'), "
                "没有一条外部可检验的依据"
            )

    # 7. 上诉窗口必须落在未来
    try:
        at = datetime.fromisoformat(rec["at"])
        until = datetime.fromisoformat(rec["appeal_until"])
        if until <= at:
            errs.append("E_WINDOW: appeal_until 不晚于判决时间, 窗口是关的")
    except (ValueError, TypeError) as e:
        errs.append(f"E_TIME: 时间格式无法解析 ({e})")

    return errs


# ---------------------------------------------------------------- self-test

GOOD = {
    "id": "j.2026-11-05.0041",
    "at": "2026-11-05T14:02:11+08:00",
    "actor": "agent.pricing.v3",
    "principal": "zhang.wei@example.com",
    "scope": ["order:88213", "order:88214"],
    "verdict": "reject",
    "grounds": [
        {"claim": "risk_score >= 0.72", "value": 0.74, "source": "model:pricing.v3"},
        {"claim": "policy:R-114 applies", "source": "policy/rules.yaml#R-114"},
    ],
    "counterfactual": "risk_score < 0.72",
    "appeal_to": "ops-lead@example.com",
    "appeal_until": "2026-11-12T00:00:00+08:00",
    "revoke": "POST /verdicts/j.2026-11-05.0041/revoke",
    "effect_ref": "txn:9f2a...",
    "status": "open",
}

BAD = [
    (
        "上诉对象是个概念",
        {**GOOD, "appeal_to": "公共利益"},
    ),
    (
        "责任人是个 agent",
        {**GOOD, "principal": "agent.pricing.v3"},
    ),
    (
        "没有撤销句柄",
        {**GOOD, "revoke": ""},
    ),
    (
        "理由是事后编的, 全靠模型自己",
        {**GOOD, "grounds": [{"claim": "looks risky", "source": "model:pricing.v3"}]},
    ),
    (
        "窗口是关的",
        {**GOOD, "appeal_until": "2026-11-05T13:00:00+08:00"},
    ),
    (
        "缺字段",
        {k: v for k, v in GOOD.items() if k not in ("principal", "appeal_to")},
    ),
]


def _run(label: str, rec: dict, want: bool) -> bool:
    errs = check(rec)
    ok = not errs
    mark = "PASS" if ok == want else "FAIL"
    print(f"[{mark}] {label}: {'通过' if ok else '不通过'}")
    for e in errs:
        print(f"        {e}")
    return ok == want


def main() -> int:
    if len(sys.argv) > 1:
        data = json.load(open(sys.argv[1], encoding="utf-8"))
        records = data if isinstance(data, list) else [data]
        bad = 0
        for r in records:
            errs = check(r)
            print(f"{r.get('id', '<no id>')}: {'OK' if not errs else 'REJECT'}")
            for e in errs:
                print(f"    {e}")
            bad += bool(errs)
        return 1 if bad else 0

    print("== 可上诉性 v0.1 / 自测 ==\n")
    results = [_run("合规记录", GOOD, True)]
    for label, rec in BAD:
        results.append(_run(label, rec, False))

    print(f"\n{sum(results)}/{len(results)} 符合预期")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
