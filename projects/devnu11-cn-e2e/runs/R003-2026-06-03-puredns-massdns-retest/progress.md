# 本轮测试进度

## 概要

- 项目：devnu11-cn-e2e
- 复测编号：R003
- Run：R003-2026-06-03-puredns-massdns-retest
- 当前阶段：completed
- 执行主体：Claude Code（按 T-0042 任务卡正式执行）
- 执行时间：2026-06-04 11:05:36 ~ 11:06:36 CST
- 引擎：massdns direct

## 本轮目标

- 按 T-0042 任务卡正式执行 `devnu11.cn` 主动 DNS 子域名枚举
- 使用 `massdns direct` 默认链路，不复用旧 puredns pipe
- 与 R001 Codex 前置验证基线对比

## 时间线

| 时间 | 执行者 | 动作 | 结果 | 证据引用 |
| --- | --- | --- | --- | --- |
| 2026-06-04 11:05 | Claude Code | 生成执行计划（pents active-dns --engine auto） | 计划已保存到 outputs/ | E-0011 |
| 2026-06-04 11:05:36 | Claude Code | Canary 校验（ai.devnu11.cn） | canary 命中，6 个 resolver 全部可用 | E-0011 |
| 2026-06-04 11:05:37 | Claude Code | NXDOMAIN 泛解析检查 | 随机子域 NXDOMAIN 无命中，无 wildcard | E-0011 |
| 2026-06-04 11:05:37 | Claude Code | 候选生成（167377 词条） | 0.707 秒完成 | E-0011 |
| 2026-06-04 11:05:38 | Claude Code | 完整字典枚举（massdns） | 56.443 秒完成 | E-0011 |
| 2026-06-04 11:06:35 | Claude Code | 命中提取 | 4 命中（ai/blog/lk/st） | E-0011 |
| 2026-06-04 11:06:36 | Claude Code | 执行完成 | 总耗时 60.669 秒，成功 | E-0011 |

## 已执行项

| 目标 | 测试面 | 方法 | 结果 | 证据引用 | 是否需要合并到顶层 |
| --- | --- | --- | --- | --- | --- |
| `devnu11.cn` | 主动 DNS 子域名枚举 | massdns direct（tools/recon/active-dns-massdns.ps1） | 167377 候选，4 命中，60.669 秒 | E-0011 | yes |

## 命中对比：R003 vs R001

| 子域名 | R001 (dnsx) | R003 (massdns) | 备注 |
| --- | --- | --- | --- |
| `ai.devnu11.cn` | NOERROR + A/AAAA | A 命中 | 一致 |
| `blog.devnu11.cn` | NOERROR + A/AAAA | A 命中 | 一致 |
| `lk.devnu11.cn` | NOERROR + A/AAAA | A 命中 | 一致 |
| `st.devnu11.cn` | NOERROR + A/AAAA | A 命中 | 一致 |
| `online.devnu11.cn` | NOERROR，无 A/AAAA | **未命中** | massdns 只捕获有 A/AAAA/CNAME 的记录，NODATA 不出现 |

## 差异分析

- R001 使用 dnsx，查询类型 a+aaaa+cname，rcode=noerror，命中包括 NOERROR 但无 A/AAAA 的 `online.devnu11.cn`
- R003 使用 massdns，记录类型 A（`-t A`），`Snl` 输出格式只包含有 A/AAAA/CNAME 记录的域名
- `online.devnu11.cn` 未出现在 R003 命中中是预期行为——E-0010 已将其标记为 NODATA 候选，不作为 Web 入口
- 两次执行在可解析子域名层面完全一致（ai/blog/lk/st），且 A 记录均指向同一组 Cloudflare IP

## 跳过 / 阻塞项

原因类型可选：授权缺失、工具缺失、目标无输入、网络失败、风险过高、范围外、等待账号、其他。

| 目标 | 测试面 | 状态 | 原因类型 | 具体原因 | 已尝试来源 / 替代动作 | 影响 | 需要用户补充 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 无 | — | — | — | 本轮无阻塞项 | — | — | — |

## 本轮待归并

| 顶层文件 | 是否需要更新 | 原因 |
| --- | --- | --- |
| inventory.md | yes | 新增 R003 执行结果到资产清单 |
| evidence.md | yes | 新增 E-0011 证据 |
| findings/ | no | 无新漏洞发现 |
| report.md | yes | 更新主动 DNS 测试状态和对比 |
| review.md | yes | 补充执行对比和 massdns 经验 |
