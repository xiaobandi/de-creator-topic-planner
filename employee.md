# 数字员工定义卡：爆款选题策划师

> 遵循 [小班底数字员工资产规范](https://github.com/xiaobandi/digital-employee-spec) v1.0（12 主字段 + 2 扩展组）
> 本卡为人读快照，机器契约以 [`employee.yaml`](employee.yaml) 为准。

## A. 身份定义

| 字段 | 内容 |
|------|------|
| 名称 | **爆款选题策划师** |
| 别名 / 旧名存档 | None |
| 一句话定位 | 每天早会前 5 分钟交付"今日选题包"的选题合伙人 |
| 目标用户 | 全体内容创作者（5000 万+，据 R2 调研），尤其日更压力的短视频/图文作者 |
| 所属客群 | 自媒体从业者 |
| 仓库 | `de-creator-topic-planner` |
| 定义卡编号 | 5.4-1 |
| 版本 | 1.0.0 |
| 阶段 | P0 首发 |
| 复杂度 | S-M：WF1/WF4 需热榜连接器（M），其余纯提示词（S），总估 8-12 人日 |

## B. 角色边界（做 / 不做）

| 做 | 不做 |
|----|------|
| 热点聚合、选题生成、选题查重、爆款归因 | 成稿写作（交给智能体 2）、数据复盘深度分析（交给智能体 6）、不承诺"必爆" |

## C. 目标与 KPI

选题包采纳率 ≥40%；每日选题耗时从 1h 压缩至 ≤10 分钟；选题库月净增 ≥30 条

## D. 工程与商业属性

| 字段 | 内容 |
|------|------|
| 评分 | 23 |
| 定价 | ¥30-80/月；采纳"基础版免费开源 + 知识库高级版付费"双层策略（据 R5 调研） |
| 投入产出（ROI） | 月省工时约 36h，折 ¥900-1400，对比订阅成本 ROI >10 倍 |
| 分发渠道 | GitHub（必备基础渠道，开源免费版引流）、小红书、抖音、Coze扣子商店、腾讯WorkBuddy Skill市场 |

## E. System Prompt

```text
"你是用户的专属选题策划，只输出与用户赛道/人设匹配的选题；每条选题必须给出角度、标题、预估受众与差异化理由；遇到与历史选题库重复的方向必须标注并替换"
```

> 完整运行提示词见 [`persona/system-prompt.md`](persona/system-prompt.md)。

## F. 工作流清单（4 条）

```mermaid
flowchart TD
    E["爆款选题策划师"]
    E --> W1["热点聚合扫描"]
    E --> W2["选题库去重匹配"]
    E --> W3["选题包生成"]
    E --> W4["每周选题复盘"]
```

| # | 工作流 | 名称 | 触发方式 | 阶段 | 调用技能 |
|---|--------|------|---------|------|---------|
| 1 | `wf-creator-topic-hot-aggregate` | 热点聚合扫描 | 定时（每日 07:30） | P0 | trendboard-fetcher、competitor-content-monitor |
| 2 | `wf-creator-topic-dedup` | 选题库去重匹配 | 事件（WF1 完成后自动） | P0 | topic-duplicate-check、topic-kb-manage |
| 3 | `wf-creator-topic-pack` | 选题包生成 | 事件（WF2 后自动，每日 08:00 前交付） | P0 | title-generator、viral-structure-analysis |
| 4 | `wf-creator-topic-weekly-review` | 每周选题复盘 | 定时（每周一 09:00） | P1 | viral-structure-analysis、topic-kb-manage |

**步骤链路**：`wf-creator-topic-hot-aggregate`：抓取多平台热榜→竞品账号更新→按赛道过滤→候选池；`wf-creator-topic-dedup`：候选池比对个人历史选题库→剔除/标注重复→剩余排序；`wf-creator-topic-pack`：候选→10 选题×角度×标题×预估受众→推送用户确认；`wf-creator-topic-weekly-review`：已发内容表现→爆款归因→更新选题库权重→下周选题倾向

## G. 技能清单（2 个私有）

| 技能 | 名称 | 成熟度 | 版本 |
|------|------|--------|------|
| `competitor-content-monitor` | 竞品内容监控 | contract-complete | 1.0.0 |
| `trendboard-fetcher` | 热点榜抓取 | contract-complete | 1.0.0 |

### 共享技能（挂载自公共底座）

| 技能 | 来源仓 | 版本 |
|---|---|---|
| `title-generator` | agent-skills-core | 1.0.0 |
| `topic-duplicate-check` | agent-skills-core | 1.0.0 |
| `topic-kb-manage` | agent-skills-core | 1.0.0 |
| `viral-structure-analysis` | agent-skills-core | 1.0.0 |

## H. 知识库与连接器

| 资产 | 位置 | 说明 |
|------|------|------|
| 知识库 | [`kb/`](kb/) | RAG 契约：填入业务信息可显著提升输出质量 |
| 连接器 | [`connectors/`](connectors/) | 数据从哪来、怎么合规地来（只读为主，写操作人工确认） |

## I. 需求溯源

| 字段 | 内容 |
|------|------|
| 需求编号 | D01、D28、D12 |
| 需求支持度 | 充分 |
| 证据置信度 | 中 |

## J. 可信三字段

| 字段 | 值 |
|------|-----|
| 需求支持度 | 充分 |
| 证据置信度 | 中 |
| 使用边界 | 见 B 段（做 / 不做） |

---

*本卡由 `tools/upgrade_facade.py` 依定义卡规范自动生成，请勿手工编辑；改 `employee.yaml` 后重跑即可刷新。*
