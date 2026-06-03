# 项目复盘

## 元数据

- 项目：demo-project
- 复盘时间：2026-06-03 18:50:00
- 复盘人：demo-agent

## 做得好的

- scope、inventory、evidence、finding、report、review 之间有可追踪引用。
- R001 run 单独记录本轮主动 DNS 计划，顶层文档只保留累计事实。
- 候选 finding 没有被写成 confirmed。

## 做得不好的

- demo 没有真实响应，因此无法展示 confirmed finding 的完整证据链。

## 遗漏或覆盖不足

| 领域 | 原因 | 后续跟进 |
| --- | --- | --- |
| HTTP 低频探测 | demo 不执行真实请求 | 在授权靶场中补充确认型示例 |
| 字典回灌 | 未产生真实新词条 | 等实战 run 后补充 candidates 示例 |

## 跳过 / 阻塞复盘

| 测试面 | 原因类型 | 已尝试来源 / 替代动作 | 未执行项 | 影响 | 建议安装工具 | 需要用户补充 | 后续跟进 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 源站验证 | 授权缺失 | DNS 线索记录 | 源站直连 | 无法确认源站 | 无 | 源站授权 | 不在 demo 中执行 |
| 端口扫描 | 范围外 | scope 检查 | 端口探测 | 不影响 demo | 无 | 无 | 保持禁止 |

## 武器库反馈

| 技能或主题 | 保留 | 改进 | 原因 |
| --- | --- | --- | --- |
| subdomain-enumeration | 是 | 保持 canary/NXDOMAIN/resolver 自检 | 防止主动 DNS 误判 |
| javascript-analysis | 是 | 示例中展示 API 线索提取 | 便于发现候选端点 |

## 候选新技能

| 候选名称 | 来源证据 | 优先级 |
| --- | --- | --- |
| 无 | demo 未产生真实新技能需求 | P3 |

## CLI 或模板反馈

- `pents brief` 适合把短指令转成任务卡。
- `pents active-dns` 适合生成主动 DNS 计划，不默认执行真实扫描。

## 行动项

| 事项 | 负责人 | 优先级 |
| --- | --- | --- |
| 后续补充 confirmed finding 示例 | codex | P2 |
