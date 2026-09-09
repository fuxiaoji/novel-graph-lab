# Novel Graph Lab

让完整小说变成可复用的证据图谱，比较不同检索方法，回放模型读取节点与选择关系的实际操作。

[在线交互 Demo](https://fuxiaoji.github.io/novel-graph-lab/) · [English](README.md) · [日本語](README.ja.md) · [Español](README.es.md) · [下载项目与 Skill](https://github.com/fuxiaoji/novel-graph-lab/releases) · [媒体素材](docs/promo/README.md)

![完整图谱与原文证据](docs/images/overview.png)

## v0.4 更新：整部长篇小说 Demo

Demo 换成公版长篇小说《月亮宝石》（Wilkie Collins，1868，全书 1,073,378 字符，约为旧短篇的 25 倍），用 GLM-5.3 重建：**427 节点 / 1,460 边证据图谱（孤立率 0.7%）**，建图仅 109 次调用；3 个预先固定的问题 × 4 种方法共 12 份真实回答，全部通过逐字引文审计。

面向约 1M 上下文模型的批量参数（`--pass1-group`、`--pass2-chars`、`--workers` 并发）把建图调用从逐块方式的约 760 次降到约七分之一；引文校验升级为空白串不敏感匹配（模型把换行折叠为空格时仍可命中），但入库引文永远取原文精确切片。v0.3 曾把误打包的早期 Dashboard 示例替换为后来研究内核的可搬迁实现（逐字情节筛选、v4 关系优先建图、人物归并、质量检查、AGM-S/R/D 与逐节点工具导航）。详见[内核谱系](../docs/kernel.md)。

这是完整长篇上的端到端演示，**不是超长小说性能或准确率基准测试**。[运行清单](examples/demo-manifest.json)记录模型、源文哈希、内核哈希、用量、批量参数和图谱质量。

## 四种方法

| 方法 | 如何使用图谱 |
| --- | --- |
| AGM-S · 证据扩展 | BM25 + BGE-M3 + 带关系权重的 16 轮个性化 PageRank，三路融合后读取最多 6 块原文 |
| AGM-R · 图谱重排 | 从图谱文档形成最多 28 张候选卡，由模型重排并读取最多 8 块原文 |
| AGM-D · 分歧仲裁 | S/R 两条路径独立回答；结论不一致时，裁判依据证据并集重新判断 |
| 逐节点工具导航 | 每读取一个节点的原文，再选择一条真实邻接边；校验通过才移动到下一节点 |
| 金标叠加 | 每题关键答案实体（`examples/demo-gold.json`）以金环标出；被当前方法实际检索到的节点脉冲亮金高亮，侧栏显示各方法命中数 |

S/R/D 对应后续 G7/G9/G10 的移植接口。后两种组合并不保证每题更好。旧研究的正确率来自不同模型和两个建图队列，不能直接当作本软件或 GLM 的成绩。导航模式尚无正确率优势声明。[完整方法来源与移植差异](docs/kernel.md)。

![检索与选边回放](docs/images/retrieval.png)

## 本机运行

需要 Python 3.10+，Python 代码不需要额外 pip 包，前端没有 CDN 和构建步骤。

```bash
git clone https://github.com/fuxiaoji/novel-graph-lab.git
cd novel-graph-lab
python server.py --open
```

Windows 也可以双击 `start.cmd`。打开 http://127.0.0.1:8765，导入 TXT / Markdown，输入 API Base URL、模型和 Key，选择方法后提问。第一次先建完整图，以后复用。

新 Demo 使用本机 Ollama 的 BGE-M3，向量不会发送到额外远程服务：

```bash
ollama pull bge-m3
ollama serve
```

前端可选「必须使用 BGE-M3」以保持三路检索；自动模式连接失败会明确提示降为 BM25 + 图谱。逐节点导航无需向量服务。

GLM Coding 接口为 `https://open.bigmodel.cn/api/coding/paas/v4`，Demo 模型为 `glm-5.3`。使用其他供应商时，填入兼容 Chat Completions 的 URL 与模型名称。密钥只保存在当前任务内存，发布文件不包含密钥。

## 命令行与重新生成 Demo

密钥通过进程环境变量 `NOVEL_API_KEY` 提供，不写入命令参数、源码或 Git。

```bash
python cli.py --novel novel.txt --question "哪些线索推翻了嫌疑人的证词？" --method agm_d --dense-mode required --base-url https://your-provider.example/v1 --model YOUR_MODEL --out outputs/my-novel
python cli.py --graph outputs/my-novel/graph.json --question "关键线索怎样相连？" --method walk --model YOUR_MODEL --out outputs/next
python tools/run_demo.py --model glm-5.3   --source examples/the-moonstone.txt --title '月亮宝石 · The Moonstone'   --source-url https://www.gutenberg.org/ebooks/155   --story 'The Moonstone' --author 'Wilkie Collins'   --scope 'complete full-length public-domain novel (1868); exploratory functional run, not a benchmark'   --questions examples/moonstone-questions.json --pass1-group 24 --pass2-chars 6000 --build-max-tokens 16000
```

最后一条命令会从公开小说原文运行新建图与全部 12 份问答（大上下文批量参数见上文），保存 `outputs/moonstone/graph.json`、`session.json`、`manifest.json`。用 `tools/audit_demo.py` 审计后，将 session 作为新的 `examples/demo.json`，再执行 `python tools/build_demo.py --public --out docs/index.html`。

## 图谱指标与动画

默认先展示完整三维力导向图，包含孤立节点；播放时在全图高亮路径，可手动切换问题子图。节点和关系可点选核对原文。

- 孤立节点率：没有连接到其他节点的节点数 / 全图节点数。
- 节点原文覆盖率：节点证据字符区间取并集 / 全文字符数，重叠不重复计算。
- 覆盖率与问答正确率不同；缺少全文或位置的导入图显示「无法计算」。
- 工具导航每次只接受当前节点的真实邻接边，最多读取 8 个节点，并阻止循环与无效边。
- 光点回放实际传播或选边记录；简短说明是证据摘要，不展示模型私有思维链，播放速度不代表 API 推理速度。

## 保存与 Skill

网页可以导出图谱与问答 JSON、自包含动画 HTML，再载入图谱继续提问。CLI 在回答前保存图谱，回答失败不丢失建图结果。

从 Releases 下载 `novel-graph-lab-skill.zip` 并解压到 `~/.codex/skills/`。使用 `$novel-graph-lab`；`NOVEL_GRAPH_LAB_HOME` 可指定项目位置。Skill 包包含新内核和新 Demo 的可运行模板。

## 用量与验证

默认 1,500 字符一块、重叠 100 字符，每个未缓存块需要约 2 次请求，另有人物归并调用。每题按方法约 2–10 次请求。已完成调用可缓存复用；停止会在当前 API 请求返回后生效。

小说与问题会发送到你选择的 API。缓存及导出含原文证据。服务仅绑定本机，不适合直接公开为多人 API。

```bash
python -m unittest discover -s tests -v
node tests/test_graph_utils.cjs
```

12 项后端测试覆盖原文校验、缓存、API/导出、真实边传播、逐节点导航和仲裁。真实 GLM Demo 是功能运行证据，不能替代独立准确率评测。CI 尚未启用，模板见 [tests.workflow.yml](docs/tests.workflow.yml)。

小说来自 [Project Gutenberg](https://www.gutenberg.org/ebooks/1661)，保留[来源许可证](examples/GUTENBERG-LICENSE.txt)。代码使用 [MIT License](LICENSE)。[来源说明](NOTICE.md) · [验证记录](QA.md)。
