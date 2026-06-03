# 主动 DNS 执行计划示例

## 输入

- 根域：`example.test`
- 字典：`dicts/curated/subdomains-main.txt`
- Resolver：`1.1.1.1,8.8.8.8`
- Canary：`app.example.test`
- 随机 NXDOMAIN：`nx-demo.example.test`
- 选择引擎：`puredns + massdns`

## 安全声明

本文件是 demo 计划，不代表真实执行结果。不要对真实目标复用这里的 resolver、canary 或授权边界。

## 执行步骤摘要

1. canary 子域校验。
2. 随机 NXDOMAIN 泛解析检查。
3. 逐 resolver 健康检查。
4. 完整字典枚举。
5. A/AAAA/CNAME 复核。
6. 证据登记。

## 停止条件

- canary 未命中。
- NXDOMAIN 命中 wildcard。
- resolver 0 响应或异常超时。
- 需要扩大到 scope 外目标。
