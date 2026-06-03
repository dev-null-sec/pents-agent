# tools/third-party

本目录统一管理第三方工具资产，避免第三方运行时、源码二开和自写脚本混在一起。

## 分类

| 目录 | 用途 | 是否进入普通 Git |
| --- | --- | --- |
| `install/` | 安装说明、manifest、来源和版本记录 | 是 |
| `vendor/` | 项目维护或准备二开的第三方源码/fork/补丁 | 是 |
| `patches/` | 能以补丁表达的小改动 | 是 |
| `bin/` | 本机可执行文件，供 CLI 和 AI 优先调用 | 默认否，仅 README 入仓 |
| `cache/` | 下载、编译、临时缓存 | 否 |
| `dist/` | 离线包或发布产物 | 默认否，后续可走 Git LFS 或 release artifact |

## recon 工具方向

- 主动 DNS 主引擎：`puredns + massdns`。
- 主动 DNS 兼容替代：`shuffledns + massdns`。
- DNS 复核和小规模 fallback：`dnsx`。

`pents doctor-recon` 的查找顺序是 `tools/third-party/bin` -> 系统 PATH。PATH 只作为 fallback，不是项目推荐安装位置。
