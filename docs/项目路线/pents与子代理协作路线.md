# pents 与子代理协作路线

## 核心定位

`pents` 不只是项目管理 CLI，也不应该变成漏洞扫描器。

它的定位是：给 Claude Code 使用的渗透测试上下文压缩器、证据登记器和子代理协作辅助器。

要减少的是三类浪费：

- 反复读取 scope、目标、禁止动作。
- 多个 agent 重复测试同一入口。
- 报告阶段找不到证据、请求、截图和复现步骤。

## CLI 能力分层

### 1. 管理层

负责项目生命周期和最终交付：

- `pents new`：创建项目目录和基础模板。
- `pents finding`：按模板创建正式漏洞记录。
- `pents report`：汇总 finding 生成报告草稿。
- `pents review`：复盘项目记录，产出 skill 改进建议。

### 2. 提效层

负责把散乱上下文变成 AI 可读的短材料：

- `pents scope`：输出授权范围、目标清单、禁止动作和确认状态。
- `pents brief`：生成给主代理或子代理看的任务简报。
- `pents inventory`：维护 URL、接口、参数、账号、资产和测试面清单。
- `pents note`：追加过程记录和经验笔记。
- `pents evidence`：登记截图、请求包、响应摘要、复现材料和证据路径。
- `pents suggest-skills`：根据目标类型推荐正式 skill 或 `refer/xalgorix/` 原始资料路径。

### 3. 协作层

负责子代理之间的边界和结果合并：

- `pents tasks`：维护测试子任务和分配状态。
- `pents brief --agent <role>`：为指定子代理生成窄任务卡。
- `pents merge`：合并子代理输出，去重并标记候选 finding。
- `pents review-agent-output`：检查子代理结果是否越界、重复、证据不足或误报风险高。

## 子代理协作模式

### 主代理：Test Lead

主代理负责完整上下文和最终判断：

- 读取 `scope.md`，确认授权范围和禁止动作。
- 建立 inventory，拆分测试面。
- 给子代理生成窄任务卡。
- 审核子代理输出。
- 只有主代理写正式 finding。
- 负责最终 report 和 review。

### 子代理：专业工位

子代理只处理被分配的窄范围，不擅自扩大目标：

- Recon Agent：资产、入口、技术栈、URL、API、参数清单。
- Web Surface Agent：页面、表单、参数、状态变化点。
- API Agent：接口鉴权、对象权限、参数污染、速率限制。
- Auth Agent：登录、注册、找回密码、会话、OAuth/OIDC。
- Evidence Agent：整理请求/响应、截图、复现步骤、证据引用。
- Report Agent：把已确认 finding 变成报告草稿。
- Review Agent：复盘遗漏、重复、证据不足、scope 风险和 skill 改进点。

## 子代理任务卡

每个子代理只应拿到最小必要信息：

- 授权范围摘要。
- 当前目标子集。
- 禁止动作。
- 测试面和停止条件。
- 可参考的正式 skill 或原始资料路径。
- 输出格式。
- 证据要求。

子代理输出必须结构化。当前 `pents merge` 和 `pents review-agent-output` 支持 JSON 文件，或 Markdown 文档中的 fenced JSON：

```json
{
  "agent_role": "api-agent",
  "tested_targets": [
    {
      "url": "",
      "method": "GET",
      "surface": "API",
      "result": "",
      "evidence_refs": []
    }
  ],
  "potential_findings": [
    {
      "title": "",
      "reason": "",
      "evidence_refs": []
    }
  ],
  "confirmed_findings": [
    {
      "title": "",
      "severity": "",
      "evidence_refs": []
    }
  ],
  "blocked_or_skipped": [
    {
      "target": "",
      "reason": "",
      "reason_type": "其他",
      "status": "skipped"
    }
  ],
  "recommended_next": [""],
  "scope_risk": [
    {
      "target": "",
      "reason": ""
    }
  ]
}
```

## 推荐流程

1. 主代理执行 `pents scope`，确认授权边界。
2. 主代理执行 `pents inventory`，整理目标和测试面。
3. 主代理执行 `pents brief --agent recon`，启动 Recon Agent。
4. Recon Agent 输出资产、URL、API、参数和认证入口。
5. 主代理执行 `pents merge <project> <agent-output.json>`，合并 recon 输出到 inventory/progress。
6. 主代理按测试面生成 Web/API/Auth 子任务。
7. 子代理并行测试，输出候选 finding 和证据引用。
8. 主代理执行 `pents review-agent-output <project> <agent-output.json>`，检查越界、重复和证据缺口。
9. 主代理确认漏洞后执行 `pents finding` 创建正式记录。
10. 主代理执行 `pents report` 生成报告草稿。
11. 主代理执行 `pents review`，沉淀 skill 改进建议。

## 边界

- `pents` 不内置扫描器。
- `pents` 不自动执行 exploit。
- `pents` 不替主代理做漏洞真实性判断。
- 子代理不能扩大授权范围。
- 子代理不能直接写正式 finding，除非后续明确改变规则。
- 高风险动作必须由主代理和用户确认。
