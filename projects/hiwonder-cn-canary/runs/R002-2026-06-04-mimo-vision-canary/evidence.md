# R002 证据记录

## E-0001：页面截图

- 证据类型：browser_screenshot
- 来源 URL：https://www.hiwonder.com.cn/admin_hiwonder.php/
- 本地路径：`outputs/browser/screenshots/admin_hiwonder_2026-06-04.png`
- 采集时间：2026-06-04 18:02
- 采集工具：agent-browser screenshot
- 文件大小：219,132 bytes
- SHA256：`c8c67558bd9ddbd56844d331e3a78315d4487aff5eb2e85cd3965d6af1eb7ab1`
- 备注：截图已保存；视觉 API (mimo-v2.5) 成功读取截图内容
- browser_step=open; source_url=https://www.hiwonder.com.cn/admin_hiwonder.php/; screenshot=admin_hiwonder_2026-06-04.png; collected_at=2026-06-04T18:02; chain=complete

## E-0002：页面快照（完整可访问性树）

- 证据类型：accessibility_snapshot
- 来源 URL：https://www.hiwonder.com.cn/admin_hiwonder.php/
- 本地路径：`outputs/browser/snapshots/admin_hiwonder_full.txt`
- 采集时间：2026-06-04 18:02
- 采集工具：agent-browser snapshot --full
- 关键内容摘要：
  - 页面标题："幻尔后台管理"
  - 用户名输入框、密码输入框
  - 点击验证组件（疑似滑块验证码）
  - 保持会话复选框
  - 登录按钮
  - 公司链接（深圳市幻尔科技有限公司）
- 备注：`snapshot -i` 初始返回空，`--full` 返回完整可访问性树

## E-0003：pents vision-review canary 输出（mimo-v2.5）

- 证据类型：visual_review_json
- 本地路径：`outputs/browser/visual-reviews/vision-review-001.json`
- 采集时间：2026-06-04 18:02
- 模型：mimo-v2.5
- API 基址：https://token-plan-cn.xiaomimimo.com/v1
- HTTP 状态：200
- 耗时：4,781ms
- 结果摘要：
  - `can_read_image: true`
  - `page_type: login`
  - `captcha_or_waf.present: true`（type: captcha）
  - `visible_interactive_elements`: username input, password input, captcha button, keep session checkbox, login button（5 个）
  - `sensitive_content.present: null`
  - `confidence: 1.0`
- 备注：MiMo v2.5 视觉 API 成功读图，视觉 fallback 链路可用

## 证据列表

| 编号 | 类型 | 目标 | 关联 Finding | 关联文件 | 备注 |
| --- | --- | --- | --- | --- | --- |
| E-0001 | browser_screenshot | https://www.hiwonder.com.cn/admin_hiwonder.php/ | - | outputs/browser/screenshots/admin_hiwonder_2026-06-04.png | collected_at=2026-06-04T18:02; sha256=c8c67558bd9ddbd56844d331e3a78315d4487aff5eb2e85cd3965d6af1eb7ab1; chain=complete |
| E-0002 | accessibility_snapshot | https://www.hiwonder.com.cn/admin_hiwonder.php/ | - | outputs/browser/snapshots/admin_hiwonder_full.txt | collected_at=2026-06-04T18:02; chain=complete |
| E-0003 | visual_review_json | https://www.hiwonder.com.cn/admin_hiwonder.php/ | - | outputs/browser/visual-reviews/vision-review-001.json | collected_at=2026-06-04T18:02; model=mimo-v2.5; can_read_image=true; chain=complete |
