# 资产清单

## 元数据

- 项目：demo-project
- 更新时间：2026-06-03 18:40:00

## 资产

| 编号 | 类型 | 目标 | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| A-0001 | dns | `*.example.test` | 已授权 | 示例泛域名 |
| A-0002 | web | `https://app.example.test` | 待确认 | 示例 Web 入口 |
| A-0003 | api | `https://api.example.test` | 待确认 | 示例 API 入口 |

## URL 列表

| 编号 | URL | 方法 | 需认证 | 备注 |
| --- | --- | --- | --- | --- |
| U-0001 | `https://app.example.test/login` | GET | 否 | 示例登录页 |
| U-0002 | `https://app.example.test/dashboard` | GET | 是 | 示例登录后页面 |

## API 端点

| 编号 | 方法 | 端点 | 需认证 | 参数 | 备注 |
| --- | --- | --- | --- | --- | --- |
| API-0001 | GET | `/api/v1/status` | 否 | 无 | 示例健康检查 |
| API-0002 | GET | `/api/v1/users/me` | 是 | `id` | 示例用户信息接口 |
| API-0003 | GET | `/api/v1/debug/status` | 未知 | 无 | 进入 candidate finding |

## 参数清单

| 编号 | 位置 | 参数名 | 来源 | 备注 |
| --- | --- | --- | --- | --- |
| P-0001 | query | `redirect_uri` | JS 静态分析 | OAuth 场景待确认 |
| P-0002 | query | `state` | JS 静态分析 | OAuth 场景待确认 |
| P-0003 | query | `id` | API 清单 | BOLA 场景待确认 |

## 账号

| 编号 | 角色 | 用户名 | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| ACC-0001 | demo-user | `demo-user@example.test` | 示例 | 不是真实凭据 |

## 测试面

| 编号 | 测试面 | 负责代理 | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| S-0001 | 子域名枚举 | Recon Agent | 已计划 | 见 R001 active-dns-plan |
| S-0002 | API 鉴权 | API Agent | 待确认 | 需要低频 HTTP 授权 |
| S-0003 | OAuth 配置 | Auth Agent | 待确认 | 需要登录流程授权 |
