# Claude Code 任务卡：T-0042 正式主动 DNS 枚举

## 一句话目标

由 Claude Code 正式执行 `devnu11.cn` 主动 DNS 子域名枚举，并与 R001 Codex 前置验证基线对比。

## 启动方式

先用 ai-board 申领任务：

```powershell
ai-board start T-0042 --agent claude-code --scope projects/devnu11-cn-e2e docs/当前状态.md
```

## 必读

- `docs/计划看板.md`
- `docs/当前状态.md`
- `projects/devnu11-cn-e2e/scope.md`
- `projects/devnu11-cn-e2e/runs/R001-2026-06-03-active-dns/review.md`

## 边界

- 授权范围：`*.devnu11.cn`
- 本轮只做 DNS 子域名枚举和 DNS 记录复核。
- 禁止 HTTP 存活、端口扫描、路径/API 请求、漏洞验证、源站直连。
- R001 是 Codex 前置验证中误执行完整字典形成的对照基线，不是 Claude Code 正式结果。

## 执行要求

1. 先做 canary：
   - `ai.devnu11.cn` 应可解析。
   - 随机 3-5 个不存在子域应为 NXDOMAIN 或不可解析。
   - resolver 必须可用。
2. 泛解析检测和字典枚举分开做。
3. 不要把 dnsx `-wd` 当作正式字典枚举参数。
4. 使用 `dicts/curated/subdomains-main.txt` 完整枚举 `devnu11.cn`。
5. 对命中结果补查 A/AAAA/CNAME，并区分：
   - 有 A/AAAA
   - NOERROR 但无 A/AAAA
   - NXDOMAIN
   - 疑似泛解析噪声

## 可参考参数

R001 前置验证参数仅供参考，Claude Code 可按实际情况调整并记录原因：

- threads=2000
- retry=2
- timeout=2s
- rcode=noerror
- resolver：1.1.1.1、1.0.0.1、8.8.8.8、8.8.4.4、9.9.9.9、223.5.5.5、119.29.29.29

## 回填要求

更新：

- `projects/devnu11-cn-e2e/progress.md`
- `projects/devnu11-cn-e2e/inventory.md`
- `projects/devnu11-cn-e2e/evidence.md`
- `projects/devnu11-cn-e2e/report.md`
- `projects/devnu11-cn-e2e/review.md`
- 必要时创建新的 run 目录，如 `runs/R002-<date>-claude-active-dns/`

必须记录：

- 字典路径和词条数
- resolver
- 并发、retry、timeout
- 耗时
- canary 与泛解析检查结果
- 命中列表和 A/AAAA/CNAME 复核
- 与 R001 Codex 前置验证结果的差异

## 完成

完成后：

```powershell
ai-board complete T-0042 --verification "<写清执行结果和证据>" --leftovers "<遗留问题或无>"
ai-board archive T-0042
```

如果缺工具、缺权限、resolver 不稳定或结果异常，先记录 blocker/复盘，不要扩展到 HTTP 或端口。
