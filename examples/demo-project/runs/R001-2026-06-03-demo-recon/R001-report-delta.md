# R001 报告增量

## 本轮范围

- `*.example.test`
- `app.example.test`
- `api.example.test`

## 本轮新增资产

| 资产 | 类型 | 来源 | 状态 |
| --- | --- | --- | --- |
| `app.example.test` | web | demo active DNS plan | 待确认 |
| `api.example.test` | api | demo active DNS plan | 待确认 |

## 本轮候选 Finding

| 编号 | 标题 | 状态 | 证据 | 缺口 |
| --- | --- | --- | --- | --- |
| F-0001 | 示例调试接口暴露候选 | candidate | E-0003, E-0004 | 未执行真实 HTTP 验证 |

## 本轮结论

R001 展示了从短指令任务卡到 run 级记录，再回填顶层报告的流程。真实项目中必须用实际证据替换 demo 证据。
