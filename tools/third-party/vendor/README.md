# tools/third-party/vendor

本目录用于存放项目准备长期维护或二开的第三方工具源码/fork。

## 规则

- 放入源码时保留上游仓库地址、版本、LICENSE 和本地修改说明。
- 能以补丁表达的小改动，优先放清楚补丁和变更原因。
- 构建产物输出到 `tools/third-party/bin/`，不要把缓存和临时包混进源码目录。
- 不需要二开的第三方工具，可以只在 `tools/third-party/install/recon-tools.json` 记录来源和安装方式。
