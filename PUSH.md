# 怎么把它推到 GitHub

五分钟的事。按顺序做，别跳。

---

## 0. 发之前，改三个地方

**① LICENSE 第一行的名字**

```
Copyright (c) 2026 <YOUR NAME>
```

改成你的名字或 GitHub handle。不改的话，这份许可证是无效的。

**② README 里的仓库名**

如果你不叫 `recourse`，把 README 里出现的仓库名换掉。目前只在一处。

**③ 确认没有垃圾文件**

```powershell
Get-ChildItem -Force | Select-Object Name
```

应该有这些（`.gitignore` 会自动排除 `__pycache__`）：

```
.github/  .gitignore  LICENSE  README.md  RESULTS.md  SPEC...
TESTING.md  appeal_check.py  conformance.py  run_targets.py
scorecard.html  tests.py
```

---

## 1. 在 GitHub 上建仓库

打开 https://github.com/new

- **Repository name**: `recourse`
- **Description**: `Every agent decision should come with a receipt, a deadline, and an undo button.`
- **Public**
- **不要**勾 "Add a README"、"Add .gitignore"、"Choose a license" —— 你本地都有了

建完记下那个地址，形如 `https://github.com/<你的用户名>/recourse.git`

---

## 2. 推上去

```powershell
cd "D:\TRAE SOLO CN\output\appeal"

# 如果这台机器没配过 git 身份
git config --global user.name  "你的名字"
git config --global user.email "你的邮箱"

git init
git add .
git status                # ← 先看一眼，确认没有 __pycache__、没有无关文件
git commit -m "recourse v0.1: appealability spec + conformance test + 3-system results"
git branch -M main
git remote add origin https://github.com/<你的用户名>/recourse.git
git push -u origin main
```

第一次 push 会要求登录。GitHub 现在不收密码，用 **Personal Access Token**：
Settings → Developer settings → Personal access tokens → Tokens (classic) → 勾 `repo` → 生成 → 复制。

或者直接装 [GitHub CLI](https://cli.github.com/)，然后：

```powershell
gh auth login
gh repo create recourse --public --source . --push
```

一条命令搞定。

---

## 3. 推完立刻做三件事（否则等于没推）

**① 打开 Actions 页面，看 CI 是不是绿的**

绿了就说明：8 个测试通过、记录校验器自测通过、演示系统被判 `NON_APPEALABLE`。
**那个红色其实是绿色** —— 演示本来就该失败。CI 里写清楚了。

**② 点仓库右上角的 ⚙️ → 把 Topics 填上**

```
ai-agents  accountability  audit  ai-governance  appeal  corrigibility
```

这是别人搜到你的唯一途径。

**③ 把仓库地址发到该发的地方**

一篇 800 字，标题就是那个发现，不是项目介绍。

---

## 4. 如果不想用命令行

**GitHub Desktop**：File → Add local repository → 选这个目录 → Publish repository。

**网页上传**：直接在 GitHub 建空仓库，然后 "uploading an existing file"，拖整个文件夹进去。
（`.github/workflows/ci.yml` 这种带点开头的目录，网页上传容易漏，命令行更稳。）

---

## 5. 之后

- 别忘了 `RESULTS.md` 里那条：**三家系统，没有一个能说出「谁负责」。** 那才是别人会转的东西。
- 下次改东西之前先 `python tests.py`。

---

## 附：这个仓库现在有什么

| 文件 | 作用 |
|---|---|
| `README.md` | 门面。三句话 + 四条不变量 + 两个工具 |
| `APPEALABILITY-v0.1.md` | 规范：schema、反事实测试、20 项 |
| `conformance.py` | 测一个系统，三档证据，四态判定 |
| `appeal_check.py` | 测一条判决记录 |
| `tests.py` | 8 个行为测试，含两条假通过回归 |
| `run_targets.py` | 对三个真实系统的声明层测试 |
| `RESULTS.md` | 测试报告。**这是最值钱的一份** |
| `TESTING.md` | 怎么测别人的系统（含五个杀手问题） |
| `scorecard.html` | 双击打开的人工体检表 |
| `LICENSE` | MIT（代码）+ CC BY 4.0（规范） |
| `.github/workflows/ci.yml` | 两个系统 × 两个 Python 版本 |
