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

## 2026-09-09 科普视频 v3（重构）

- 结构改为真正的科普片三幕：序幕"思维宫殿"（侦探两次梳理动画：碎片筛选→关系连线，对应 pass1/pass2）→ 第一幕"机制"（Transformer 注意力距离衰减 3D 曲面 + 衰减曲线 + 1.07M 字符 vs 16K 窗口动画 → 双轴解压 → 图谱凝聚 → skill 打包）→ 第二幕"一个案子"（问题→三物证→金标→洞察→四方法 trace）→ 第三幕"成果"（全部取自 novel-kg-studio 论文报告）→ 片尾。
- 成果数字：G7 53.8% ≈ 公平金标预言机 54.7%（p=0.912）、G9 50.9%、G10 53.4%（新小说队列 58.6%）、RAG 51.7%、压缩 51.3%、尾窗 46.2%、仅题目 40.2%；13 道双基线全错的独赢题图谱全对、其中 10 道官方金标也错；金标关键词 97% 在图谱节点。口径常驻画面（exploratory · 9B · 16K）。
- 修复音频重叠根因：此前案情段解说语速顶满仍超时 4.6 秒并写入音轨，压住后续段落。新 make_narration.py 按场景硬隔离——超时直接抛错、段尾 80ms 钳位淡出、程序化校验段间零重叠（实测 17 段最小间隔 0.83s）。
- BGM（原创合成）新增解说闪避（活跃时约 -7dB）；两版配音（bm_george 男声 / af_heart 女声）语速均为 1.1。
- 全片 173.5s、60fps、1280×720，场景间 0.5s 交叉溶解。三版（无声/男声/女声）已上传 Release v0.4.0。

### v3 补充：逐帧/逐段核查结论（同日）

- 用户反馈"音画不同步、台词缺失、停顿"。逐项核查：混流层零偏差（成片音轨与 final_mix 相关性 1.0000、17/27 段逐一相关 ≥0.9999）；帧序号抽帧（n=1440/3540/5520/7500/9240）确认场景时间轴正确。上一版的真实缺陷是内容层的：案情段解说溢出 4.6 秒（已修）、部分场景无解说（chunks 静默）、解说不跟字幕导致最长 9.9 秒空白。
- 解说改为**逐字幕对齐**：27 段、每条字幕一句，语音严格落在字幕窗口内；make_narration.py 对超时直接抛错（迭代中拦下 8 处溢出），段尾 80ms 钳位。最终 0 溢出，段间最大空白 6.2s（为注意力收尾节拍），其余 ≤4.4s。
- 视频端微调：axes 字幕窗加宽、case 15s、results_cubes 12s、results_bar 字幕窗重排；场景交叉溶解 0.5s。
- 教训：`-ss` 输入寻帧在个别混流产物上偏差，核查一律改用帧序号 select 抽帧；音画核查用"逐段相关性 + 帧序号抽帧"双证据。

### v4：单一数据源 + 侦探片头 + 台词加密（同日）

- **根治漂移**：新增 `promo/timeline.json` 作为字幕与台词的唯一数据源——`make_video.py` 从它取场景时长与字幕、`make_narration.py` 从它取台词（每条字幕恰好一句配音，en 字幕即配音原文）。两端不再各写一份，结构上不可能再失步。
- **新片头（按用户脚本）**：福尔摩斯剪影（猎鹿帽+烟斗+侧脸，矢量绘制）→ "顶级侦探是怎么破案的" → 把案件事实按 Day 1/2/3 排到时间轴（4 张卡片按时间落位）→ 用真实图谱生成思维导图（427 节点，标出 Franklin Blake / laudanum / nightgown）→ 引出"AI 为什么做不到：注意力与旋转位置编码被输入长度稀释"，接注意力衰减演示。
- **台词与字幕全部重写加密**：29 条，平均 2.37 词/秒（此前 27 条短句且断续）；最短窗口 5.6s、最长 12s；解说段间空白上限从 9.9s 降到 5.28s，下限 1.54s。
- **成果幕加密度**：柱状图幕讲 53.8% 与金标预言机 p=0.912；立方体幕增加基线对比小柱（RAG 51.7 / 压缩 51.3 / 尾窗 46.2 / 仅题目 40.2）；新增"10 部新小说升至 58.6%"与"97% 覆盖"口径。
- **验证**：成片 4 分 30 秒；29 段配音 0 溢出、逐段与混音相关性最差 0.9998；帧序号抽帧核对 t=2s（剪影）/11s（梳理）/19s（导图）/250s（基线）全部符合设计。
- 版式修正：梳理卡片改为按时间轴落位（不再重叠）并在进入导图前淡出；基线小柱移到独立底带，不再压住立方体。

### v5：收紧换页停顿（同日）

- 问题：场景之间静默最长 5.28s，像 PPT 换页在等。根因是场景时长按"动画最短需求"取大值，多出的时间全成了片尾静默。
- 方案：新增 `promo/_retime.py`——先用 Kokoro 实测每句台词真实时长（两种音色取较慢者），再**按场景内相对定位**重排：字幕间隔固定 1.05s（含 LEAD/TAIL/MARGIN），场景时长 = max(该幕动画最短时长, 该幕台词总长 + 0.5s 落点)，并断言每条字幕都落在自己那一幕内。
- 结果：片长 4:30 → **3:37**；句间停顿 最长 5.28s → **1.82s**（平均 1.47s，最短 1.10s）；语音覆盖全片 **80.2%**；29 段 0 溢出、逐段相关性全部 >0.9。
- 片头节奏同步提前（剪影 0-5.4s / 梳理 5.8-12.4s / 导图 11.8s 起），第三条台词加密以覆盖导图阶段。
- 帧核对：t=3s 剪影、t=9s 按时间梳理、t=15s 思维导图。

### v5.1：成果立方体幕版式修正

- 用户反馈：左下角基线柱组被字幕条挡住（柱标签 RAG/Compr./Tail/Q0 不可见，且"EVERY BASELINE TRAILS"与 51.7 数值重叠）。
- 修正：立方体两行上移（214 / 320），基线柱组整体上移至基线 y=556、柱高上限 150px，组标题移至 y=366，右侧说明文字移至 400/436/468——全部落在字幕条（y>=610）之上，互不遮挡。
- 已重渲染并核对成片该帧（t=205s）无误。

## 2026-09-19 剪映 MCP 安装 + 真实录屏预告片

- **剪映 MCP 安装**：官方 marketplace 无剪映插件，改装社区方案 `jianying-ai-mcp`（验证基线 剪映专业版 10.0.5.13816）：
  - 仓库：`D:/desktop/coding/科研/mcp/jianying-ai-mcp`，`uv venv --python 3.12` + `pip install -e .`（依赖 mcp + pyJianYingDraft）
  - 注册到 ZCode：`~/.zcode/cli/config.json` → `mcp.servers.jianying-ai-editor`（stdio，含 JIANYING_DRAFT_ROOT / JIANYING_EXE / 工作目录）
  - Skill 安装到 `~/.zcode/skills/jianying-ai-editor`（来自仓库 `skills/`）
  - stdio 冒烟测试通过，8 个工具可用：`get_jianying_capabilities`、`build_draft`、`build_from_reference`、`batch_from_template`、`analyze_reference_draft`、`analyze_video_source`、`save_video_observations`、`get_video_analysis_context`
- **真实素材录制（沙盒）**：宿主 IAB 的 `recording` 能力未开放、且后台节流 rAF（`S.frame=0`），改为**手动驱动渲染 + 逐帧抓 canvas**（`frame(t)` 合成时钟 + `toDataURL`），得到 5 段真实渲染素材（rotate/replay/walk/focus/gold，共 750 帧 @30fps）+ 5 张 1920×1080 全页 UI 截图（demo 首页、回答+引用、金标命中、节点详情、问题页）。
- **100 秒预告片**（按用户提供的脚本与视觉规范：深色 #0A0C0F + 琥珀 #F2B544，每 3–5 秒一次视觉事件，真实录屏主导）：
  - 12 幕：钩子 → 项目名 → 线索分散问题 → 数据规模（count-up：107 万字符 / 427 节点 / 1,460 边）→ 交互系统 → 提问 → 路径追踪（核心）→ 原文证据可追溯 → 四种策略卡 → 批处理 ~760→109 → CTA → 片尾
  - 音频：12 段英文旁白（Kokoro，硬隔离断言全部通过）+ 原创深色氛围乐 + 界面音效（pop/whoosh/tick，闪避混音）
  - 成片：`novel-graph-lab-trailer.mp4`（101s，1920×1080，AAC）、女声版、无声版、30 秒短版（男/女声）
  - 验证：成片音轨与混音相关性 1.0000；12 段旁白逐段相关性最差 0.9999；抽帧核对 6 个关键点
- **剪映可编辑草稿**：通过 MCP `build_draft` 生成 `NovelGraphLab_Trailer_100s`（video 12 段 + audio 1 轨 + text 12 条字幕，1920×1080/30fps，duration 101s），先 dry_run 校验再发布，路径在剪映草稿目录下，可直接在剪映中微调导出。

### 2026-09-19 开篇重构 + 1920×1088 修正 + 剪映草稿更新

- **开篇 32.5s（新增）**：按需求把 30 秒段重做成整片开头，叙事改为「让你的 AI 像顶级侦探一样思考」→「装上一个 skill，把整本小说变成侦探式思维导图」→「AI 用这张图思考：沿关系检索证据」→「你也可以用它阅读：观察思维导图辅助理解」→「接下来，完整看一遍它是怎么工作的」。素材仍是真实录屏（图谱旋转 / 聚焦 / 检索回放 / 金标 UI 截图）。
- **整片 4:09.47**：开篇（1280×720@60，从 1080p 干净降采样）+ 长片（3:37）。音频用「逐段拼接再合流」构建（opening_audio + final_mix_george），避免 `-c copy` 拼接 AAC 造成的 priming 错位。
- **音画验证**：整片 5 个采样点（开篇 0-20s / 25-32s、长片拼接后 0-20s / 100-120s / 200-217s）与源音轨相关性均为 **1.0000**；拼接处逐秒 RMS 无空隙。
- **修正编码黑边**：`imageio_ffmpeg.write_frames` 默认 `macro_block_size=16`，把 1920×1080 补成 **1920×1088**（预告片与开篇都受影响）。已在两个渲染脚本显式设 `macro_block_size=1` 并重渲染；现预告片/短版均为标准 1920×1080。
- **剪映草稿更新**：`NovelGraphLab_Full_4m09s`（开篇 5 幕 + 长片 17 段 = 22 视频片段，1 轨配音 full_audio.wav，17 条中文字幕，250s/1920×1080）。旧的 `NovelGraphLab_Trailer_100s` 保留。

### 补记：开篇字形修正与剪映草稿校正

- 开篇 skill 卡片文案由 `novel → evidence mind map` 改为 `one novel, one evidence mind map`（Georgia 字体缺 → 字形，会渲染成方框）；已重渲染该幕并重出整片。
- 剪映草稿修正：初版误把 100 秒预告片当作长片主体（133s 视频 vs 250s 音频）。改为「开篇 5 段 + 长片按场景切分的 17 段（source_start 指向长片文件）」= 22 个可剪辑片段 + 精确 249.5s 配音轨；去掉了重复的字幕轨（字幕已烧录在画面中）。草稿 `NovelGraphLab_Full_4m09s` 已重新发布，旧 `NovelGraphLab_Trailer_100s` 保留。
- 交付：release 现含整片 `novel-graph-lab-full.mp4`（4:09.47，1280×720@60）+ 预告片 5 版（1920×1080）+ 长片 3 版。

### 补记：女声版整片

- 整片此前只有男声（开篇音频用 bm_george 生成）。已补 `novel-graph-lab-full-female.mp4`：女声开篇（af_heart）+ 女声长片音轨（final_mix_heart.wav）拼接而成。
- 验证：整片 5 个采样点与源音轨相关性 0.9998-0.9999，时长 4:09.47，1280×720@60。
- 剪映草稿同步新增女声版 `NovelGraphLab_Full_4m09s_female`（22 片段 + 女声配音轨），与男声草稿并存，可直接对拍。
- 至此 release 上每支视频均为男/女双声版：整片 ×2、长片 ×2（+无声）、预告片 ×2（+无声）、30 秒短版 ×2。

### 2026-09-19 节奏与配乐调整（v6）

- **开篇加快**：32.5s → **24.0s**。每幕时长按台词实测重排（hook 4.4 / mindmap 5.8 / aithink 6.6 / humanread 4.4 / bridge 2.8），LEAD/TAIL 从 0.35/0.45 收到 0.15/0.30；台词一字未删，只砍掉等待。
- **BGM 换新**：新增共享 `promo/music_bed.py`——104 BPM 律动床（四拍底鼓、反拍 hi-hat、2/4 拍 clap、走动贝斯、和弦点奏、16 分琶音 + 侧链闪避），替换原来的 Am–F–C–G 长垫乐。长片、预告片、30 秒短版与开篇全部改用同一套床。节拍验证：拍长自相关 0.878、8 分音 0.566（有明确律动，不再是持续长音）。
- **重出成片**：整片 4:00.97（开篇 24s + 长片 217s）、长片 3:37、预告片 1:41、短版 0:30，男/女双声；音画验证 8 个采样点相关性 0.9996–0.9999。
- **剪映草稿**：重建为 `NovelGraphLab_Full_4m01s`（男声）与 `_female`（女声），22 个可剪片段 + 对应配音轨；旧 4m09s 草稿已清理。
