# tools/recon/static-js

JS 静态分析辅助工具预留目录。

当前 `pents static-js` 已提供轻量本地提取能力：

- 路由。
- API 端点。
- 参数名线索。
- OAuth / OIDC 线索。
- 支付线索。
- 配置、CDN、WAF 线索。

后续如果需要更复杂的解析，例如 AST、source map、chunk 依赖关系、框架路由还原，应把核心逻辑沉淀到本目录，再由 `pents static-js` 做薄封装。

默认只分析本地已下载 JS 文件，不主动访问目标。
