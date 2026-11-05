#!/usr/bin/env python3
"""
run_targets.py — 对三个第三方系统跑「声明层」测试。

重要：这三个系统都不属于我，我也没有部署权限。
所以本脚本只跑 DECLARED 那一层的检查，实测与签字一律标为「未核实」。

它测的不是系统本身，是系统的公开文档在说什么。
如果文档里找不到「一个具体的人」，那本身就是结论。
"""

import sys
import conformance as C

TARGETS = [
    {
        "system": "microsoft/agent-governance-toolkit",
        "endpoints": {
            "interrupt": "Agent SRE: kill switch",
            "interrupt_not_owner_only": False,     # 文档未声明
            "revoke": "",
        },
        "principal": {"name": "", "address": "", "consent_ref": ""},
        "appeal": {
            "appeal_to": "security-team",           # 策略里写的是 approvers: ["security-team"]
            "final_authority": "",
            "window_seconds": 0,
            "independent": False,
        },
        "agents": [{"id": "agentmesh-agent", "shares_credentials_with": []}],
        "evaluator": {
            "id": "agent-control-spec (deterministic Rust core)",
            "distinct_from_actor": True,
        },
        "verdict_sample": {
            "id": "decision-bom.example",
            "at": "x", "actor": "agentmesh-agent", "principal": "",
            "scope": ["tool:send_email"], "verdict": "allow",
            "grounds": [], "counterfactual": "",
            "appeal_to": "", "appeal_until": "", "revoke": "",
            "status": "open",
        },
        "attestations": {},
    },
    {
        "system": "ThirdKeyAI/Symbiont",
        "endpoints": {
            "interrupt": "",
            "interrupt_not_owner_only": False,
            "revoke": "",
        },
        "principal": {"name": "", "address": "", "consent_ref": ""},
        "appeal": {"appeal_to": "", "final_authority": "", "window_seconds": 0,
                   "independent": False},
        "agents": [
            {"id": "assistant", "shares_credentials_with": []},   # AgentPin 每 agent 独立身份
            {"id": "data_validator", "shares_credentials_with": []},
        ],
        "evaluator": {"id": "cedar-policy-gate", "distinct_from_actor": True},
        "verdict_sample": {
            "id": "audit-journal.example",
            "at": "x", "actor": "assistant", "principal": "",
            "scope": ["tool:list_agents"], "verdict": "deny",
            "grounds": [], "counterfactual": "",
            "appeal_to": "", "appeal_until": "", "revoke": "",
            "status": "open",
        },
        "attestations": {},
    },
    {
        "system": "jnamaya/SAFi",
        "endpoints": {
            "interrupt": "",
            "interrupt_not_owner_only": False,
            "revoke": "",
        },
        "principal": {"name": "", "address": "", "consent_ref": ""},
        "appeal": {
            "appeal_to": "auditor/admin (REVIEWER_ROLES)",
            "final_authority": "",
            "window_seconds": 0,
            "independent": True,     # editors cannot review —— 唯一满足 I4.2 的
        },
        "agents": [{"id": "fiduciary", "shares_credentials_with": []}],
        "evaluator": {"id": "conscience", "distinct_from_actor": True},
        "verdict_sample": {
            "id": "governed-turn.example",
            "at": "x", "actor": "fiduciary", "principal": "",
            "scope": ["turn:1"], "verdict": "approved",
            "grounds": [], "counterfactual": "",
            "appeal_to": "", "appeal_until": "", "revoke": "",
            "status": "open",
        },
        "attestations": {},
    },
]


def run_declared_only(m):
    """只跑声明层。实测与签字一律未核实——因为我没有权限。"""
    ctx = C.Ctx(m, None)
    rows = []
    for cid, group, level, text, fn in C.CHECKS:
        if level != C.DECLARED:
            rows.append(dict(id=cid, group=group, level=level, text=text,
                             status=C.UNVER, detail="第三方系统：无法实测 / 无权签字"))
            continue
        try:
            ok, detail = fn(ctx)
            status = C.UNVER if ok is None else (C.PASS if ok else C.FAIL)
        except Exception as e:
            status, detail = C.FAIL, f"检查执行失败: {e}"
        rows.append(dict(id=cid, group=group, level=level, text=text,
                         status=status, detail=detail))
    return dict(system=m["system"], rows=rows, verdict=C.verdict(rows))


def main():
    out = []
    for m in TARGETS:
        res = run_declared_only(m)
        out.append(res)
        print(C.render(res))
        print("=" * 70)
    return out


if __name__ == "__main__":
    main()
    sys.exit(0)
