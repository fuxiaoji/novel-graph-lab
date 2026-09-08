# v0.3 verification

The former v0.2 historical example is replaced with a new relation-centered graph and real multi-method answers. The earlier implementation record below is retained only as history.

- 12 Python tests pass: source/line grounding, full text coverage, chunk caching, HTTP/export credential exclusion, mass-conserving graph propagation, real traversal edges, invalid-neighbor rejection, read/choose/read ordering, reranker-ID validation, disagreement referee and explicit BGE failure.
- The full Blue Carbuncle story contains 42,115 Unicode characters. A real GLM-4.7 build used 63 successful API calls; all new node/edge source offsets were independently checked.
- Resulting graph: 121 nodes, 169 edges, 8 isolated nodes (6.6%). Node evidence character-union coverage: 6,630 / 42,115 (15.7%). All 121 nodes have grounded source evidence. Coverage is not answer accuracy.
- Early live integration exposed citation renumbering. The final kernel explicitly constrains IDs and includes one logged repair request. New answers are rerun with the corrected kernel; old pre-fix outputs are not the default demo.
- The published `examples/demo-audit.json` records final per-method warnings, citations, node reads and real traversals. This is a structural audit, not a correctness score.
- API request counts exclude failed/in-flight calls and prior debugging attempts. The run manifest reports successful calls represented by the final published artifacts.

---

## Historical v0.2 record

# 验证记录

v0.2 阅读界面更新：冷白底与墨蓝控件、原文阅读排版、统计横栏，移除装饰性透视地板和默认旋转。保留全图、子图筛选与节点证据功能，截图来自真实应用。公开 Demo 使用自包含静态 HTML，导入入口引导用户在本机运行，不显示密钥表单。Python 测试、图谱工具测试与脚本语法检查通过。

本次全图总览更新：浏览器确认默认 force 布局、focus=false、画布显示 739/739 节点；检索阶段也保留 739 节点。原始图谱 92 个孤立节点，12.4%。新增 `node tests/test_graph_utils.cjs` 验证重叠证据去重、Unicode 字符偏移、缺失全文不推算、孤立节点保留和确定性力导向布局。739 节点布局在本机 Node 测试约 2 秒；布局包含节点排斥、边弹簧吸引和中心力。原始存储坐标保留在数据中，默认展示使用重新计算的全图布局。

2026-09-08，Windows / Python 3.13 / Codex 内置浏览器。

- 6 项自动测试通过：中文 BM25、分块无遗漏、逐字证据与缓存、两轮真实图遍历、取消前不发请求、完整 HTTP 建图/问答/复用/导出及 Origin 拒绝。
- 故意注入不存在的引文被拒绝；不存在的回答引用被标记。原文字符偏移逐字比对通过。
- 本地模拟 API 经过实际 HTTP 适配器：首次建图和问答 3 次调用，复用图谱新问答 2 次。模拟 Key 不存在于任务响应、缓存和 HTML 中。
- CLI 完整运行输出 `outputs/smoke-test/graph.json`、`session.json`、`replay.html`。该输出来自确定性模拟模型，仅用于功能测试。
- 浏览器验证：原 739 节点 / 1,886 关系载入；7 个历史问题；逐步时间轴修复边界偏移；子图聚焦和标签避让；节点点击显示原文与关系；两种布局；倍速播放；导入中文文本、配置本地 API、完整回答和证据引用；HTML 导出成功保存至 outputs/exports，并打开导出文件验证内容。
- 桌面 1440×900 与窄屏布局已观察；侧栏可滚动，文本输入不再被 flex 压缩。
- 导出 HTML 的脚本和样式完全内嵌，HTML 解析器验证无外部 script；经本地静态服务打开正常。测试浏览器策略阻止 file:// 导航，因此未在此浏览器直接测试双击 file://；没有绕过该限制。
- 未使用用户的真实 API Key，未调用真实付费模型，未验证新小说推理准确率或百万字规模性能。

此版本仍是可运行原型。每块实体/边上限、查询候选数量和歧义名字会影响超长文本召回，原文引用有效不等于语义关系与回答已经完全正确。
