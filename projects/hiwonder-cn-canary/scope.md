# 测试范围

## 项目信息

- 项目名称：hiwonder-cn-canary
- 负责人：user
- 创建时间：2026-06-04
- 状态：仅执行视觉 canary 验证，不做漏洞测试

## 授权信息

- 授权来源：T-0056 任务卡，用户确认允许对公开页面执行仅浏览/截图/视觉识别 canary
- 授权人：用户
- 授权窗口：2026-06-04 单次会话
- 紧急联系人：当前用户

## 测试范围

| 类型 | 目标 | 备注 |
| --- | --- | --- |
| 浏览器视觉 canary | `https://www.hiwonder.com.cn/admin_hiwonder.php/` | 仅打开公开页面、snapshot、截图、视觉识别链路验证 |

## 不在范围内

| 目标或动作 | 原因 |
| --- | --- |
| 登录、注册、提交表单 | 未授权，本次只做视觉 canary |
| 绕过验证码、绕过风控 | 禁止 |
| 漏洞 payload、暴力破解 | 禁止 |
| 目录/API 大字典枚举 | 禁止 |
| 非 hiwonder.com.cn 的第三方资产 | 未授权 |

## 允许的操作

- 使用 agent-browser 打开公开目标 URL
- 执行 agent-browser snapshot
- 保存页面截图
- 调用 vision-reviewer 子代理进行视觉识别（如果需要）
- 记录 run 过程和结构化结果

## 禁止的操作

- 输入账号密码、提交表单
- 绕过验证码或风控
- 漏洞 payload 扫描
- 越权访问

## 速率限制

- 仅 1 个 URL、1 次打开、1-2 次截图，无速率压力
- 如遇 WAF/429/403，立即停止

## 确认

- 测试者已审阅范围：是
- 已与用户确认范围：是（T-0056 任务卡已明确授权边界）
- 备注：本任务是 T-0056 的视觉 canary 验证，目的是验证 Claude Code + agent-browser + vision-reviewer fallback 链路是否正常工作
