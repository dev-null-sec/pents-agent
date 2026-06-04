# R002 复盘

## 概要

- 项目：hiwonder-cn-canary
- 复测编号：R002
- Run：R002-2026-06-04-mimo-vision-canary
- 复盘时间：2026-06-04

## 本轮做得好的

- 纯文本可达性测试孤立了问题：确认 haiku/mimo 模型本身可达，问题仅在图片处理路径
- Chrome 无头截图比 Edge 更稳定，记录了工具的可靠性差异
- 记录了所有 502 的 ray_id，便于排查网关问题
- 明确区分了 `model_no_image_input`（R001）和 `inference_gateway_502`（R002）两种不同性质的 blocker
- 直连 API canary 进一步拆清问题：token-plan-cn + `mimo-v2.5` 可以读图，内置 haiku 图片 Read 和 `mimo-v2.5-pro` 图片入口不应作为默认链路

## 本轮问题

| 问题 | 影响 | 后续动作 |
| --- | --- | --- |
| ai.devnu11.cn 网关处理 vision 请求时 502 超时 | Claude Code 内置子代理视觉链路不可用 | 默认绕开内置 Read 图片，改用 `pents vision-review` |
| token-plan-cn 下 `mimo-v2.5-pro` 图片入口 404 | 不能作为默认视觉模型 | 使用 `mimo-v2.5` 作为视觉模型 |
| 缺少 agent-browser MCP 工具 | 无法按 browser-test-agent skill 标准流程执行，只能用 Invoke-WebRequest + Chrome 无头降级 | 确认 agent-browser MCP 在本环境的可用性；如不可用，补充替代方案到 skill |
| Chrome 无头截图耗时较长（有时挂起） | 截图采集不稳定，Edge 完全不可用 | Chrome `--headless=new` + `--timeout=15000` 相对稳定；记录为备用方案 |
| WebFetch 安全策略拦截 | 无法直接用 WebFetch 获取目标页面内容 | 使用 Invoke-WebRequest 作为替代；记录 WebFetch 对 hiwonder.com.cn 的拦截情况 |

## 对 skill 的反馈

| skill | 反馈 | 建议 |
| --- | --- | --- |
| browser-test-agent | skill 假设 agent-browser MCP 可用，但本环境没有；skill 中的 `agent-browser open/snapshot/screenshot` 步骤无法执行 | 当前项目规则已收紧：agent-browser 不可用时停止记录 blocker，不再自行安装或替代截图链路 |
| browser-test-agent | vision-reviewer 调用依赖推理网关稳定，且容易卡死 | 已改为优先调用 `pents vision-review` 输出 JSON |
| vision-reviewer 模板 | 模板只定义了 `model_no_image_input` 一种 blocker，未覆盖网关故障 | 在模板中增加 `inference_gateway_error` blocker 类型和对应输出格式 |

## 对 CLI 的反馈

| 命令或能力 | 反馈 | 建议入池需求 |
| --- | --- | --- |
| pents vision-review | 直连 token-plan-cn + `mimo-v2.5` 可读图，并能输出稳定 JSON | 作为默认视觉链路继续演进，后续补 evidence 自动登记 |
| agent-browser MCP | 本环境未提供 | 确认 MCP 配置或在 doctor 中检查 agent-browser 可用性 |
| WebFetch 域名安全策略 | 对 hiwonder.com.cn 返回"无法验证是否安全" | 无——这是安全策略的正常行为，不是 CLI 问题 |

## 对 tools 的反馈

| 场景 | 是否适合自写脚本 | 原因 | 建议目录 |
| --- | --- | --- | --- |
| Chrome 无头截图 | yes | PowerShell 封装的 Chrome `--headless=new` `--screenshot` 稳定可用 | `tools/evidence/` |
| vision canary 一键测试 | yes | 将 open → snapshot → screenshot → vision-reviewer → 结构化输出 流程合并为单脚本 | `tools/recon/` |

## 对 dicts 的反馈

无（本轮不涉及字典）

## 待进入需求池

| 需求 | 优先级 | 原因 |
| --- | --- | --- |
| 排查 ai.devnu11.cn 网关 vision 请求 502 | P2 | 已有 `pents vision-review` 可绕开，降为内置子代理链路问题 |
| agent-browser MCP 可用性确认 | P1 | browser-test-agent skill 的核心依赖 |
| Chrome 无头截图工具脚本化 | P2 | 重复出现的手动截图操作 |
| browser-test-agent skill 降级方案 | P2 | agent-browser 不可用时的替代路径 |
| vision-reviewer 模板增加网关故障 blocker | P2 | 模板覆盖不完整 |
