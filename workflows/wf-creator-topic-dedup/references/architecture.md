# 能力与字段速查

技能：`wf-creator-topic-dedup`（L2 工作流技能）

## 元信息

| 字段 | 值 |
|---|---|
| 技能 ID | `wf_creator_topic_dedup` |
| 目录 | `workflows/wf-creator-topic-dedup` |
| 复杂度 | S |
| 阶段 | P0 |
| 可见性 | employee-owned |
| 版本 | v1.0.0 |
| 许可 | MIT |
| 验证等级 | B（工作流技能，其调用链中的确定性脚本已逐个真实执行：`topic-kb-manage`） |

## 输入契约

- **必填**：流程起始材料（见执行步骤第 1 步）
- **必填**：用户身份与目标渠道/平台
- **可选**：历史产出
- **可选**：账号人设
- **可选**：渠道规则
- **可选**：上一周期数据

## 脚本清单

| 脚本 | 用途 | 调用方式 |
|---|---|---|
| `../../tools/kb_manage.py` | 确定性执行逻辑 | `python3 ../../tools/kb_manage.py` |

真实调用：

```bash
python3 ../../tools/kb_manage.py --db examples/input/kb.json add --title '通勤保温杯实测' --tags '产品,测评' --weight 3
python3 ../../tools/kb_manage.py --db examples/input/kb.json add --title '办公室喝热水指南' --tags '场景,科普' --weight 2
python3 ../../tools/kb_manage.py --db examples/input/kb.json add --title '保温原理 3 秒讲清' --tags '科普' --weight 1
python3 ../../tools/kb_manage.py --db examples/input/kb.json list --top 5
```

## 质量门

- 新增前做过查重
- 各步产出按顺序衔接，链路无断点
- 缺料时显式停下来问，未用假设填补

## 已知陷阱

- 库以 JSON 文本落盘，天然可 git 版本化——不要把库塞进某个不透明的数据库

## 边界

- 只负责本工作流这一条链路，不承担所属员工的其它职责
- 步骤与原子技能是**指示性映射**，允许按实际情况调整，不是强制编排
- 中途缺料必须停下来问，不允许用假设补齐

## 编排关系

- 所属数字员工：`de_creator_topic_planner`
- 建议调用的原子技能：`skill_topic_kb_manage`
- 步骤与技能是**指示性映射**，允许按实际情况调整
