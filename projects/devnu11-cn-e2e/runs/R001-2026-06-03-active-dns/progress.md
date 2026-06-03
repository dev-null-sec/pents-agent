# 本轮测试进度

## 概要

- 项目：devnu11-cn-e2e
- 复测编号：R001
- Run：R001-2026-06-03-active-dns
- 当前阶段：done
- 执行主体：Codex（按用户本轮“现在就跑”授权执行 DNS 枚举）
- 更新时间：2026-06-03 15:48:00

## 本轮目标

- 对 `devnu11.cn` 执行主动 DNS 子域名字典枚举。
- 使用 `dicts/curated/subdomains-main.txt` 完整跑完主字典，控制在 5 分钟内。
- 记录 resolver、并发、耗时、泛解析检查、命中结果和证据链。

## 时间线

| 时间 | 执行者 | 动作 | 结果 | 证据引用 |
| --- | --- | --- | --- | --- |
| 2026-06-03 15:41 | Codex | 最小链路复核 | `ai.devnu11.cn` 可通过系统解析和 dnsx 解析；确认此前 0 命中不可信 | E-0009 |
| 2026-06-03 15:42 | Codex | 泛解析噪声检查 | 5 个随机子域均返回 NXDOMAIN；未发现 DNS 泛解析噪声 | E-0009 |
| 2026-06-03 15:43 | Codex | 主字典主动 DNS 枚举 | `subdomains-main.txt` 167377 词条跑完，耗时约 99.363 秒，命中 5 条 | E-0009 |
| 2026-06-03 15:47 | Codex | 命中记录复核 | `ai/blog/lk/st` 有 A/AAAA，`online` 为 NOERROR 但无 A/AAAA | E-0010 |

## 已执行项

| 目标 | 测试面 | 方法 | 结果 | 证据引用 | 是否需要合并到顶层 |
| --- | --- | --- | --- | --- | --- |
| `*.devnu11.cn` | 主动 DNS 子域名枚举 | dnsx + `dicts/curated/subdomains-main.txt`，resolver 混合公共 DNS，threads=2000，retry=2，timeout=2s，`rcode=noerror` | 命中 `ai/blog/lk/online/st` 5 条；完整字典耗时约 99.363 秒 | E-0009 | yes |
| `ai/blog/lk/online/st.devnu11.cn` | DNS 记录复核 | dnsx 查询 A/AAAA/CNAME | `ai/blog/lk/st` 指向 Cloudflare A/AAAA；`online` 无 A/AAAA，暂记 NODATA | E-0010 | yes |

## 跳过 / 阻塞项

原因类型可选：授权缺失、工具缺失、目标无输入、网络失败、风险过高、范围外、等待账号、其他。

| 目标 | 测试面 | 状态 | 原因类型 | 具体原因 | 已尝试来源 / 替代动作 | 影响 | 需要用户补充 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 候选子域名 | HTTP 存活 / CDN / 服务指纹 | blocker | 授权缺失 | 本轮只授权并执行 DNS 枚举；未确认 HTTP 请求速率和窗口 | 已完成 DNS 记录复核 | 不能确认 Web 是否存活、响应头、证书和跳转链 | 是否允许对 `ai/blog/lk/st` 做低频 HTTP 探测；HTTP 请求速率和窗口 |
| 候选子域名 | 端口确认 | blocker | 授权缺失 / 风险过高 | 未确认端口范围和速率，不能从 DNS 命中自动扩展到端口扫描 | 仅记录 Cloudflare A/AAAA | 不能确认 80/443/8080/8443 等入口暴露 | 端口范围、允许速率、授权窗口 |

## 本轮待归并

| 顶层文件 | 是否需要更新 | 原因 |
| --- | --- | --- |
| inventory.md | yes | 新增 5 个 DNS 命中和 Cloudflare A/AAAA 记录 |
| evidence.md | yes | 新增 E-0009/E-0010 |
| findings/ | no | 本轮只做 DNS 枚举，不确认漏洞 |
| report.md | yes | 修正“未主动 DNS 枚举”的限制，加入主动 DNS 结果 |
| review.md | yes | 记录 `-wd` 误用、预检缺口和后续需求建议 |
