# 本轮证据

## 元数据

- 项目：devnu11-cn-e2e
- 复测编号：R003
- Run：R003-2026-06-03-puredns-massdns-retest
- 证据类型：active-dns-massdns-direct
- 采集时间：2026-06-04 11:05:36 ~ 11:06:36 CST

## E-0011：Claude Code 正式主动 DNS 枚举

### 执行摘要

- 执行时间：2026-06-04 11:05:36 ~ 11:06:36 CST
- 引擎：massdns direct
- 脚本：tools/recon/active-dns-massdns.ps1
- 总耗时：60.669 秒
- 字典：dicts/curated/subdomains-main.txt（167,377 词条）
- Resolver：1.1.1.1, 1.0.0.1, 8.8.8.8, 8.8.4.4, 223.5.5.5, 119.29.29.29（6 个全通过自检）
- 记录类型：A
- Hashmap size：10000
- Canary：ai.devnu11.cn（命中）
- NXDOMAIN 检查：nx-20260604110500.devnu11.cn（无命中，无 wildcard）

### 各步骤耗时

| 步骤 | 耗时（秒） | 退出码 |
| --- | ---: | ---: |
| canary_massdns | 0.152 | 0 |
| resolver_1-1-1-1 | 0.268 | 0 |
| resolver_1-0-0-1 | 0.247 | 0 |
| resolver_8-8-8-8 | 0.289 | 0 |
| resolver_8-8-4-4 | 0.401 | 0 |
| resolver_223-5-5-5 | 0.153 | 0 |
| resolver_119-29-29-29 | 0.149 | 0 |
| nxdomain_massdns | 0.135 | 0 |
| generate_candidates | 0.707 | 0 |
| massdns_full_enum | 56.443 | 0 |
| extract_hits | 1.725 | 0 |
| **总计** | **60.669** | **0** |

### 命中列表

| 子域名 | A 记录 |
| --- | --- |
| `ai.devnu11.cn` | 104.21.52.13, 172.67.193.236 |
| `blog.devnu11.cn` | 104.21.52.13, 172.67.193.236 |
| `lk.devnu11.cn` | 104.21.52.13, 172.67.193.236 |
| `st.devnu11.cn` | 104.21.52.13, 172.67.193.236 |

> 全部指向 Cloudflare 代理 IP（104.21.52.13 / 172.67.193.236），与 R001 E-0010 一致。

### 文件清单

| 文件 | 路径 | SHA256 |
| --- | --- | --- |
| 候选列表 | raw/active-dns-candidates.txt | — |
| Massdns 原始输出 | raw/active-dns-massdns.txt | D01BB1956C376EF52A8C66537E5473B9D8A2E0894BA6B89E3FF11E02E59471B0 |
| 命中列表 | raw/active-dns-hits.txt | DAAFF483C47481B0AE21EF9CB1D5BFBB4CB4CE49BF42E4EFC77CBA586B105F26 |
| 执行指标 | outputs/active-dns-metrics.json | — |
| 执行摘要 | outputs/active-dns-summary.json | — |
| 执行计划 | outputs/active-dns-plan.md | — |
