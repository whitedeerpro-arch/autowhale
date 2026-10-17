# 会话交接（2026-10-17 17:12）

> 给「压缩后 / 新会话」的我：先读这一页，再读 `memory.md`、`timeline.md`、`docs/`。

## 现在是什么状态

- **目标**：autowhale（自动鲸鱼）——每天替使用者刷 B站、写日报；能回私信、能主动联系社群。
- **底座**：`dsh-bili-scroll` 插件（fork：`whitedeerpro-arch/dsh-bili-scroll`，分支 `feat/memory-time`）
- **本机插件家**：`C:\Users\White deer\.dsh\bili-duty`（凭证、memory.md、timeline.md、out/、overlay）
- **仓库**：`D:\workspace_llm\autowhale`（main `53556ea` 之后）
- **长期记忆**：meow-memory 0.31.0（desktop + web，promptLang=zh；记忆库 `.dsh-meow/memory.db`）
- **B站**：账号「自动鲸鱼和虚拟白饭」(569166300)；@ 的人是「一只深沉」(10450479)

## 正在跑的

| 东西 | 状态 |
|---|---|
| 反射 watcher | `scripts/inbox_watch.py`，后台 job `pwsh-ae14f83085dc4844`，20s 轮询 10450479 |
| 行为 | 寒暄 → 模板；≤4 字短句 → 忽略；其它 → 先回占位，再 spawn headless |
| spawn | 复用 `DeepSeek Harness.exe + app.asar/.../cli.js + headless-overlay.yml`；预算 6/时、30/天；同一时间一轮 |
| 日志 | `inbox-watch.log`（轮询/回复）、`agent-spawn.log`（agent 输出/退出码） |

## 刚踩的坑

- Python **看不到 app.asar 里的 cli.js**：`os.path.exists` 为 False → spawn 被跳过（日志 `spawn skipped: dsh/overlay missing`）。
- 修法：只检查 `exe` 和 `overlay`，CLI 路径直接交给 Electron 解析。已实测 `exit=0`，9.5s。

## 待办

1. 让 watcher 常驻（Windows 计划任务 / 宿主插件），现在还是本会话的后台进程。
2. dsh-message-gateway 0.2.1 POST body 兼容（`missing text/chatid`）：提 issue 或补丁。
3. meow-memory 装进 headless（现在 headless 只读 memory.md，读不到 meow-memory）。
4. SQLite（`data/autowhale.db`）接管 `seen.md` + 待处理队列。
5. 等蓝鲸灵（1628807448）回信；7 天冷却到 10-24。

## 上下文/多联系人

- watcher **每条消息 spawn 一个新 headless**，上下文不跨联系人累积；每轮只读 memory.md + timeline。
- 绝不能把所有联系人塞进同一个会话——那会迅速打满。按联系人隔离 + 只注入相关记忆是标准做法。
- 本对话很长：压缩用 `/compact`，或开新会话；长期记忆在 meow-memory，不会丢。
