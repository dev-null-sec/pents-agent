# tools/recon

信息收集辅助脚本目录。

适合放这里：

- 已下载 JS 的静态提取脚本。
- DNS 结果去重、wildcard 噪声标记、子域名命中统计。
- HTTP 响应头、TLS、标题和技术栈摘要整理。
- OpenAPI/Swagger/GraphQL 发现结果的格式转换。

不适合放这里：

- 第三方扫描器二进制。
- 自动 exploit。
- 未经授权条件确认就会发起大量请求的脚本。

默认输出位置应在当前 run：

```text
projects/<name>/runs/Rxxx-<date-purpose>/outputs/
```

## 当前子目录

- `static-js/`：JS 静态分析辅助工具预留目录；当前由 `pents static-js` 提供轻量提取能力。

## 当前脚本

- `active-dns-massdns.ps1`：主动 DNS 默认执行器。它用字典生成候选文件，再以文件输入方式调用 `massdns`，同时记录 canary、resolver 自检、NXDOMAIN/wildcard、完整枚举、命中提取和耗时 metrics。默认给 Claude Code 使用，避免 puredns wrapper 的 stdin pipe 卡死问题。
