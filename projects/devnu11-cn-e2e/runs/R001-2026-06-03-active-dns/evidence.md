# 证据索引

## 元数据

- 项目：devnu11-cn-e2e
- 更新时间：2026-06-03 15:48:00

## 证据列表

备注建议记录结构化证据链字段：`source_url=...; headers=...; file=...; sha256=...; collected_at=...; chain=complete/incomplete`。漏洞记录和报告引用证据时使用证据编号。

| 编号 | 类型 | 关联目标 | 关联漏洞 | 路径或引用 | 备注 |
| --- | --- | --- | --- | --- | --- |
| E-0001 | 备注 |  |  | progress.md | 项目初始化 |
| E-0009 | active-dns | `*.devnu11.cn` | — | `raw/dnsx-active-dns.jsonl` | 主字典完整扫描结果；167377 词条，约 99.363 秒，命中 5 条；SHA256 `259f3b1a4224afa7b7f52192ec3b3a19520a8519b825c0e3aa6a5a8f66bee692` |
| E-0010 | dns-record-check | `ai/blog/lk/online/st.devnu11.cn` | — | `raw/dnsx-active-dns-record-check.jsonl` | 命中记录复核；`ai/blog/lk/st` 有 A/AAAA，`online` 为 NOERROR 但无 A/AAAA；SHA256 `a5377ea315897660ef151c8197a7575c5d1731dc1facb16ec6b49b0c8d88aa3b` |

## 请求证据

| 证据编号 | 方法 | URL 或端点 | 请求引用 | 响应引用 | 备注 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## 截图证据

| 证据编号 | 路径 | 关联步骤 | 备注 |
| --- | --- | --- | --- |
|  |  |  |  |

## 终端输出证据

| 证据编号 | 命令摘要 | 输出引用 | 备注 |
| --- | --- | --- | --- |
| E-0009 | dnsx 主字典主动 DNS 枚举 | `raw/dnsx-active-dns.jsonl` | 去掉误用的 `-wd`，使用 `-rcode noerror`；resolver 为 1.1.1.1/1.0.0.1/8.8.8.8/8.8.4.4/9.9.9.9/223.5.5.5/119.29.29.29 |
| E-0010 | dnsx 命中记录 A/AAAA/CNAME 复核 | `raw/dnsx-active-dns-record-check.jsonl` | 对 5 个命中补查记录类型，避免把 NODATA 误读为 Web 入口 |
