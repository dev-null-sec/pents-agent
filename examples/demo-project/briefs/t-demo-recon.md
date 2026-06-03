# 代理任务卡

## 任务分配

- 项目：demo-project
- 代理角色：recon
- 创建时间：2026-06-03 18:30:00
- 任务编号：T-DEMO-RECON
- 用户短指令：对 `*.example.test` 做信息收集，别碰端口扫描和源站直连。

## 授权范围摘要

### 测试范围内

- `*.example.test` DNS 子域名枚举
- `app.example.test` 与 `api.example.test` 示例入口记录

### 不在范围内

- 源站 IP 直连
- 端口扫描
- 真实第三方资产

### 禁止动作

- DoS
- 社会工程学
- 凭据填充
- 破坏性操作

### 停止条件

- canary 未命中
- 随机 NXDOMAIN 命中 wildcard
- 需要扩大到范围外目标

## 目标子集

| 目标 | 测试面 | 备注 |
| --- | --- | --- |
| `*.example.test` | 主动 DNS | 只生成计划，不执行真实扫描 |
| `app.example.test` | Web 入口 | 低频 HTTP 授权后再探测 |

## 任务目标

生成 R001 信息收集记录，展示主动 DNS 计划、JS 静态线索和候选 finding 的记录方式。

## 输入缺口

- 真实 HTTP 授权缺失
- 真实 canary 子域名缺失，demo 使用 `app.example.test`

## 参考资料建议

| 类型 | 路径 | 备注 |
| --- | --- | --- |
| skill | skills/recon/subdomain-enumeration/SKILL.md | 主动 DNS checklist |
| cli | docs/项目路线/主动DNS执行封装.md | active-dns 计划生成 |

## 验收标准

- 有 run 级 brief/progress/evidence/report-delta/review。
- 有主动 DNS 计划样例。
- finding 保持 candidate，说明证据缺口。

## 回填文件

- inventory.md
- evidence.md
- progress.md
- report.md
- review.md

## 完成与归档要求

- 更新 run 级文档。
- 将累计事实回填顶层文档。
- ai-board complete/archive 对应任务。

## 输出要求

返回结构化输出，必须包含：

- 已测试目标
- 候选漏洞
- 已确认漏洞
- 证据引用
- 阻塞或跳过项
- 建议下一步
- 范围风险

## 证据要求

- 有意义的请求和响应需记录引用。
- 有意义的截图或终端输出需记录路径。
- 没有可复现证据时，不得声称漏洞已确认。
