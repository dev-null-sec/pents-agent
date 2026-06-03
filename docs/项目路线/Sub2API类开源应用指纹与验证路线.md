# Sub2API 类开源应用指纹与验证路线

## 目标

把 devnu11 实战中证明有价值的“先识别开源应用，再按默认攻击面验证”的方法沉淀下来。

适用对象不只 Sub2API，也包括类似的开源 Web/API 平台：

- 前端是 SPA，API 路径和配置大量出现在 JS bundle 中。
- 后端是 Web/API 网关、管理后台、支付/订阅/OAuth 集成平台。
- 公开仓库或文档能帮助理解默认路由、默认配置和风险面。

## 授权边界

允许：

- 阅读公开源码、README、release note、issue、默认配置示例。
- 用公开资料理解功能模块、默认路由、配置项和技术栈。
- 把从源码/文档得出的假设写入 inventory、review 和待验证路线。

不允许默认执行：

- 测试作者 demo 站、官方体验站、GitHub Pages、第三方托管环境。
- 对公开仓库中提到的第三方 API、OAuth provider、支付平台、对象存储做探测。
- 把源码中的默认凭据、示例 token、测试配置当成真实目标凭据尝试。
- 未获用户确认时直连疑似源站 IP 或第三方基础设施。

所有主动验证都必须落在用户授权目标上，并满足对应的授权窗口、速率、账号和范围要求。

## 指纹识别方法

### 1. JS Bundle 线索

优先从 `javascript-analysis` 结果中提取：

- 默认站点名、产品名、版权、license、GitHub 链接。
- `baseURL`、`apiBase`、`VITE_*`、`window.__APP_CONFIG__` 等配置模式。
- 前端框架和库：Vue/React、Axios、router、i18n、支付 SDK。
- 管理后台路由、setup/install/wizard 路由、OAuth 回调、支付页面。
- Turnstile/captcha/CDN/WAF 线索。

识别结论分级：

| 级别 | 条件 | 记录方式 |
| --- | --- | --- |
| 确认 | 产品名、默认配置、路由和 API 结构均与公开项目匹配 | 写入 software asset |
| 较可能 | 多个功能模块匹配，但缺少版本或默认配置证据 | 写入 clue |
| 线索 | 只有单个字符串或相似路径 | 写入 note，不做断言 |

### 2. 路由与 API 结构

从 JS/API 结果中确认是否存在这些模块：

- setup/install：`/setup`、`/api/v1/setup/status`、`test-db`、`test-redis`、`install`。
- 认证：邮箱登录、注册、2FA、密码重置、OAuth pending/exchange。
- 用户侧：API Key、用量、订阅、兑换码、推广、订单。
- 管理后台：admin users、accounts、channels、settings、system、billing、audit。
- 运维高敏：restart、update、rollback、backup、admin-api-key regenerate。
- 支付：Stripe、Airwallex、二维码、订单回调。
- OAuth/OIDC：redirect_uri、state、provider、绑定/解绑、管理员侧账号 OAuth。

### 3. 默认配置与技术栈

公开源码和文档只用于理解默认情况：

- 后端框架、数据库、缓存、队列和对象存储。
- 默认 API 前缀、默认站点名、默认功能开关。
- 安装流程是否依赖数据库、Redis、SMTP、管理员初始化。
- 安全配置项：Turnstile、验证码、CORS、JWT/session、管理员 API Key。

不要因为源码中存在某个默认配置，就直接断言目标生产环境也存在。所有结论都要回到授权目标验证。

## Sub2API 后续验证路线

### A. Setup / Install

目标：

- 确认生产环境是否仍暴露 setup 页面和 setup API。
- 判断 setup status 是否泄露安装状态、版本或配置。

验证前置：

- 实际访问 URL。
- 授权窗口和 HTTP 请求速率。
- 只做 GET/HEAD 或明确安全的状态查询；不得提交 install、test-db、test-redis 等可能触发连接或写入的请求，除非用户专项授权。

重点路径：

- `/setup`
- `/api/v1/setup/status`
- `/api/v1/setup/test-db`
- `/api/v1/setup/test-redis`
- `/api/v1/setup/install`

### B. Admin API

目标：

- 验证管理后台 API 是否有正确认证和细粒度授权。
- 重点关注 IDOR/BFLA、批量操作、系统运维动作和 Admin API Key 操作。

验证前置：

- 普通测试账号和管理员账号，或用户确认允许创建对应账号。
- 管理员操作必须逐项确认，不默认执行会改变状态的接口。

优先关注：

- `/admin/system/restart`
- `/admin/system/update`
- `/admin/system/rollback`
- `/admin/settings/admin-api-key/regenerate`
- `/admin/accounts/batch*`
- `/admin/settings/test-smtp`

### C. OAuth / OIDC

目标：

- 检查 redirect_uri、state、provider 参数、绑定/解绑流程。
- 区分用户侧 OAuth 和管理员侧第三方账号 OAuth。

验证前置：

- 实际登录入口。
- 测试账号。
- 用户确认允许触发 OAuth 登录流程；不测试第三方 provider 本身。

检查点：

- redirect_uri 是否严格白名单。
- state 是否存在、是否一次性、是否绑定 session。
- provider 参数是否可枚举或绕过。
- pending/exchange 流程是否存在账号绑定混淆。

### D. 支付 / 订阅

目标：

- 检查订单金额、套餐、数量、币种、回调状态是否在服务端校验。
- 确认前端价格参数是否只是展示，不被服务端信任。

验证前置：

- 测试账号。
- 用户确认可在测试环境或低风险订单上验证支付流程。
- 不真实支付，不测试第三方支付平台。

检查点：

- Stripe / Airwallex / 二维码支付的订单创建参数。
- 支付结果页和回调状态是否可被前端参数影响。
- 订阅、兑换码、余额和用量是否存在越权读取或修改。

### E. 默认配置 / 安全开关

目标：

- 确认生产环境是否启用了必要安全配置。
- 通过响应和公开配置线索判断，不做破坏性验证。

检查点：

- Turnstile/captcha 是否只在前端展示，后端是否校验。
- CORS 是否过宽。
- 安全响应头是否缺失。
- Session/JWT cookie 是否有 `HttpOnly`、`Secure`、`SameSite`。
- SMTP、对象存储、模型供应商密钥是否有泄露线索。

## 输出要求

每次执行这一路线时，必须回填：

- `inventory.md`：软件识别、路由/API、OAuth、支付、默认配置、CDN/WAF 线索。
- `evidence.md`：JS 文件、公开源码/文档引用、请求摘要、响应摘要。
- `progress.md`：已执行项、跳过/阻塞项和原因类型。
- `review.md`：哪些指纹有效，哪些默认攻击面需要新增 skill 或 CLI 支持。

如果只完成静态识别，finding 状态必须保持 candidate / 待确认。
