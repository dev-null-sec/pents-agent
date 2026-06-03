# 本轮报告增量（R001）

## 概要

- 项目：devnu11-cn-e2e
- 复测编号：R001
- Run：R001-2026-06-03-active-dns
- 生成时间：2026-06-03 15:36:05

## 本轮结论变化

| 类型 | 内容 | 证据引用 | 是否合并到总报告 |
| --- | --- | --- | --- |
| 新增 | Codex 前置链路验证中误执行完整主动 DNS：`dicts/curated/subdomains-main.txt` 167377 词条完整跑完，耗时约 99.363 秒，命中 `ai.devnu11.cn`、`blog.devnu11.cn`、`lk.devnu11.cn`、`online.devnu11.cn`、`st.devnu11.cn`；不替代 Claude Code 正式执行 | E-0009 | yes |
| 修正 | 之前“0 命中”是扫描链路错误：dnsx `-wd` 会进入泛解析过滤模式，未真正执行字典暴力枚举 | E-0009 | yes |
| 待确认 | `online.devnu11.cn` 为 NOERROR 但无 A/AAAA，暂不作为可访问 Web 入口；`ai/blog/lk/st` 指向 Cloudflare A/AAAA，但未做 HTTP 探测 | E-0010 | yes |

## 新增资产或攻击面

- `ai.devnu11.cn`：DNS A/AAAA 已确认，Cloudflare IP。
- `blog.devnu11.cn`：DNS A/AAAA 已确认，Cloudflare IP。
- `lk.devnu11.cn`：DNS A/AAAA 已确认，Cloudflare IP。
- `st.devnu11.cn`：DNS A/AAAA 已确认，Cloudflare IP。
- `online.devnu11.cn`：NOERROR/NODATA 候选，无 A/AAAA。

## 新增或状态变化的漏洞

| 编号 | 标题 | 原状态 | 新状态 | 证据引用 |
| --- | --- | --- | --- | --- |
| F-0001 | 安装向导端点暴露 | 待确认 | 待确认 | E-0004；本轮未执行 HTTP/API 验证 |

## 仍然阻塞的测试面

| 测试面 | 原因类型 | 影响 | 需要用户补充 |
| --- | --- | --- | --- |
| HTTP 存活 / CDN / 服务指纹 | 授权缺失 | 不能确认 `ai/blog/lk/st` 是否为真实 Web 入口、响应头、证书和跳转链 | 是否允许低频 HTTP 探测；请求速率和授权窗口 |
| 端口确认 | 授权缺失 / 风险过高 | 不能确认候选子域名的端口暴露情况 | 端口范围、允许速率和授权窗口 |
| API / 认证后测试 | 等待账号 / 授权缺失 | F-0001 与管理后台 API 风险仍无法验证 | 实际 URL、普通测试账号、管理员账号授权或注册许可 |

## 建议合并到总报告的段落

```md
R001 是 Codex 前置链路验证中误执行完整主动 DNS 的事实记录，不替代 Claude Code 正式执行。使用 `dicts/curated/subdomains-main.txt`（167377 词条）对 `devnu11.cn` 执行 dnsx 枚举，threads=2000、retry=2、timeout=2s、`rcode=noerror`，resolver 为 1.1.1.1/1.0.0.1/8.8.8.8/8.8.4.4/9.9.9.9/223.5.5.5/119.29.29.29。完整扫描耗时约 99.363 秒，命中 5 个 DNS 名称：`ai.devnu11.cn`、`blog.devnu11.cn`、`lk.devnu11.cn`、`online.devnu11.cn`、`st.devnu11.cn`。其中 `ai/blog/lk/st` 有 Cloudflare A/AAAA 记录，`online` 为 NOERROR 但无 A/AAAA，暂记为 NODATA 候选。本轮未执行 HTTP 存活、端口、路径/API 或漏洞验证；Claude Code 正式主动 DNS 执行仍待 T-0042。

```
