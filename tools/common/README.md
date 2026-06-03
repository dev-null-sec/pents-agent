# tools/common

多个 tools 共用逻辑的目录。

适合放这里：

- Markdown 表格读写辅助。
- JSON/Markdown 输出格式化。
- 路径、run 编号、证据 ID 等通用校验。
- 安全检查：确认目标是否在 scope、确认 run 输出目录、拒绝写到项目外。

不要把业务脚本直接堆到 common；只有 2 个及以上工具共用时再放公共逻辑。
