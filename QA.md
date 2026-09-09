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


## 2026-09-09 v0.4 长篇小说 Demo 验证

- 源文：公版《月亮宝石》全书 1,073,378 字符（Gutenberg #155，去头尾保留正文），许可文件保留。
- 建图：glm-5.3，大上下文批量（pass1_group=24，pass2_chars=6000，max_tokens=16000，串行）；109 次调用 / 约 81 万 token。逐块旧方式估算需 760+ 次。
- 质量与审计：`tools/audit_demo.py` 通过——427 节点 / 1,460 边，孤立率 0.7%，边点比 3.42，拒绝率 4.3%；12 条回答引用全部可回放定位，0 警告；walk 三问分别为 5/4/2 次节点读取，停止原因 model_stop / repeated_edge / invalid_action（保留原始记录，未挑选成功样本）。
- 引文校验升级：空白串不敏感匹配（GLM-5.3 会把换行折叠为空格），入库引文一律取原文精确切片；冒烟测试中拒绝引文从 87 降至 0。
- 单元测试 13 项全部通过（新增 wide 批量路径测试）；`build_demo --public` 重建页面，内嵌 12 条回答。
- 已知限制：节点数低于 30 本 DQA 研究图谱的均值，因全书更长且全局名称去重；这是端到端功能演示，不是准确率或超长文本性能基准。

## 2026-09-09 金标叠加验证

- 金标定义：`examples/demo-gold.json`，按问题列出已知答案关键实体组（含同义节点名），页面加载时按节点名/别名解析为节点 ID；全部名称均可在图中解析。`build_demo` 会把它合并进公开页面，`examples/demo.json` 同步包含。
- 命中口径：该方法的 trace 步骤 node_ids ∪ evidence node_ids 中出现组内任一节点即算命中。
- 浏览器实测（本地 server 与静态自包含页各一次）：Q1 AGM-S 显示「金标命中 3/6 组」，★/☆ 芯片正确；切换 walk 后变为 1/6。画布像素校验：亮金命中标记与金环未命中标记均有非零像素。
- 修复一个前端 bug：`refreshGoldIndex` 中 `.filter` 误作用于 [问题, 组] 二元组导致 Map 值为 undefined、金标不显示；改为先构建条目再过滤。
- 预计算命中（Python 复核）：Q1 s/r/d/walk = 3/6、4/6、3/6、1/6；Q2 = 4/4、4/4、4/4、2/4；Q3 = 5/5、5/5、5/5、3/5。值得注意：Q1 四种方法轨迹均未触及 Franklin Blake 节点（回答文本正确但检索轨迹未经过该节点）。

## 2026-09-09 金标解析修正：别名遮蔽

- 发现并修复：gold 组名解析时别名与精确名混在一个 Map 里按插入顺序占位，导致 "Franklin Blake" 被更早出现的节点别名（n12 "Mr. Franklin" 的别名）遮蔽，命中判定全部偏误。修复为**先精确节点名、后别名**两遍构建（`web/app.js` 与 `promo/make_video.py` 同步修复）。
- 修正后各方法命中（trace ∪ evidence 口径）：
  - Q1 谁拿走宝石：AGM-S 4/6（漏 Ezra Jennings、Mr. Candy 两位人证）、AGM-R 5/6、AGM-D 4/6、walk 2/6（命中真凶+药物，漏掉物证与地点）。
  - Q2 宝石流转：4/4、4/4、4/4、3/4。
  - Q3 锡盒：5/5、5/5、5/5、3/5。
- 此前日志里 "Q1 四种方法均未触及 Franklin Blake" 的结论是遮蔽 bug 的伪象：n111（Franklin Blake，全图最高连通度的主角节点）实际被全部四种方法触达。真正稳定的洞察是：**AGM-S/R/D 拿到物证链但漏人证，walk 触及人证却漏物证**。
- 公开页 `docs/index.html` 已用修复后的脚本重建。
