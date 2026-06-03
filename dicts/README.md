# 精选字典库

`dicts/` 是本项目自己的默认字典层，不直接要求 AI 每次去原始仓库里找词表。

## 分层规则

| 目录 | 用途 | 默认可用性 |
| --- | --- | --- |
| `curated/` | 当前默认可用字典；子域名优先从参考库主字典原样同步 | 可作为默认建议 |
| `candidates/` | 渗透复盘中发现但尚未治理的新词条 | 不默认使用 |
| `notes/` | 字典来源、回灌记录、取舍说明 | 文档记录 |

原始素材保留在 `refer/fuzzDicts/`。子域名先照搬 `refer/fuzzDicts/subdomainDicts/main.txt`，后续再根据实战命中质量做分层、裁剪和优化。其他类型字典需要扩大规模时，从 refer 临时选取并说明原因、规模、速率和授权条件。

## 默认边界

- 默认只使用发现类字典：子域名、目录/API 路径、参数名。
- 弱口令、RCE、SQL、XSS、SSRF、XXE 等 payload 字典不进入默认主动 recon。
- 主动枚举必须确认授权范围、授权窗口、允许速率或并发、字典规模和停止条件。
- 复盘时发现有效但默认字典没有的词条，先进入 `candidates/`，经复核后再提升或同步到 `curated/`。

## 当前精选字典

| 文件 | 用途 | 默认建议 |
| --- | --- | --- |
| `curated/subdomains-main.txt` | 主动 DNS 子域名枚举，原样同步自 `refer/fuzzDicts/subdomainDicts/main.txt` | 默认首选 |
| `curated/web-paths-small.txt` | 低频目录/API 路径发现 | 仅对已确认入口使用 |
| `curated/params-small.txt` | 参数名提示和 JS/API 分析辅助 | 默认可读，不自动爆破 |
