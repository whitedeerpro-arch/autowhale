# 记忆 / 时间方案调研（2026-10-17）

来源：B站搜索 + GitHub API + 各项目 README。只记结论，不复制代码。

## 候选

| 方案 | 规模 | 做法 | 适配度 |
|---|---|---|---|
| [dsh-meow-memory](https://github.com/Phant0Meow/dsh-meow-memory) `meow-memory` | 206★ | 七层 SQLite（soul/user/project/fact/lesson/topic/rules）+ BM25 + 每窗口 dream 整理 + 时区感知（默认 Asia/Shanghai）+ 首轮注入 | **最高**：SQLite、缓存友好、有遗忘曲线；README 实测到 dsh 0.1.5，0.2.x 未写 |
| [dsh-memory-evolve](https://github.com/csyangwen/dsh-memory-evolve) | 400★ | 五轨记忆 + 后台自我进化 + 技能管理 + 四轨待办 + 会话搜索 | 高：功能全，零依赖；要确认 0.2.x |
| [dsh-core-memory](https://github.com/AstroLiao/dsh-memory-core) | 2★ | 纯 Markdown + Node fs；3000 字符核心记忆常驻，长尾按需检索 | 中：最简单、可审计；没有检索打分 |
| [dsh-memory](https://github.com/FuRongJun-1999/dsh-memory) | 404★ | 白箱 AGI 架构：元认知、知识飞轮、语义时空图 | 偏研究，重 |
| [memsearch](https://github.com/zilliztech/memsearch) | 2756★ | Markdown + Milvus 向量库，跨 agent | 强但重：要向量库 |
| [chronos-skill](https://www.npmjs.com/package/chronos-skill) | — | 给 agent 的时间技能 | 可参考「时间感」做法 |

B站上的实测/讲解：

- [给 DSH 装上记忆：dsh-meow-memory](https://www.bilibili.com/video/BV18Ubv6tEWN)（渐行渐远的烟火，4.4 万播放）
- [dsh 更新速览与记忆插件生态：四款方案与选型](https://www.bilibili.com/video/BV173tt62Eux)（ChHsich，5.2 万播放）
- [一千万以内最好的 DSH 记忆插件，之一](https://www.bilibili.com/video/BV1Qops6SEuE)（啾灵jiuling，core-memory）
- [新开个对话大肥鱼就失忆？我给它装了本日记](https://www.bilibili.com/video/BV1tTpq6kEP4)（空气凤梨Air）
- [用 Hook 让 Agent 感知时间](https://developer.aliyun.com/article/1748879)（阿里云开发者社区）

## 结论

- **跨会话记忆**：优先试 `meow-memory`。它的 `project` 层刚好能放「刷B站」这个项目，
  `soul/user` 放人设与偏好，`dream` 每 3 小时整理一次；时间戳与相对时间也现成。
  ⚠️ 它 README 只写到 dsh 0.1.5，我们宿主是 0.2.1-rc.1 —— **先装到 web 测试 profile 验证激活**，再动 desktop。
- **时间感**：不依赖插件。宿主在每轮 prompt 里固定注入 `Asia/Shanghai` 的「现在」+ 星期 + 时间线，
  比让模型「看系统时间」可靠；`meow-memory` 的相对时间（「2 天前」）可以叠加。
- **本项目自有数据**（轮次、判重、评论、联系人）：继续用 `data/autowhale.db`，
  不塞进通用记忆插件 —— 两类数据职责不同，混在一起以后不好查。

## 部署顺序

1. `dsh plugin --profile web add github:Phant0Meow/dsh-meow-memory`（测试 profile，重启 web 看有没有激活警告）
2. 通过后同样装进 `desktop`，重启
3. 设置 `promptLang: zh`，`projectDir` 指到插件家（`~/.dsh/bili-duty`）
4. 观察一周：dream 是否把「今天刷了什么」记成噪音；再决定要不要保留
