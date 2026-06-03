# tools/third-party/bin

本目录是 workspace-local 第三方工具运行目录，`pents doctor-recon` 会优先检查这里，再检查系统 PATH。

这里通常放本机编译或下载的可执行文件，例如：

- `dnsx.exe`
- `puredns.exe`
- `massdns.exe`
- `shuffledns.exe`
- `subfinder.exe`
- `httpx.exe`
- `subzy.exe`

普通 Git 默认不提交这些二进制。需要二开时，把源码或 fork 放到 `tools/third-party/vendor/`；需要离线迁移时，后续使用 Git LFS、release artifact 或单独备份包承载二进制。
