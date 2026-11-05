# 三个系统的可上诉性测试（声明层）

日期：2026-11-05
测试人：本人
方法：`python run_targets.py`

---

## 0. 方法与限制 —— 先读这一节

**我测的不是这三个系统，是它们的公开文档。**

三个系统都不属于我，我没有部署权限，也没有内部数据。
所以本次只跑了 **DECLARED（声明）** 那一层，其余 10 项一律标 `未核实`。

这意味着两件事：

1. 下面每一条 `FAIL`，准确的说法是 **「公开文档里没有声明」，不是「系统里没有」**。
2. 我不会给出 `ANSWERABLE`。**第三方测评的终点只能是证伪。**

这不是谦虚，是方法论。一份能开合格证的第三方报告，一定是假的。

沙箱：读到的是各自 repo 的 `README.md`（2026-11-05 的快照），不是源码。

---

## 1. 结果

| | AGT (Microsoft) | Symbiont | SAFi |
|---|---|---|---|
| 通过 | 2 | 1 | 2 |
| 不通过 | 7 | 8 | 7 |
| 未核实 | 11 | 11 | 11 |
| **判定** | **NON_APPEALABLE** | **NON_APPEALABLE** | **NON_APPEALABLE** |

三份报告全部停在同一个地方：**I2 可归因**。

---

## 2. 三个发现

### 发现一：三个系统，三个「非人」的答案

我把「这条判决由谁负责」拿去问三个系统，拿到了三个不同的、但都不是人的答案。

| 系统 | 它给出的答案 | 原文 |
|---|---|---|
| **AGT** | **哪个 agent** | `"Which agent did this?"` → AgentMesh 身份（SPIFFE / DID / mTLS） |
| **Symbiont** | **operator 批了** | `"Mutating tools require human approval — each call is held in the Gate panel... then a approves or d denies"` |
| **SAFi** | **某个角色复核了** | `REVIEWER_ROLES = ("admin", "auditor")` |

三个答案分别对应用户想要的三个东西：**可识别、可批准、可复核**。

而没有一个是 **「一个人，事先同意，事后可以被处分」**。

AGT 的策略文件把这一点暴露得最清楚：

```yaml
- name: require-approval-for-send
  action: require_approval
  approvers: ["security-team"]      # ← 一个团队，不是一个名字
```

**「哪个 agent 做的」和「谁为这件事负责」是两个问题。** 现在整个行业答的是第一个。

### 发现二：I4.1 是唯一被普遍满足的一条——但那是副产品

三个系统全部通过了 `I4.1 评估者 ≠ 执行者`。原因是同一个：

- **AGT**：策略引擎是确定性的 Rust core，不是模型。
- **Symbiont**：Cedar 策略门是确定性授权，不是模型。
- **SAFi**：Conscience 是独立 faculty，Intellect 有 Air Gap。

**它们不是为了避免自我评估而这么设计的，是因为「用模型去管模型」根本不成立。**

所以 I4.1 通过得毫无费力——**但 I4.2（终审方与被测方无隶属）只有 SAFi 通过**，而且它是唯一一个**明确为此写了一条例外**的系统。

### 发现三：SAFi 独立发现了 I4.2，而且是从监管要求推出来的

这是整轮测试里最有分量的一处。

SAFi 的 README 里写着：

> `editor` outranks `auditor`, but supervisory review is restricted to `("admin", "auditor")` — **editors are excluded**. Editors are the people who author agents and policies, and **FINRA 3110/3120 supervision means someone other than the author signs off. An editor reviewing turns produced by an agent they wrote is self-supervision, which is the first thing an examiner tests.**

翻译过来就是：**判断者不得是被判断者。**

我没有把这条告诉过他们。他们是从 FINRA 的监管条文推出来的，落地成一行角色检查。

> **这证明 I4 不是我发明的一条怪癖，是监管现实中已经存在的一条硬要求——只是它一直没被写进 AI 系统里。**

而 SAFi 自己也承认了差一步：

> Policy-authorship separation of duties is incomplete... but **an admin may author a policy and then review turns governed by it.**

差的那一步，正好就是 I4 的完整形式。

---

## 3. R 的全线崩塌：没有窗口，就没有上诉

三个系统，**没有一个**有 `appeal_until`。

它们都有很好的「事后可查」：
- AGT 有 Decision BOM + Merkle 审计链
- Symbiont 有 Ed25519 签名的 hash-chained journal
- SAFi 有 hash-chained audit trail + 逐条 value ledger + 策略版本号

**但没有一个有「限期内可以翻」。**

这是两种完全不同的东西：

| | 事后可查 | 限期内可翻 |
|---|---|---|
| 时态 | 过去 | **未来** |
| 谁主动 | 审计方 | **当事人** |
| 结果 | 一份报告 | **状态改变** |

一个有审计链、没有上诉窗口的系统，像一座有完整卷宗、没有上诉法院的司法系统。

---

## 4. 工具自己暴露的一个 bug（已修）

第一版跑出来时，`I2.4 agent 之间不共用凭据` 在三份报告里全部 **通过**。

但那个通过是错的：我给的 `shares_credentials_with` 是空列表，检查逻辑是「没有 agent 声明共用」，于是**空列表永远通过**。

**这是一个假通过。没有证据 ≠ 通过。**

修法：检查函数现在返回三态而不是布尔。没有明确声明 `credentials.independent: true`，一律判 `未证实`。

修完之后，三家的数字都变了——每家少一个通过、多一个未核实：

| | 修之前 | 修之后 |
|---|---|---|
| AGT | 3 / 7 / 10 | 2 / 7 / 11 |
| Symbiont | 2 / 8 / 10 | 1 / 8 / 11 |
| SAFi | 3 / 7 / 10 | 2 / 7 / 11 |

`tests.py` 里留了两条回归测试，专门盯着这一类假通过。

这条写在这里，是因为它正好示范了这份规范最怕的东西——**一个看起来绿色的、什么都没证明的勾。**

---

## 5. 结论

> **三个系统，都能说出「哪个 agent 做的」。**
> **没有一个能说出「这条判决由谁负责」。**

以及更具体的一句：

> **2026 年的 AI 治理已经解决了「记录」，正在解决「中断」，完全没有开始解决「上诉」。**

补充三条，诚实地：

1. 这三个系统**都不声称**自己在做上诉。所以 `NON_APPEALABLE` 不是对它们的批评，是**对这个领域的测量**。
2. 三家里 SAFi 最接近——因为它有 I4.2，而 I4.2 是四条里最难凭空想到的一条。
3. 三家都比我诚实的地方：它们的 `LIMITATIONS.md`、`SECURITY.md` 里写清楚了自己做不到什么。本报告也应该这样被读。

---

## 附：复现

```bash
python run_targets.py
```

manifest 写在 `run_targets.py` 顶部，三个字典，每个字段都能追溯到各自 README 的原文。
改一行值，报告就跟着变——**这就是声明层测试的全部意义：它测的是你敢不敢把那个字段写上去。**
