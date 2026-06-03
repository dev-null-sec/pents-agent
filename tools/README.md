# tools

`tools/` 存放项目维护的工具资产：自写脚本和第三方工具资产。

自写脚本按用途放在 `recon/`、`evidence/`、`dicts/`、`common/`。第三方工具统一归入 `third-party/`，避免二进制、源码 fork、安装脚本和自写工具混在同一层。

## 职责

tools 负责可复用、可验证、输入输出明确的小任务，例如：

- 从已下载 JS 中提取 API、路由、参数和集成线索。
- 计算证据文件 hash、生成响应摘要。
- 统计字典命中、噪声和候选词条。
- 把工具输出转换成 inventory/evidence/report-delta 可读的 Markdown 或 JSON。
- 管理第三方 recon 工具的本地安装、源码二开入口和可迁移清单。

## 与 CLI 的边界

- `pents` 负责项目创建、记录、任务卡、汇总和合并。
- `tools/` 负责具体可复用脚本。
- CLI 可以在后续调用 tools，但不要把脚本逻辑全部塞进 `cli/src/pents/cli.py`。
- `pents doctor-*` 优先检查 `tools/third-party/bin/`，再检查系统 PATH。
- 需要二开的第三方工具源码/fork 放入 `tools/third-party/vendor/` 并提交；本机编译出的二进制放入 `tools/third-party/bin/`，默认不按普通 Git 提交。

## 分类

| 目录 | 用途 |
| --- | --- |
| `recon/` | 信息收集辅助脚本，例如 JS 静态分析、DNS 结果去噪、HTTP 指纹摘要 |
| `evidence/` | 证据 hash、响应摘要、截图/文件登记辅助 |
| `dicts/` | 字典统计、候选词条提取、命中率和噪声分析 |
| `common/` | 多个工具共享的解析、输出和安全检查逻辑 |
| `third-party/` | 第三方工具的安装清单、源码/fork、补丁、本机二进制和缓存 |

## 第三方工具入仓规则

- 入 Git：`tools/third-party/install/`、`tools/third-party/patches/`、`tools/third-party/vendor/` 中的安装脚本、manifest、README、补丁、LICENSE、二开源码/fork。
- 不默认入普通 Git：`tools/third-party/bin/` 中不同机器编译出的 exe、临时下载包、构建缓存、大体积离线包。
- 如果确实需要把二进制随项目分发，后续单独使用 Git LFS、release artifact 或备份包方案，不和源码规则混在一起。
- 全局安装只能作为 fallback；项目内规范安装位置是 `tools/third-party/bin/`。
- 当前 `dnsx` 曾被安装到 `C:\Users\Administrator\go\bin\dnsx.exe`，这是历史偏差；后续应迁到 `tools/third-party/bin/` 或由 `tools/third-party/vendor/` 源码重新构建。

## 新增脚本标准

新增脚本前先确认：

- 该动作在至少 2 次测试中重复出现，或明显能减少大量手工工作。
- 输入、输出、失败情况能说清楚。
- 不会默认执行高风险请求、漏洞利用、爆破认证或破坏性动作。
- 输出能写入 run 的 `outputs/`，或被 `pents evidence/merge/report` 使用。

Python 脚本运行优先使用 `uv`。
