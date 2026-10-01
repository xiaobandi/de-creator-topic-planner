# 选题库去重匹配

> 候选池比对个人历史选题库→剔除/标注重复→剩余排序

工作流 `wf-creator-topic-dedup`　·　归属 爆款选题策划师　·　触发 事件（WF1 完成后自动）　·　
复杂度 S　·　阶段 P0

## 调用链

- `选题查重`（topic-duplicate-check）
- `选题知识库管理`（topic-kb-manage）

## 文档

- [`WORKFLOW.md`](WORKFLOW.md) — 完整编排、闸门、降级与验收标准
- [`tests/cases.yaml`](tests/cases.yaml) — 端到端 / 闸门 / 降级用例

## 一句话试用

```text
帮我跑 爆款选题策划师 的「选题库去重匹配」：<你的输入>
```
