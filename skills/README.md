# 正式武器库

这里是经过质量治理的正式 Claude Code skill，不是 Xalgorix 原始资料的批量搬运。

## 规则

- 原始资料保留在 `refer/xalgorix/internal/tools/skills/data/`，作为素材库。
- 不做全量格式转换和批量搬运。
- 只有通过 `docs/项目路线/skill质量标准.md` 质量审查的 skill 才放入这里。
- **正式 skill 统一使用简体中文撰写**。
- 每个正式 skill 必须能直接指导一次授权测试，而不只是知识条目。

## 质量标准

详见 `docs/项目路线/skill质量标准.md`。

## Skill 清单

### 信息收集（recon）

| 名称 | 简介 | 来源 |
| --- | --- | --- |
| [subdomain-enumeration](recon/subdomain-enumeration/SKILL.md) | 通过被动（证书透明）和主动（DNS 爆破）方式枚举目标子域名 | xalgorix |
| [javascript-analysis](recon/javascript-analysis/SKILL.md) | 分析前端 JS 文件，提取 API 端点、密钥和隐藏路径 | xalgorix |
| [api-discovery](recon/api-discovery/SKILL.md) | 发现目标 API（OpenAPI/Swagger、版本枚举、REST 资源、GraphQL） | xalgorix |

### Web 漏洞（web）

| 名称 | 简介 | 来源 |
| --- | --- | --- |
| [xss-reflected](web/xss-reflected/SKILL.md) | 反射/存储/DOM 型 XSS 检测，含 WAF 绕过和 CSP 测试 | xalgorix |
| [sqli-sqlmap](web/sqli-sqlmap/SKILL.md) | 使用 sqlmap 检测和利用 SQL 注入，含数据库枚举和 WAF 绕过 | xalgorix |
| [ssrf](web/ssrf/SKILL.md) | SSRF 检测与利用，云元数据访问、内网探测和协议绕过 | xalgorix |
| [file-upload](web/file-upload/SKILL.md) | 文件上传漏洞利用，扩展名/Content-Type/幻数绕过和 polyglot 文件 | xalgorix |
| [idor](web/idor/SKILL.md) | IDOR 不安全的直接对象引用，水平/垂直越权测试 | xalgorix |
| [ssti](web/ssti/SKILL.md) | SSTI 服务端模板注入，Jinja2/Twig/Freemarker/Velocity 引擎利用 | xalgorix |
| [csrf](web/csrf/SKILL.md) | CSRF 跨站请求伪造检测，验证反 CSRF Token 和 SameSite Cookie | xalgorix |
| [directory-traversal](web/directory-traversal/SKILL.md) | 目录遍历/路径穿越，读取系统文件和源码 | xalgorix |
| [insecure-deserialization](web/insecure-deserialization/SKILL.md) | 不安全的反序列化，Java/PHP/Python/.NET/Node.js 利用 | xalgorix |
| [http-request-smuggling](web/http-request-smuggling/SKILL.md) | HTTP 请求走私 CL.TE/TE.CL/TE.TE，缓存投毒和安全绕过 | xalgorix |
| [nosql-injection](web/nosql-injection/SKILL.md) | NoSQL 注入，MongoDB 操作符注入和盲注提取 | xalgorix |
| [graphql-security](web/graphql-security/SKILL.md) | GraphQL 安全测试，内省查询、深度限制和批量查询注入 | xalgorix |
| [oauth-misconfiguration](web/oauth-misconfiguration/SKILL.md) | OAuth 2.0/OIDC 配置缺陷，redirect_uri 绕过和 PKCE 测试 | xalgorix |
| [prototype-pollution](web/prototype-pollution/SKILL.md) | JavaScript 原型污染，__proto__ 注入和属性劫持 | xalgorix |

### API 安全（api）

| 名称 | 简介 | 来源 |
| --- | --- | --- |
| [bola](api/bola/SKILL.md) | BOLA 对象级授权缺陷，越权访问和修改其他用户数据 | xalgorix |
| [mass-assignment](api/mass-assignment/SKILL.md) | 批量赋值漏洞，注入特权字段（role/isAdmin/balance） | xalgorix |
| [bfla](api/bfla/SKILL.md) | BFLA 功能级授权缺陷，普通用户执行管理操作 | xalgorix |
| [jwt-none-attack](api/jwt-none-attack/SKILL.md) | JWT None 算法攻击，绕过签名验证伪造 Token | xalgorix |
| [rate-limit-bypass](api/rate-limit-bypass/SKILL.md) | API 速率限制绕过，HTTP 头/IP 欺骗/路径变体/多账号 | xalgorix |

### 统计

- 总计：**22 个正式 skill**
- 信息收集（recon）：3 个
- Web 漏洞（web）：14 个
- API 安全（api）：5 个

## 如何添加新 Skill

1. 从 `refer/xalgorix/internal/tools/skills/data/` 或实战经验中挑选候选。
2. 按 `docs/项目路线/skill质量标准.md` 重写为中文正式 skill。
3. 放入对应分类目录（`skills/<分类>/<skill名称>/SKILL.md`）。
4. 更新上面清单表。
