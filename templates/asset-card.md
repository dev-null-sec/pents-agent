# 入口卡片：{{asset_card_title}}

## 元数据

- 入口 ID：{{asset_card_id}}
- 项目：{{project_name}}
- 创建时间：{{created_at}}
- 更新时间：{{updated_at}}
- 授权状态：{{authorization_status}}
- 当前状态：{{asset_status}}

## 入口概览

| 字段 | 内容 |
| --- | --- |
| 入口 URL / 目标 | {{entry_target}} |
| 入口类型 | {{entry_type}} |
| 归属资产 | {{linked_assets}} |
| 存活状态 | {{alive_status}} |
| 需认证 | {{auth_required}} |
| 登录 / 注册 | {{login_register_status}} |
| CDN / WAF | {{cdn_waf}} |

## 关联资产

| 类型 | ID | 值 | 备注 |
| --- | --- | --- | --- |
| Domain |  |  |  |
| Subdomain |  |  |  |
| IP |  |  |  |
| Service |  |  |  |
| App |  |  |  |

## 源站线索

| 字段 | 内容 |
| --- | --- |
| 源站线索状态 | {{origin_clue_status}} |
| 线索来源 | {{origin_clue_source}} |
| 允许验证动作 | {{origin_allowed_validation}} |
| 验证约束 | {{origin_validation_constraints}} |
| 待确认事项 | {{origin_confirmations}} |

## 指纹与技术栈

| 类型 | 值 | 置信度 | 证据 |
| --- | --- | --- | --- |
| framework |  |  |  |
| app |  |  |  |
| cdn-waf |  |  |  |
| server |  |  |  |
| language |  |  |  |

## API / 路径线索

| 方法 | 路径或 URL | 来源 | 需认证 | 备注 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 交互点

| 类型 | 位置 | 状态 | 备注 |
| --- | --- | --- | --- |
| 登录 |  | 未验证 |  |
| 注册 |  | 未验证 |  |
| 搜索 |  | 未验证 |  |
| 上传 |  | 未验证 |  |
| 支付 |  | 未验证 |  |
| OAuth |  | 未验证 |  |
| 管理功能 |  | 未验证 |  |

## 浏览器验证

| 字段 | 内容 |
| --- | --- |
| 执行 run | {{browser_run}} |
| 浏览器会话 | {{browser_session}} |
| 账号角色 | {{browser_account_role}} |
| 首屏截图 | {{browser_first_screenshot}} |
| 关键截图 | {{browser_key_screenshots}} |
| 网络摘要 | {{browser_network_summary}} |
| 状态文件 | {{browser_state_file}} |

### 交互步骤摘要

| 步骤 | 动作 | 等待条件 | 结果 | 证据 |
| --- | --- | --- | --- | --- |
| 1 |  |  |  |  |

## 高价值测试点

| 测试点 | 状态 | 前置条件 | 证据 / 来源 |
| --- | --- | --- | --- |
| setup / install | 候选 |  |  |
| authz / IDOR / BFLA | 候选 | 需要账号 |  |
| 默认配置 | 候选 |  |  |
| 敏感信息 | 候选 |  |  |

## 风险线索

| 编号 | 风险 | 状态 | 关联 finding | 证据 |
| --- | --- | --- | --- | --- |
| RISK-0001 |  | 候选 |  |  |

## 证据

| 证据 ID | 类型 | 路径 / 引用 | 备注 |
| --- | --- | --- | --- |
|  |  |  |  |

## 停止条件

- 目标跳转到范围外资产。
- 出现登录、写入、支付、OAuth 授权或管理员权限要求，且尚未获得对应授权。
- 出现 429、WAF/验证码升级、连续 5xx 或明显业务异常。
- 响应包含敏感数据、凭据、个人信息或生产数据。
- 发现疑似源站 IP，未获用户单独确认前不得直连。

## 下一步

- 建议代理：{{next_agent}}
- 建议 skill：{{next_skill}}
- 建议 run：{{next_run}}
- 待用户确认：{{user_confirmations}}
