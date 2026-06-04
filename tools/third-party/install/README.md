# 第三方工具安装说明

## 原则

- 本项目优先把第三方 recon 工具安装到 `tools/third-party/bin/`。
- 安装脚本、manifest、来源和版本说明进入 Git。
- 需要二开的工具源码或 fork 放到 `tools/third-party/vendor/<tool>/` 并进入 Git。
- 下载缓存、编译缓存和本机运行二进制不默认进入普通 Git。

## PowerShell 本地安装目标

在项目根目录执行：

```powershell
New-Item -ItemType Directory -Force .\tools\third-party\bin | Out-Null
$env:GOBIN = (Resolve-Path ".\tools\third-party\bin").Path
```

如果需要访问国外网络，在本机 PowerShell 临时设置：

```powershell
$env:all_proxy = "http://127.0.0.1:7890"
```

这个代理配置只适用于本机，不要写入远端机器或项目通用配置。

## Go 工具

```powershell
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest
go install -v github.com/d3mondev/puredns/v2@latest
go install -v github.com/PentestPad/subzy@latest
```

安装完成后运行：

```powershell
uv run --project cli pents doctor-recon
```

## massdns

`massdns` 是当前主动 DNS 默认主引擎。`tools/recon/active-dns-massdns.ps1` 会先生成候选文件，再把候选文件作为 massdns 输入，避免 puredns wrapper 内部 stdin pipe 在 Claude Code 执行环境里卡死。

`puredns`、`dnsx`、`shuffledns` 现在都是可选诊断或替代工具，不再是默认主动 DNS 主链路的必需项。

当前 Windows 本地链路：

- 上游版本：`blechschmidt/massdns` `v1.1.0`。
- 源码位置：`tools/third-party/vendor/massdns/`。
- 构建方式：Cygwin `gcc-core` + `make`，使用官方 `make nolinux` 等价参数编译。
- 运行文件：`tools/third-party/bin/massdns.exe`，并把 Cygwin runtime `cygwin1.dll` 放在同目录，避免依赖系统 PATH。

如果需要改 massdns 源码，把 fork 或源码放入 `tools/third-party/vendor/massdns/`，保留上游来源、版本和 LICENSE。

## 二开流程

1. 在 `tools/third-party/vendor/<tool>/` 放入源码或 fork。
2. 在 `tools/third-party/install/recon-tools.json` 更新来源、版本、构建方式和本地二进制名。
3. 从 `tools/third-party/vendor/<tool>/` 构建到 `tools/third-party/bin/`。
4. 提交源码、补丁、manifest 和说明，不提交普通构建缓存。
