# tools/dicts

字典治理辅助脚本目录。

适合放这里：

- 从 inventory/evidence/progress 中提取候选子域名、路径、参数。
- 对比 `dicts/curated/` 和 `dicts/candidates/`，找出缺失词条。
- 统计主动 DNS 枚举中 `subdomains-main.txt` 的命中率、噪声和耗时。
- 生成字典分层建议，例如 fast / normal / deep。

规则：

- `refer/fuzzDicts/` 是原始参考库。
- `dicts/curated/subdomains-main.txt` 保留与 fuzzDicts main 的同步关系。
- 优化和分层必须基于实战数据，不凭空自创。
