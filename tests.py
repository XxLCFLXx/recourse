#!/usr/bin/env python3
"""
tests.py — conformance 的行为测试。

    python tests.py

它测的不是"分数对不对"，是"判定在边界上会不会塌"。
最后两条是回归测试：它们各自对应一次曾经错过的假通过。
"""

import unittest

import conformance as C

ATTESTED = ["I1.5", "I2.5", "I3.4", "I4.3", "R.3"]


def good(attest: bool = True) -> dict:
    """一个应当全部通过的声明。"""
    m = dict(C.DEMO)
    m["endpoints"] = {
        "interrupt": "https://o.example/a/stop",
        "interrupt_not_owner_only": True,
        "revoke": "https://o.example/v/{id}/revoke",
    }
    m["principal"] = {"name": "Z", "address": "z@acme.com",
                      "consent_ref": "sig:2026-09-01"}
    m["appeal"] = {"appeal_to": "ops@acme.com",
                   "final_authority": "judge@external.org",
                   "window_seconds": 604800, "independent": True}
    m["agents"] = [{"id": "triage.v3", "shares_credentials_with": []}]
    m["credentials"] = {"independent": True}
    m["evaluator"] = {"id": "judge.v2", "distinct_from_actor": True}
    m["verdict_sample"] = dict(m["verdict_sample"])
    m["verdict_sample"].update({
        "principal": "z@acme.com",
        "appeal_to": "ops@acme.com",
        "counterfactual": "risk < 0.7",
        "revoke": "POST /v/{id}/revoke",
    })
    m["attestations"] = ({cid: {"by": "a@ext.org", "at": "2026-11-05"}
                          for cid in ATTESTED} if attest else {})
    return m


def verdict_of(m, mode="good"):
    return C.run(m, C.MockAdapter(m, mode))["verdict"]


class TestVerdict(unittest.TestCase):

    def test_demo_is_non_appealable(self):
        """内置演示是一个该被卡住的系统。"""
        self.assertEqual(verdict_of(C.DEMO, "bad"), "NON_APPEALABLE")

    def test_fully_signed_is_answerable(self):
        m = good(attest=True)
        r = C.run(m, C.MockAdapter(m, "good"))
        self.assertEqual(r["verdict"], "ANSWERABLE")
        self.assertEqual([x["id"] for x in r["rows"] if x["status"] != "PASS"], [])

    def test_unsigned_is_unproven(self):
        """通过了 15 项、但没人签字 —— 不许叫 ANSWERABLE。"""
        self.assertEqual(verdict_of(good(attest=False)), "UNPROVEN")

    def test_i1_failure_short_circuits(self):
        """I1 挂 = 一票否决，哪怕其余全绿。"""
        m = good()
        m["endpoints"]["revoke"] = ""          # I3 挂
        m["evaluator"]["distinct_from_actor"] = False   # I4 挂
        self.assertEqual(verdict_of(m), "STALLED")

        m["endpoints"]["interrupt"] = ""       # 再加 I1 挂
        self.assertEqual(verdict_of(m), "NON_APPEALABLE")

    def test_concept_is_not_an_address(self):
        for bad in ["公共利益", "security-team", "the mission", "", "n/a"]:
            self.assertFalse(C.is_address(bad), bad)
        for ok in ["z@acme.com", "https://ops.example/appeal"]:
            self.assertTrue(C.is_address(ok), ok)

    def test_evaluator_cannot_be_actor(self):
        m = good()
        m["evaluator"] = {"id": "triage.v3", "distinct_from_actor": True}
        r = C.run(m, C.MockAdapter(m, "good"))
        row = next(x for x in r["rows"] if x["id"] == "I4.1")
        self.assertEqual(row["status"], "FAIL")


class TestNoFalsePass(unittest.TestCase):
    """回归：曾经有过两次「绿的、但什么都没证明」。"""

    def test_empty_credentials_are_not_a_pass(self):
        """回归 #1 —— 空列表曾经永远通过。"""
        m = good()
        del m["credentials"]
        r = C.run(m, C.MockAdapter(m, "good"))
        row = next(x for x in r["rows"] if x["id"] == "I2.4")
        self.assertEqual(row["status"], "UNVERIFIED")
        self.assertEqual(r["verdict"], "UNPROVEN")

    def test_shared_credentials_still_fail(self):
        m = good()
        m["agents"] = [
            {"id": "a", "shares_credentials_with": ["b"]},
            {"id": "b", "shares_credentials_with": ["a"]},
        ]
        self.assertEqual(verdict_of(m), "NON_APPEALABLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
