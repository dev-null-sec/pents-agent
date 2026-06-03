# 字典回灌与治理规则

## 当前取舍

子域名字典先照搬 `refer/fuzzDicts/subdomainDicts/main.txt` 到 `dicts/curated/subdomains-main.txt`，不在当前阶段自行发明或过早裁剪。

后续优化再根据实战命中率、误报率、目标类型和执行成本拆分 fast / normal / deep 等层级。

## 进入 candidates 的条件

渗透过程中遇到以下内容，如果默认字典没有，可以先加入 `dicts/candidates/`：

- 真实存在的子域名前缀。
- 真实存在的目录、前端路由、API 路径。
- 真实业务参数名、对象 ID 参数、OAuth/支付相关参数。
- 与当前项目类型高度相关的常见词，例如 AI API 代理平台中的 `channel`、`model`、`subscription`。

## 晋升或同步到 curated 的条件

满足以下至少两项，再从 candidates 晋升：

- 在 2 个及以上项目中出现。
- 与常见 Web/API 工作流强相关。
- 低风险、适合发现阶段使用。
- 不属于弱口令、漏洞 payload、破坏性测试载荷。
- 能帮助减少手工重复分析。

子域名前缀如果已经存在于 `subdomains-main.txt`，无需重复加入 candidates；如果不存在，先加入 candidates，复盘时再决定是否追加到主字典副本或后续分层字典。

## 禁止默认晋升

以下内容不得进入默认精选字典：

- 密码、弱口令、用户名撞库词表。
- RCE、SQL、XSS、SSRF、XXE 等攻击 payload。
- 可能触发高风险行为的管理操作路径，除非作为人工审查提示而非自动枚举。
- 第三方资产、客户敏感命名或真实内部命名。

## 复盘记录格式

```md
| 词条 | 类型 | 来源项目 | 证据 | 处理建议 |
| --- | --- | --- | --- | --- |
| api | 子域名 | demo-project | E-0001 | 已在 subdomains-main，无需新增 |
```
