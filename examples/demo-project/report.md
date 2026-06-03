# 测试报告

## 元数据

- 项目：demo-project
- 目标：`*.example.test`
- 报告时间：2026-06-03 18:45:00
- 测试者：demo-agent
- 范围文件：scope.md

## 执行摘要

本报告展示 Pentest Framework 的示例报告结构。所有目标均为保留域名，未执行真实扫描或漏洞利用。

## 范围摘要

- 授权内：`*.example.test`、`app.example.test`、`api.example.test`
- 授权外：源站 IP 直连、端口扫描、DoS、社会工程学、真实第三方资产
- 速率：每秒 1 请求

## 漏洞汇总

| 编号 | 标题 | 严重程度 | 状态 | 证据 |
| --- | --- | --- | --- | --- |
| F-0001 | 示例调试接口暴露候选 | Low | candidate | `E-0003`, `E-0004` |

## 严重程度统计

| 严重程度 | 数量 |
| --- | --- |
| Low | 1 |

## 证据与缺口

| Finding | 状态 | 证据 | 缺口 |
| --- | --- | --- | --- |
| F-0001 | candidate | `E-0003`, `E-0004` | 未执行真实 HTTP 验证；E-0004 证据链不完整 |

## 结论

demo-project 展示了从 scope 到 inventory、evidence、finding、report 和 review 的完整记录方式。候选 finding 必须保留 candidate 状态，直到获得真实证据。
