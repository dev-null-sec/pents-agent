# 资产清单

## 元数据

- 项目：devnu11-cn-e2e
- 更新时间：2026-06-03
- 分析来源：前端 JS 静态分析（js_files/），被动子域名枚举（5 个来源全部无结果），主动 DNS 主字典枚举（2026-06-03）

## 资产

| 编号 | 类型 | 目标 | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| A-0001 | web/api | `*.devnu11.cn` | in-scope | 用户声明自有域名和服务器，允许授权测试 |
| A-0002 | web/app | AI API 代理/中转平台（SPA） | identified | 前端 SPA，Vue 3.5.26 + Axios + Vue i18n |
| A-0003 | dns | `*.devnu11.cn` | active-dns-results | 5 个被动来源复查全部无结果；主动主字典枚举命中 5 条（见 E-0009/E-0010） |
| A-0004 | software | Sub2API（开源 AI API 代理平台） | identified | GitHub: Wei-Shaw/sub2api；Go + Vue 3 + PostgreSQL + Redis；demo.sub2api.org |
| A-0005 | cdn/waf | Cloudflare（推测） | clue | 前端 JS 含 Cloudflare Turnstile 集成；被动来源无结果可能因 Cloudflare 泛解析遮挡 |
| A-0006 | dns | `ai.devnu11.cn` | resolved | A/AAAA 指向 Cloudflare IP：104.21.52.13、172.67.193.236、2606:4700:3030::ac43:c1ec、2606:4700:3036::6815:340d |
| A-0007 | dns | `blog.devnu11.cn` | resolved | A/AAAA 指向 Cloudflare IP：104.21.52.13、172.67.193.236、2606:4700:3030::ac43:c1ec、2606:4700:3036::6815:340d |
| A-0008 | dns | `lk.devnu11.cn` | resolved | A/AAAA 指向 Cloudflare IP：104.21.52.13、172.67.193.236、2606:4700:3030::ac43:c1ec、2606:4700:3036::6815:340d |
| A-0009 | dns | `st.devnu11.cn` | resolved | A/AAAA 指向 Cloudflare IP：104.21.52.13、172.67.193.236、2606:4700:3030::ac43:c1ec、2606:4700:3036::6815:340d |
| A-0010 | dns | `online.devnu11.cn` | nodata-candidate | NOERROR 但无 A/AAAA，暂不作为 Web 入口 |

## Recon 基本盘补强清单

| 检查项 | 当前状态 | 下一步 | 记录位置 |
| --- | --- | --- | --- |
| 子域名发现 | ✅ 被动与主动 DNS 均完成 | 后续根据 HTTP 授权对候选入口做低频存活确认 | E-0007, E-0008, E-0009 |
| DNS 解析 | ✅ 候选子域名已复核 | `ai/blog/lk/st` 有 Cloudflare A/AAAA；`online` 为 NODATA 候选 | E-0010 |
| 端口确认 | ⛔ blocker：需 URL+窗口+速率 | 确认后只做 80/443/8080/8443 | 本文件”端口与服务指纹记录模板” |
| CDN/WAF 判断 | ✅ 被动部分完成 | 已发现 Cloudflare Turnstile 线索；DNS 解析后可确认 | A-0005, E-0004 |
| 源站线索 | ✅ 被动部分完成 | Sub2API 开源项目 GitHub/GitHub Pages 属于第三方，不探测 | 本文件”源站线索记录模板” |
| 服务指纹 | ✅ 软件识别完成 | 已确认 Sub2API + Go + Vue 3 + PostgreSQL + Redis | A-0004, E-0007 |

### 子域名发现 — 被动来源汇总

| 来源 | 类型 | 采集时间 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| crt.sh | CT 证书透明 | 2026-06-02 | 空 | 两次查询均无记录 |
| urlscan.io | URL 扫描归档 | 2026-06-02 | 空 | API 返回 total:0 |
| Wayback Machine | 网页历史归档 | 2026-06-02 | 空 | `*.devnu11.cn` 无归档 |
| AlienVault OTX | 被动 DNS / 威胁情报 | 2026-06-02 | 需认证 | 匿名访问受限 |
| Google 搜索 | 搜索引擎收录 | 2026-06-02 | 空 | `site:devnu11.cn` 无结果 |

> 结论：所有被动来源均无子域名记录，但主动主字典枚举已命中 5 个 DNS 名称。被动全空不能作为“不存在子域名”的判断依据。

### 子域名发现 — 主动字典枚举

| 来源 | 类型 | 采集时间 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| dnsx + `dicts/curated/subdomains-main.txt` | 主动 DNS 字典枚举 | 2026-06-03 | 命中 5 条 | 字典 167377 词条，约 99.363 秒；E-0009 |

| 子域名 | DNS 状态 | A/AAAA | 初步判断 | 证据 |
| --- | --- | --- | --- | --- |
| `ai.devnu11.cn` | NOERROR | 有 | Cloudflare 代理入口候选 | E-0010 |
| `blog.devnu11.cn` | NOERROR | 有 | Cloudflare 代理入口候选 | E-0010 |
| `lk.devnu11.cn` | NOERROR | 有 | Cloudflare 代理入口候选 | E-0010 |
| `st.devnu11.cn` | NOERROR | 有 | Cloudflare 代理入口候选 | E-0010 |
| `online.devnu11.cn` | NOERROR | 无 | NODATA 候选，暂不作为 Web 入口 | E-0010 |

### DNS / CDN 线索记录

| 线索 | 来源 | 可信度 | 判断 | 备注 |
| --- | --- | --- | --- | --- |
| Cloudflare Turnstile 集成 | index.js `turnstile_site_key` | 较可能 | 站点可能使用 Cloudflare 代理 | 需 DNS CNAME 解析确认 |
| 多个候选子域名指向 Cloudflare IP | E-0010 | 确认 | `ai/blog/lk/st` A/AAAA 指向 104.21.52.13、172.67.193.236 及对应 IPv6 | 还需 HTTP 响应头/证书确认具体入口 |

### 源站线索记录

| 线索 | 来源 | 可信度 | 是否已确认授权 | 处理建议 |
| --- | --- | --- | --- | --- |
| Sub2API GitHub 仓库 | WebSearch (github.com/Wei-Shaw/sub2api) | 确认 | 第三方 | 开源项目本身属于第三方资产，不探测。仅用其文档理解默认配置和攻击面。 |
| demo.sub2api.org | WebSearch | 确认 | 第三方 | 官方演示站，不在授权范围，不探测。 |

## 技术栈

| 组件 | 版本/信息 | 来源 |
| --- | --- | --- |
| Vue | 3.5.26 | vendor-vue-BRjbeJGJ.js |
| Axios | — | vendor-misc-T69nC9V6.js |
| Vue i18n | — | vendor-i18n-BZoxDmZq.js |
| 前端构建 | Vite (推测) | 文件名含 hash（DG7INg5y、BZoxDmZq 等） |

## URL 列表（前端路由）

| 编号 | URL | 方法 | 需认证 | 备注 |
| --- | --- | --- | --- | --- |
| U-001 | `/login` | GET | 否 | 登录页 |
| U-002 | `/register` | GET | 否 | 注册页 |
| U-003 | `/email-verify` | GET | 待确认 | 邮箱验证页 |
| U-004 | `/forgot-password` | GET | 否 | 忘记密码 |
| U-005 | `/reset-password` | GET | 待确认 | 重置密码（需 token） |
| U-006 | `/auth/callback` | GET | 待确认 | OAuth 通用回调 |
| U-007 | `/auth/oauth/callback` | GET | 待确认 | OAuth 回调 |
| U-008 | `/auth/linuxdo/callback` | GET | 待确认 | LinuxDo OAuth 回调 |
| U-009 | `/auth/wechat/callback` | GET | 待确认 | 微信 OAuth 回调 |
| U-010 | `/auth/wechat/payment/callback` | GET | 待确认 | 微信支付回调 |
| U-011 | `/auth/dingtalk/callback` | GET | 待确认 | 钉钉 OAuth 回调 |
| U-012 | `/auth/dingtalk/email-completion` | GET | 待确认 | 钉钉邮箱补全 |
| U-013 | `/auth/oidc/callback` | GET | 待确认 | OIDC 回调 |
| U-014 | `/home` | GET | 需认证 | 用户首页 |
| U-015 | `/dashboard` | GET | 需认证 | 用户仪表盘 |
| U-016 | `/keys` | GET | 需认证 | API Key 管理 |
| U-017 | `/usage` | GET | 需认证 | 用量查询 |
| U-018 | `/key-usage` | GET | 需认证 | Key 用量详情 |
| U-019 | `/redeem` | GET | 需认证 | 兑换码 |
| U-020 | `/affiliate` | GET | 需认证 | 推广联盟 |
| U-021 | `/available-channels` | GET | 需认证 | 可用渠道 |
| U-022 | `/profile` | GET | 需认证 | 个人设置 |
| U-023 | `/subscriptions` | GET | 需认证 | 订阅管理 |
| U-024 | `/purchase` | GET | 需认证 | 购买页 |
| U-025 | `/orders` | GET | 需认证 | 订单记录 |
| U-026 | `/payment/qrcode` | GET | 需认证 | 二维码支付 |
| U-027 | `/payment/result` | GET | 需认证 | 支付结果 |
| U-028 | `/payment/stripe` | GET | 需认证 | Stripe 支付 |
| U-029 | `/payment/airwallex` | GET | 需认证 | Airwallex 支付 |
| U-030 | `/payment/stripe-popup` | GET | 需认证 | Stripe 弹窗支付 |
| U-031 | `/setup` | GET | 待确认 | 安装向导（post-install setup） |
| U-032 | `/admin` | GET | 需管理权限 | 管理后台入口 |
| U-033 | `/admin/dashboard` | GET | 需管理权限 | 管理仪表盘 |
| U-034 | `/admin/users` | GET | 需管理权限 | 用户管理 |
| U-035 | `/admin/groups` | GET | 需管理权限 | 分组管理 |
| U-036 | `/admin/accounts` | GET | 需管理权限 | 账号管理 |
| U-037 | `/admin/channels` | GET | 需管理权限 | 渠道管理 |
| U-038 | `/admin/channels/pricing` | GET | 需管理权限 | 渠道定价 |
| U-039 | `/admin/channels/monitor` | GET | 需管理权限 | 渠道监控 |
| U-040 | `/admin/ops` | GET | 需管理权限 | 运维面板 |
| U-041 | `/admin/subscriptions` | GET | 需管理权限 | 订阅管理 |
| U-042 | `/admin/redeem` | GET | 需管理权限 | 兑换码管理 |

## API 端点

### 认证 API（`/api/v1/auth/`）

| 编号 | 方法 | 端点 | 需认证 | 参数 | 备注 |
| --- | --- | --- | --- | --- | --- |
| API-001 | POST | `/api/v1/auth/login` | 否 | username, password | 登录 |
| API-002 | POST | `/api/v1/auth/login/2fa` | 否 | code, session_token | 两步验证 |
| API-003 | POST | `/api/v1/auth/register` | 否 | email, username, password | 注册 |
| API-004 | GET | `/api/v1/auth/me` | 是 | — | 当前用户信息 |
| API-005 | POST | `/api/v1/auth/logout` | 是 | — | 登出 |
| API-006 | POST | `/api/v1/auth/oauth/bind-token` | 待确认 | provider, code | OAuth 绑定 |
| API-007 | POST | `/api/v1/auth/refresh` | 待确认 | refresh_token | 刷新令牌 |
| API-008 | POST | `/api/v1/auth/revoke-all-sessions` | 是 | — | 撤销所有会话 |
| API-009 | POST | `/api/v1/auth/send-verify-code` | 否 | email | 发送验证码 |
| API-010 | POST | `/api/v1/auth/oauth/pending/send-verify-code` | 待确认 | — | OAuth 待处理验证码 |
| API-011 | POST | `/api/v1/auth/validate-promo-code` | 否 | code | 验证推广码 |
| API-012 | POST | `/api/v1/auth/validate-invitation-code` | 否 | code | 验证邀请码 |
| API-013 | POST | `/api/v1/auth/forgot-password` | 否 | email | 忘记密码 |
| API-014 | POST | `/api/v1/auth/reset-password` | 否 | token, password | 重置密码 |
| API-015 | POST | `/api/v1/auth/oauth/pending/exchange` | 待确认 | — | OAuth 待处理兑换 |

### 公共 API

| 编号 | 方法 | 端点 | 需认证 | 参数 | 备注 |
| --- | --- | --- | --- | --- | --- |
| API-016 | GET | `/api/v1/settings/public` | 否 | — | 公开站点设置 |
| API-017 | GET | `/api/v1/announcements` | 待确认 | — | 公告列表 |

### 安装向导 API（`/api/v1/setup/`）

| 编号 | 方法 | 端点 | 需认证 | 参数 | 备注 |
| --- | --- | --- | --- | --- | --- |
| API-018 | GET | `/api/v1/setup/status` | 待确认 | — | 安装状态 |
| API-019 | POST | `/api/v1/setup/test-db` | 待确认 | db_config | 测试数据库连接 |
| API-020 | POST | `/api/v1/setup/test-redis` | 待确认 | redis_config | 测试 Redis 连接 |
| API-021 | POST | `/api/v1/setup/install` | 待确认 | admin_user, db, redis, smtp | 执行安装 |

### 用户 API（`/api/v1/`）

| 编号 | 方法 | 端点 | 需认证 | 参数 | 备注 |
| --- | --- | --- | --- | --- | --- |
| API-022 | GET/POST | `/api/v1/subscriptions` | 是 | — | 订阅列表/创建 |
| API-023 | GET | `/api/v1/subscriptions/active` | 是 | — | 活跃订阅 |
| API-024 | GET | `/api/v1/subscriptions/progress` | 是 | — | 订阅进度 |
| API-025 | GET | `/api/v1/subscriptions/summary` | 是 | — | 订阅汇总 |

### 管理后台 API（几十个端点，见 JS 静态分析）

完整管理后台 API 列表（`/api/v1/admin/` 前缀）见证据 E-0003 及 JS 分析记录。主要包括：

- 仪表盘统计（dashboard/*）
- 用户管理（users）
- 分组管理（groups/*）
- 账号管理（accounts/*，含批量操作、同步、导入）
- 渠道管理（channels/*，含模型定价）
- 渠道监控（channel-monitors/*）
- 代理管理（proxies/*）
- 兑换码/推广码（redeem-codes/*, promo-codes/*）
- 公告管理（announcements/*）
- 系统设置（settings/*）
- 订阅管理（subscriptions/*）
- 用量管理（usage/*）
- Gemini OAuth（gemini/oauth/*）
- Antigravity OAuth（antigravity/oauth/*）
- OpenAI Token 刷新（openai/refresh-token）
- 运维面板（ops/*）
- 错误透传规则（error-passthrough-rules/*）
- 数据管理（data-management/*）
- 备份管理（backups/*）
- TLS 指纹（tls-fingerprint-profiles/*）
- 支付管理（payment/*）
- 推广联盟（affiliates/*）
- 风控（risk-control/*）
- 用户属性（user-attributes/*）
- 系统升级（system/*）

## 参数清单

| 编号 | 位置 | 参数名 | 来源 | 备注 |
| --- | --- | --- | --- | --- |
| P-001 | body | username | index.js 路由推断 | 登录参数 |
| P-002 | body | password | index.js 路由推断 | 登录/注册参数 |
| P-003 | body | email | index.js 路由推断 | 注册/验证码/忘记密码 |
| P-004 | body | code | index.js 路由推断 | 验证码/2FA/推广码/邀请码 |
| P-005 | body | token | index.js 路由推断 | 重置密码 |
| P-006 | body | refresh_token | index.js 路由推断 | 刷新令牌 |
| P-007 | body | session_token | index.js 路由推断 | 两步验证 |
| P-008 | body | provider | index.js 路由推断 | OAuth 提供商标识 |
| P-009 | body | db_config | index.js 路由推断 | setup 数据库配置 |
| P-010 | body | redis_config | index.js 路由推断 | setup Redis 配置 |
| P-011 | body | admin_user | index.js 路由推断 | setup 管理员配置 |
| P-012 | body | smtp | index.js 路由推断 | setup SMTP 配置 |

## OAuth 集成

| 编号 | 提供商 | 回调路由 | 备注 |
| --- | --- | --- | --- |
| O-001 | LinuxDo | `/auth/linuxdo/callback` | 社区 OAuth 登录 |
| O-002 | 微信 | `/auth/wechat/callback` | 微信登录 |
| O-003 | 微信支付 | `/auth/wechat/payment/callback` | 微信支付回调 |
| O-004 | 钉钉 | `/auth/dingtalk/callback` | 钉钉登录 |
| O-005 | 通用 OIDC | `/auth/oidc/callback` | 通用 OIDC 登录 |
| O-006 | Gemini | admin → `/admin/gemini/oauth/*` | Gemini API 账号 OAuth |
| O-007 | Antigravity | admin → `/admin/antigravity/oauth/*` | Antigravity API 账号 OAuth |

## 支付集成

| 编号 | 提供商 | 相关路由 | 备注 |
| --- | --- | --- | --- |
| PY-001 | Stripe | `/payment/stripe`, `/payment/stripe-popup` | Stripe 支付 |
| PY-002 | Airwallex | `/payment/airwallex` | Airwallex 支付 |
| PY-003 | 二维码 | `/payment/qrcode` | 扫码支付 |

## 敏感功能暴露分析

| 功能 | 路由/端点 | 风险 | 状态 |
| --- | --- | --- | --- |
| 安装向导 | `/setup`, `/api/v1/setup/*` | 若安装后未禁用，可能允许重装或泄露配置 | 待验证 |
| 系统重启 | `/admin/system/restart` | 管理操作，需确认权限控制 | 待验证 |
| 系统回滚 | `/admin/system/rollback` | 管理操作，需确认权限控制 | 待验证 |
| Admin API Key 重置 | `/admin/settings/admin-api-key/regenerate` | 管理操作，需确认权限控制 | 待验证 |
| SMTP 测试 | `/admin/settings/test-smtp` | 可能被用于邮件伪造或信息泄露 | 待验证 |
| 批量操作 | `/admin/accounts/batch*` | 批量修改账号凭据，需确认权限控制 | 待验证 |

## 账号

| 编号 | 角色 | 用户名 | 状态 | 备注 |
| --- | --- | --- | --- | --- |
|  |  |  |  | 未提供测试账号 |

## 测试面

| 编号 | 测试面 | 负责代理 | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| S-0001 | recon | Claude Code / Codex | done | JS 静态分析、被动子域名枚举、主动 DNS 主字典枚举完成；HTTP/端口/API 待授权 |
| S-0002 | web | Claude Code | pending | 需存活入口 URL 才能进行手工验证 |
| S-0003 | api | Claude Code | pending | 需存活入口 + 测试账号才能进行授权测试 |
| S-0004 | auth | Claude Code | pending | OAuth 配置缺陷检查，需测试账号 |
