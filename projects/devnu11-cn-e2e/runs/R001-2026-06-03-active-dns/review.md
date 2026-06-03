# 本轮复盘

## 概要

- 项目：devnu11-cn-e2e
- 复测编号：R001
- Run：R001-2026-06-03-active-dns
- 复盘时间：2026-06-03 15:48:00

## 本轮做得好的

- 用户用 `ai.` 及时指出“0 命中”不可信，促使先做最小链路复核，没有把错误结果沉淀成结论。
- 修正后完整主字典扫描在约 99.363 秒完成，满足“完整字典不超过 5 分钟”的目标。
- 对命中结果追加 A/AAAA/CNAME 复核，区分了可解析到 Cloudflare 的子域和 `online` 这类 NODATA 候选。

## 本轮问题

| 问题 | 影响 | 后续动作 |
| --- | --- | --- |
| dnsx `-wd` 参数误用 | 上一次命令进入泛解析过滤模式，没有真正跑字典，导致空结果 | 后续应把泛解析检查与字典枚举拆成两个步骤；CLI 封装中禁止把 `-wd` 当作扫描参数 |
| 缺少扫描前 canary 校验 | 已知存在的 `ai.devnu11.cn` 没有先被用来验证链路，导致错误更晚暴露 | 主动 DNS 流程加入 canary：已知词条、随机 NXDOMAIN、resolver 健康检查 |
| NOERROR 被误读风险 | `online.devnu11.cn` 是 NOERROR 但无 A/AAAA，不能直接当作 Web 入口 | 结果解析要区分 A/AAAA/CNAME、NODATA、NXDOMAIN 和 wildcard 噪声 |

## 对 skill 的反馈

| skill | 反馈 | 建议 |
| --- | --- | --- |
| `skills/recon/subdomain-enumeration/SKILL.md` | 需要更明确地区分“泛解析检测”和“主动字典枚举”，并提示 `dnsx -wd` 的模式风险 | 增加执行前 canary、resolver 自检、随机 NXDOMAIN 检查、NOERROR/NODATA 分类 |

## 对 CLI 的反馈

| 命令或能力 | 反馈 | 建议入池需求 |
| --- | --- | --- |
| `pents doctor-recon` | 能发现工具缺失，但不能验证 dnsx 参数组合是否会跑偏 | 增加主动 DNS 运行前 checklist 输出 |
| `pents active-dns`（待实现） | 这次手工链路暴露出参数、证据、hash、分类都适合封装 | 新增 CLI：输入 domain + dict + resolvers，自动 canary、wildcard、枚举、记录复核、证据登记 |

## 对 tools 的反馈

| 场景 | 是否适合自写脚本 | 原因 | 建议目录 |
| --- | --- | --- | --- |
| DNS 枚举结果分类 | yes | 需要把 dnsx JSONL 分成 A/AAAA/CNAME、NOERROR/NODATA、NXDOMAIN、疑似 wildcard，方便报告和字典治理 | `tools/recon/` |

## 对 dicts 的反馈

| 词条 | 类型 | 来源证据 | 处理建议 |
| --- | --- | --- | --- |
| `ai` | 命中 | E-0009；主字典第 882 行 | 已在 curated 主字典，无需回灌 candidates |
| `blog` | 命中 | E-0009 | 已在主字典，后续纳入命中率统计 |
| `lk` | 命中 | E-0009 | 已在主字典，后续纳入命中率统计 |
| `st` | 命中 | E-0009 | 已在主字典，后续纳入命中率统计 |
| `online` | NODATA 候选 | E-0009/E-0010 | 保留为候选 DNS 名，不作为 HTTP 入口；后续复查记录变化 |

## 待进入需求池

| 需求 | 优先级 | 原因 |
| --- | --- | --- |
| 实现 `pents active-dns` 主动 DNS 封装 | P1 | 防止 `-wd` 等参数误用，自动完成 canary、wildcard 检查、完整枚举、记录复核、证据登记和报告摘要 |
| 完善 subdomain-enumeration skill 的主动 DNS 执行检查表 | P1 | 让 Claude Code 执行时主动说明工具缺失、参数风险、resolver 选择和 NOERROR/NODATA 分类 |
| 推进 T-0032 字典治理 | P2 | 本轮提供了命中率 5/167377、有效 A/AAAA 4/167377、耗时约 99 秒的数据点 |
