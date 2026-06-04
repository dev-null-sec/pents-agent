---
name: subdomain-enumeration
description: 通过被动来源和受控主动 DNS 枚举目标子域名，发现更多授权攻击面入口。
category: recon
source: xalgorix
tags:
  - 信息收集
  - 子域名
  - DNS
  - 证书透明
required_tools:
  - subfinder
  - massdns
  - dnsx
  - httpx
  - subzy
optional_tools:
  - puredns
  - shuffledns
---

# 子域名枚举

## 适用场景

- 渗透测试初始阶段，需要扩大目标攻击面。
- Bug Bounty 或授权测试中，目标给出了主域名，需要找到关联 Web/API 入口。
- 被动来源结果很少，需要用常见子域名字典做受控主动 DNS 枚举。

## 授权边界

- 被动收集不直接访问目标业务系统，通常可以优先执行。
- 主动子域名枚举主要产生 DNS 查询，不等同于 HTTP/API 低频探测；它可以采用受控批量解析，但必须有并发、速率、字典规模和停止条件。
- HTTP 存活探测、目录/API 路径发现、登录态接口探测、端口确认、源站直连验证属于更敏感动作，必须按低频或专项授权执行。
- 如果 scope 明确排除某些子域名、第三方资产、源站 IP 或云厂商基础设施，必须在枚举和后续验证中排除。

## 前置条件

执行前先区分任务类型：

| 类型 | 最低条件 | 默认节奏 |
| --- | --- | --- |
| 被动子域名收集 | 目标根域名 | 无主动请求 |
| 主动 DNS 子域名枚举 | 目标根域名、授权窗口、允许 DNS 并发/速率、字典规模、解析器来源 | 受控批量，不按 HTTP 低频处理 |
| HTTP 存活探测 | 已解析子域名、授权窗口、允许 HTTP 速率 | 低频 |
| 路径/API 发现 | 已确认入口 URL、授权窗口、允许请求速率、字典规模 | 低频 |
| 端口/源站验证 | 实际入口或明确授权 IP、授权窗口、端口范围、速率 | 低频或专项确认 |

工具缺失时先运行：

```bash
pents doctor-recon
```

如果缺少 `subfinder`、`massdns`、`dnsx`、`httpx`、`puredns`、`shuffledns` 或 `subzy`，必须说明缺失工具、影响步骤、安装建议和可替代方案，不能只写“未执行”。其中 `massdns` 是默认主动 DNS 核心工具；`puredns`、`shuffledns` 和 `dnsx` 是可选 wrapper/诊断/复核工具，不应因为它们缺失就阻塞 `massdns direct` 主链路。

第三方工具优先从 `tools/third-party/bin/` 查找；PATH 只作为 fallback。`dnsx` 若只存在于全局 PATH，仍要在记录中说明这是 fallback，不是项目推荐安装位置。

## 字典策略

默认使用项目字典层：

- 子域名主动 DNS 枚举：`dicts/curated/subdomains-main.txt`
- 路径/API 发现：`dicts/curated/web-paths-small.txt`
- 参数名辅助分析：`dicts/curated/params-small.txt`

`dicts/curated/subdomains-main.txt` 原样同步自 `refer/fuzzDicts/subdomainDicts/main.txt`。当前阶段子域名字典优先照搬，不自行发明或过早裁剪；后续再根据实战命中质量分层优化。

`refer/fuzzDicts/` 仍是参考库。需要扩大其他类型字典，或从参考库补充专项词表时，必须在执行记录里写清：

- 选择原因。
- 词条数量。
- 允许并发/速率。
- 授权窗口。
- 停止条件。

弱口令、RCE、SQL、XSS、SSRF、XXE 等 payload 字典不属于默认子域名枚举流程，必须专项授权。

## 执行步骤

### 步骤 1：被动枚举

至少使用 2 类被动来源，先尽量不触达目标业务：

```bash
subfinder -d <target.com> -silent -o subs_passive.txt
```

可补充：

- 证书透明日志：crt.sh、Censys 证书搜索等。
- 被动 DNS / 威胁情报：OTX、urlscan、SecurityTrails、Shodan/Censys 可公开部分。
- 已有材料：JS、HTML、历史 URL、证书 SAN、配置片段、报错信息。

记录每个子域名的来源、采集时间和是否去重。

### 被动无结果诊断 checklist

如果 crt.sh、urlscan、Wayback、OTX、搜索引擎等被动来源都没有结果，不要只写“无结果”。按下面清单复盘：

- 域名是否很新，证书透明日志可能还没有沉淀。
- 是否使用通配符证书或 Cloudflare/其他 CDN 统一入口，导致单个子域名不出现在 CT 日志。
- JS、HTML、CSP、CORS、报错信息、OAuth redirect、支付回调里是否出现 API base URL 或子域名。
- urlscan/Wayback/搜索引擎是否完全无 URL，还是只有路径但没有子域名。
- 是否存在 Cloudflare Turnstile、`CF-Ray`、`__cf_bm`、`cf_clearance`、captcha 等 CDN/WAF/反自动化线索。
- 是否需要进入主动 DNS 枚举：已确认授权窗口、DNS 并发/速率、resolver 和字典文件时，使用 `dicts/curated/subdomains-main.txt`。

输出要求：

- 写清已尝试来源和结果。
- 写清被动无结果的可能原因。
- 写清下一步是主动 DNS 枚举、等待用户补充入口，还是补充 JS/API 线索分析。

### Cloudflare / 通配符场景处理

遇到 Cloudflare、通配符证书、泛解析或被动来源全空时：

- 先做随机不存在子域名的 DNS 泛解析检测，避免把 wildcard-noise 当成真实资产。
- 将 Cloudflare、Turnstile、CNAME、证书 SAN、响应头作为线索记录，不对 Cloudflare 或其他 CDN 基础设施继续测试。
- 不要因为被动来源全空就扩大到源站 IP 直连；源站 IP 必须由用户单独确认授权。
- 主动 DNS 枚举可以继续执行，但必须用已确认的 DNS 并发/速率和 resolver，并记录命中质量与噪声。

### 步骤 2：主动 DNS 子域名枚举

满足主动 DNS 枚举条件后，使用同步自 fuzzDicts 主字典的默认子域名字典做受控批量解析。这个步骤不应被描述为“低频 HTTP 探测”，但也不能无限并发或忽略授权窗口。

建议默认：

- 字典：`dicts/curated/subdomains-main.txt`
- 解析器：可信公共 DNS 或用户确认的解析器列表，避免来源不明的开放 resolver。
- 并发/速率：按用户确认值执行；未确认时不执行主动枚举。
- Canary：至少提供 1 个已知存在子域名，例如 `ai.<target.com>`；canary 不命中时停止完整枚举。
- 泛解析检测：先解析随机不存在的子域名，判断是否存在 wildcard/catch-all。
- Resolver 自检：逐个 resolver 对 canary 或 NXDOMAIN 目标做解析，慢、0 响应或异常 resolver 必须剔除。

优先使用 `pents active-dns` 生成执行计划，不要临场拼完整流程：

```bash
uv run --project cli pents active-dns "*.target.com" \
  --project <project-name> \
  --run <Rxxx-date-purpose> \
  --dict dicts/curated/subdomains-main.txt \
  --resolvers 1.1.1.1,1.0.0.1,8.8.8.8,8.8.4.4,223.5.5.5,119.29.29.29 \
  --canary <known-existing-label-or-fqdn> \
  --engine auto \
  --save
```

执行计划或脚本必须包含：

1. canary 子域校验。
2. 随机 NXDOMAIN 泛解析检查。
3. 逐 resolver 健康检查。
4. 候选 FQDN 文件生成。
5. `massdns` 文件输入完整字典枚举。
6. 命中提取、耗时 metrics 和 summary。
7. 必要时的 `pents evidence` 证据登记命令。

工具链选择：

- 默认主链路：`massdns direct`，由 `tools/recon/active-dns-massdns.ps1` 生成候选文件并把文件交给 massdns，不走 stdin pipe。
- 可选 wrapper：`puredns + massdns`，只用于人工诊断或复杂 wildcard 场景参考；不要让 Claude Code 默认执行 puredns pipe。
- 可选替代：`shuffledns + massdns`，用于 ProjectDiscovery 风格兼容验证。
- 可选诊断：`dnsx -l`，用于小列表复核、NOERROR/NODATA 补查或参数排查，不作为默认完整字典枚举链路。

禁止把 `dnsx -wd` 当作常规枚举参数。R001 已暴露过该类参数误用会造成 0 命中误判；如果看到 `dnsx -wd <domain>` 被用于完整字典枚举，必须停止并修正为 `pents active-dns` 计划或 `dnsx -l <fqdn-list>` fallback。

- 缺 `massdns`：不能执行默认主动 DNS 主链路，应阻塞并建议按 `pents doctor-recon` 补齐项目本地工具。
- 缺 `puredns` 或 `shuffledns`：默认 `massdns direct` 不受影响，只记录 optional wrapper/fallback 缺失。
- 缺 `dnsx`：默认 `massdns direct` 仍可执行；但不能做 dnsx 小列表诊断或 NOERROR/NODATA 补查，应写清复核能力缺失。
- 缺 resolver 授权或 canary：不执行完整枚举，只记录 blocker。

#### massdns Snl 与 NODATA

`massdns -o Snl` 只输出存在 A/AAAA/CNAME 等记录的结果。NOERROR 但无 A/AAAA/CNAME 的域名不会出现在命中列表里，这是预期行为，不是漏扫。

R003 devnu11 复测中，`massdns direct` 命中 `ai/blog/lk/st` 4 个可解析子域；R001 dnsx 额外出现 `online.devnu11.cn`，原因是该域名为 NOERROR/NODATA 候选。报告对比时必须写成：

- `massdns hits`：可解析入口候选。
- `dnsx NOERROR/NODATA`：DNS 存在但无地址记录的候选，不直接作为 Web 入口。

如果任务需要捕获 NOERROR/NODATA，不要改回 puredns pipe；应对小列表、已知候选或专项候选文件追加 `dnsx` 复核，并单独记录其耗时、query 类型和差异。

### 步骤 3：DNS 解析验证与去噪

对被动和主动结果合并去重，再验证解析结果。复核必须记录 A/AAAA/CNAME，不只记录“解析成功”。

```bash
sort -u subs_passive.txt subs_active_dns.txt > subs_all.txt
dnsx -silent -l subs_all.txt -a -aaaa -cname -json -o subs_resolved.jsonl
```

结果分类要求：

| 分类 | 判定 | 处理 |
| --- | --- | --- |
| `resolved-a` | NOERROR 且有 A 记录 | 进入 inventory，后续 HTTP 授权后再探测 |
| `resolved-aaaa` | NOERROR 且有 AAAA 记录 | 进入 inventory，记录 IPv6 线索 |
| `resolved-cname` | NOERROR 且有 CNAME | 记录 CNAME、CDN/云厂商/第三方服务线索 |
| `nodata` | NOERROR 但无 A/AAAA/CNAME | 不当作可访问入口；记录为 DNS 存在但无地址 |
| `nxdomain` | NXDOMAIN | 丢弃或保留为去噪证据 |
| `wildcard-noise` | 随机 NXDOMAIN 与候选结果响应一致 | 不当作真实资产，暂停并复盘 wildcard 策略 |
| `resolver-error` | SERVFAIL、REFUSED、timeout 或 resolver 0 响应 | 剔除异常 resolver 后重试关键步骤 |

去噪要求：

- 如果存在泛解析，把与随机子域名响应一致的结果标为 `wildcard-noise`，不要当作真实资产。
- 如果解析到 Cloudflare、Akamai、Fastly、阿里云、腾讯云、华为云等第三方网络，只记录 CDN/云厂商线索，不继续测试第三方基础设施。
- 源站 IP 只作为线索，未获明确授权前不得直连验证。
- NOERROR/NODATA 必须和 A/AAAA/CNAME 分开写，避免把没有地址记录的域名当成可访问资产。

### 步骤 4：HTTP 存活探测

HTTP 探测比 DNS 枚举更接近业务系统，必须使用低频节奏：

```bash
httpx -l subs_resolved.txt -title -status-code -tech-detect -o subs_alive.txt
```

记录状态码、标题、最终 URL、关键响应头、证书线索和技术栈。不要在这个步骤做路径 fuzz、漏洞扫描或认证绕过。

### 步骤 5：子域名接管风险提示

仅做提示，不替代人工确认：

```bash
subzy run --targets subs_all.txt --hide-fails
```

疑似接管结果必须带上 CNAME、第三方服务类型和验证证据；证据不足时只能进入 candidate finding。

## 停止条件

主动 DNS 枚举遇到以下情况应暂停：

- 用户确认的 DNS 并发/速率、字典规模或授权窗口已超出。
- resolver 大量超时、SERVFAIL、被限速，或解析结果明显失真。
- wildcard/catch-all 导致无法区分真实资产。
- 结果指向第三方基础设施，需要重新确认边界。

HTTP/路径/API/端口探测遇到以下情况应立即暂停：

- 业务响应异常、WAF/IDS 告警、频繁 429/403/5xx。
- 出现疑似敏感信息、凭据、生产数据。
- 需要扩大到非授权域名、源站 IP、全端口或高风险 payload。

## 跳过 / 阻塞反馈格式

如果未执行主动子域名枚举，必须明确写：

```text
主动 DNS 子域名枚举：未执行
原因：缺少 <授权窗口 / DNS 并发或速率 / 字典规模 / 解析器来源 / scope 确认>
缺失工具：<massdns / dnsx / puredns / shuffledns / 无；说明核心或可选>
安装建议：<运行 pents doctor-recon 后摘录具体建议；不要只写“安装工具”>
已完成替代项：<被动来源、本地 JS、证书、历史 URL 等>
影响：无法确认精选字典能否发现新子域名
下一步需要用户确认：<具体问题>
```

如果未执行 HTTP 存活或路径/API 探测，必须单独说明，不要和 DNS 枚举混为一个 blocker。

## 输出格式

执行结果至少输出下面结构，方便主代理写入项目记录：

```text
目标根域：<target.com>
授权状态：<被动 / 主动 DNS / HTTP 探测分别说明>
被动来源：<来源 + 数量 + 文件>
主动 DNS：<默认 massdns direct / 可选 puredns+massdns wrapper / 替代 shuffledns+massdns / dnsx-l 诊断 / 未执行>
Canary：<目标 + 命中/未命中 + 证据文件>
NXDOMAIN / wildcard：<随机目标 + 结果 + 是否 wildcard-noise>
Resolver：<保留 resolver / 剔除 resolver / 剔除原因>
DNS 结果分类：
  - resolved-a: <数量>
  - resolved-aaaa: <数量>
  - resolved-cname: <数量>
  - nodata: <数量>
  - nxdomain: <数量>
  - wildcard-noise: <数量>
  - resolver-error: <数量>
工具缺失或 fallback：<缺失工具、是否影响 massdns direct 主链路、fallback 原因、影响>
下一步：<HTTP 探测 / 等待授权 / 字典回灌 / skill 修订>
证据：<E-xxxx 或待登记文件路径>
```

## 结果回填

执行完毕后必须更新项目记录：

- `inventory.md`：子域名、DNS 记录类型、A/AAAA/CNAME、NOERROR/NODATA 分类、CDN/云厂商判断、HTTP 存活入口、技术栈。
- `evidence.md`：来源、命令摘要、字典文件、resolver、canary、NXDOMAIN、采集时间、关键响应摘要。
- `progress.md`：已执行项、跳过项、阻塞项、停止原因。
- `review.md`：本次字典命中质量、漏掉的新词条、是否需要修订 skill。

复盘时，把实战中发现但 `dicts/curated/` 没覆盖的有效词条先写入 `dicts/candidates/`，再按 `dicts/notes/promotion-rules.md` 晋升。

## 验收标准

1. 至少通过 2 类被动来源收集子域名。
2. 如果主动 DNS 条件满足，已生成或执行 `pents active-dns` 计划，并确认默认主链路为 `massdns direct`。
3. 完整枚举前已完成 canary、随机 NXDOMAIN 和逐 resolver 自检；结果记录候选数、命中数、耗时和 wildcard 结论。
4. HTTP 存活探测按低频节奏执行，并记录标题、状态码和技术栈。
5. DNS 结果按 resolved-a、resolved-aaaa、resolved-cname、nodata、nxdomain、wildcard-noise、resolver-error 分类；如果使用 massdns Snl，明确说明 NODATA 不会出现在 massdns 命中列表中，需用 dnsx 等复核补充。
6. 跳过项写明具体原因、缺失工具、安装建议、影响和下一步需要用户确认的信息。
7. 结果已回填 inventory、evidence、progress、review，并记录字典回灌建议。
