# 本轮复盘

## 概要

- 项目：devnu11-cn-e2e
- 复测编号：R003
- Run：R003-2026-06-03-puredns-massdns-retest
- 复盘时间：2026-06-04 11:10:00
- 执行主体：Claude Code（T-0042）

## 本轮做得好的

- `massdns direct` 链路工作正常，未出现任何步骤失败。
- Canary 预检、resolver 自检、NXDOMAIN 检查均按流程执行，所有 6 个 resolver 通过健康检查。
- 60.669 秒完成 167,377 词条枚举，性能优于 R001 dnsx 的 99.363 秒（约 39% 提速）。
- 结果与 R001 在可解析子域名层面完全一致（ai/blog/lk/st），不存在遗漏。
- 未回退到 puredns pipe，避免了已知的 stdin 卡死问题。
- 执行计划由 `pents active-dns --engine auto` 生成并保存，流程可审计。

## 本轮问题

| 问题 | 影响 | 后续动作 |
| --- | --- | --- |
| `online.devnu11.cn` 未出现在 massdns 命中中 | massdns `Snl` 输出只含 A/AAAA/CNAME 记录，NODATA 域名不出现；E-0010 已将其标记为 NODATA 候选，无实际影响 | 后续如需要 NODATA 捕获，可辅以 dnsx 或单独对命中做 ANY 查询 |
| 本次执行复用了 R003 目录名（puredns-massdns-retest），但实际使用了 massdns direct | 目录名与实际执行引擎不一致，可能引起混淆 | 建议后续 `pents run new` 按实际引擎命名 |
| 字典 167,377 词条仅命中 4 条，命中率约 0.0024% | 字典偏大，大部分词条对 .cn 域名无实际覆盖价值 | 后续字典治理 T-0032 可引入按 TLD 分层的字典 |

## 对 skill 的反馈

| skill | 反馈 | 建议 |
| --- | --- | --- |
| `skills/recon/subdomain-enumeration/SKILL.md` | massdns direct 链路已验证可用，应推荐为默认执行方式 | 增加 massdns direct 推荐和 NODATA 处理说明 |

## 对 tools 的反馈

| 工具 | 反馈 | 建议 |
| --- | --- | --- |
| `tools/recon/active-dns-massdns.ps1` | 脚本运行稳定，所有步骤按预期完成 | 可考虑增加 `-t A,AAAA` 支持以同时获取 IPv6 记录 |

## 对 dicts 的反馈

| 词条 | 类型 | 来源证据 | 处理建议 |
| --- | --- | --- | --- |
| `ai` | 命中 | E-0011 | 已在 curated 主字典 |
| `blog` | 命中 | E-0011 | 已在 curated 主字典 |
| `lk` | 命中 | E-0011 | 已在 curated 主字典 |
| `st` | 命中 | E-0011 | 已在 curated 主字典 |

## 待进入需求池

| 需求 | 优先级 | 原因 |
| --- | --- | --- |
| `pents active-dns` 保存模式 | P2 | run 目录中 summary 已可用，但 CLI 未完成自动保存 |
| 字典分层（按 TLD） | P3 | 167,377 词条仅 4 命中，cn 域名命中率极低 |

## 证据缺口

| 缺口 | 影响 | 如何填补 |
| --- | --- | --- |
| 无 AAAA 记录（本次只查 A） | 无法确认 IPv6 解析 | 如需 IPv6，后续可用 `-RecordType A,AAAA` 重新扫描或单独查询 |
| online.devnu11.cn 未捕获 | NODATA 候选未在 massdns 中出现 | 已知行为，E-0010 已记录，无需填补 |
