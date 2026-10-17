# autowhale ｜ 自动鲸鱼（个人版）

> 每天替我刷一轮 B 站：搜、**读字幕原文**判断、写一份日报；特别值得的，才用我的号留一条评论 @ 我。

这是**我自己的那一套**，不是插件本体。插件（`dsh-bili-scroll`）是底座，装在本机的 DSH 里；这个仓库放我的配置、章程、脚本和运行记录规范。

## 现在到哪一步了

- [x] 本机 DSH 桌面版装好插件（`link:` 到本地工作副本）
- [x] Python 3.12 venv + MCP 依赖装好
- [x] B站 扫码登录（凭证只在本机）
- [x] 用插件自己的 `bili_run` 真跑通一轮：`code=0`，报告写出来了
- [x] 桌面版那几个「跑不起来」的坑修掉（0.1.6，在 fork 的分支上）
- [x] 自己的仓库结构 / 配置
- [x] SQLite schema（建库脚本可跑；插件还没接上）
- [x] 长记忆初版：`memory.md` + `timeline.md` + 每轮提示词简报（见 `docs/memory-and-time.md`）
- [x] 时间感：宿主固定注入 `Asia/Shanghai` 的「现在」，不再让模型猜
- [x] 社群通讯录：154 个联系人（5 个 UP + 30+ 活跃鲸鱼），0 条主动发信（见 `docs/community-policy.md`）
- [x] 记忆方案调研：meow-memory / memory-evolve / core-memory / memsearch（见 `docs/memory-solutions.md`）
- [x] meow-memory 0.31.0 装进 desktop + web，web 启动无警告、desktop 已热加载
- [ ] 观察 meow-memory 的 dream 是否产生噪音；再决定是否接进 headless 值班轮
- [ ] SQLite 替掉 `seen.md`（要改插件宿主半）
- [ ] 待处理队列：谁回复了我、哪条还没回
- [ ] 加密凭据库
- [ ] 通知（跑完/失败推给我）

## 目录约定

```
autowhale/
  README.md
  config.example.json     # 插件设置样例（不含任何凭证）
  .gitignore
```

以后往这几块长：

| 目录 | 放什么 |
|---|---|
| `config/` | 我自己的关键词、条数、@ 名单等（`autowhale.json` 是当前在用的那份） |
| `db/` | `schema.sql`：rounds / videos / comments / transcripts / events / contacts / contact_events |
| `scripts/` | 一次性工具（`init-db.mjs` 建库、迁移、对账、导出） |
| `charter/` | 我改过的值班章程（插件支持用「比它新」的那份） |
| `docs/` | 决策记录、踩坑、每轮日报的索引 |

## 本地库

```bash
node scripts/init-db.mjs      # 建 data/autowhale.db（Node ≥ 22.5，DSH 自带 Node 24 即可）
```

`data/` 不进仓库。表结构见 `db/schema.sql`：每轮、看过的视频、发过的评论（含复核）、
字幕原文、审计事件 —— 以后 `seen.md` 只是给眼睛看的导出，真相在库里。

## 社群关系（多看少发信）

```bash
python scripts/scan_bili.py        # 扫一批视频的公开评论 → scan.json
node scripts/import-contacts.mjs   # 去重导入通讯录，生成 data/contacts.md
```

当前 154 个联系人：5 个 UP（凌羽clover / 渐行渐远的烟火 / ChHsich / 空气凤梨Air / 啾灵jiuling）
+ 30 多个活跃自动鲸鱼；**一条主动私信都没发**。发信闸门、冷却、拉黑规则见
[community-policy.md](docs/community-policy.md)。

## 不放进来的东西

- **任何凭证**：B站 cookie 在 `%USERPROFILE%\.dsh\bili-duty\bili_credential.json`，不进仓库
- **插件本体**：`dsh-bili-scroll/` 是独立仓库（我的 fork），本仓库只引用，不复制
- **运行产物**：`out/`、`duty.log`、`bili-test/`（测试脚本与会话导出）都在 `.gitignore` 里

## 底座

- 上游：<https://github.com/c1overzz/dsh-bili-scroll>
- 我的 fork：<https://github.com/whitedeerpro-arch/dsh-bili-scroll>
- 我改的分支：`fix/0.1.6-desktop`

## 安全

- 凭证只用扫码登录拿，**不要密码**
- git 用 SSH key（`dsh-agent @ LAPTOP-6TQH6JHQ`），私钥不离开本机
- 公开仓库里不放任何能定位到个人账号/路径之外的信息
