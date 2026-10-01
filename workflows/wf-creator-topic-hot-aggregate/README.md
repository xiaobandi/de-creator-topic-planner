# 热点聚合扫描

> 抓取多平台热榜→竞品账号更新→按赛道过滤→候选池

工作流 `wf-creator-topic-hot-aggregate`　·　归属 爆款选题策划师　·　触发 定时（每日 07:30）　·　
复杂度 M　·　阶段 P0

## 调用链

- `热点榜抓取`（trendboard-fetcher）
- `竞品内容监控`（competitor-content-monitor）

## 文档

- [`WORKFLOW.md`](WORKFLOW.md) — 完整编排、闸门、降级与验收标准
- [`tests/cases.yaml`](tests/cases.yaml) — 端到端 / 闸门 / 降级用例

## 一句话试用

```text
帮我跑 爆款选题策划师 的「热点聚合扫描」：<你的输入>
```
