# Novel Graph Lab

**阅读完整故事，追溯每条证据。**

将长篇小说转成可复用的知识图谱，带着问题检索原文，再通过三维动画回放证据路径。

[在线交互 Demo](https://fuxiaoji.github.io/novel-graph-lab/) · [English](README.md) · [下载项目与 Skill](https://github.com/fuxiaoji/novel-graph-lab/releases)

[![完整小说图谱和原文证据](docs/images/overview.png)](https://fuxiaoji.github.io/novel-graph-lab/)

## 先看 Demo

在线版本无需登录或 API，包含原研究演示的 **739 个节点、1,886 条边、7 个历史问题**。

- 首先展示完整力导向图，包含 **92 个孤立节点（12.4%）**。
- 拖拽旋转、滚轮缩放、点击节点查看证据和关系。
- 选择问题后播放检索动画，支持暂停、逐步、倍速和拖动时间轴。
- 默认在全图上高亮检索；主动勾选后才切换到问题子图。
- 光点表示可观察的检索和引用路径，文字是证据摘要，不代表模型内部私有思维链。

在线 Demo 仅回放历史记录，不接收 API 密钥。新小说与真实问答请在本机运行。

![关系扩散与证据检索](docs/images/retrieval.png)

## 三步开始

只需 **Python 3.10+**。运行项目不需要第三方 Python 包、Node 或前端依赖，也不需要 CDN。

```bash
git clone https://github.com/fuxiaoji/novel-graph-lab.git
cd novel-graph-lab
python server.py --open
```

Windows 也可以双击 `start.cmd`。默认打开 [127.0.0.1:8765](http://127.0.0.1:8765)，端口占用时可加 `--port 8767`。

1. 点击「导入小说」，选择 TXT / Markdown，支持 UTF-8 和 GB18030。
2. 填写 Chat Completions 兼容的 Base URL、模型 ID 和 API Key。本地模型可留空 Key。
3. 输入问题，点击「检索并回答」。首次逐块建图，之后复用图谱。

接口使用 `POST {base_url}/chat/completions`，需要支持 `model`、`messages`、`max_tokens` 和 JSON 指令。模型名称按服务商实际提供的 ID 填写，未实现各家私有扩展参数。远程 API 使用 HTTPS，本地模型可使用 localhost HTTP。[接口文档参考](https://api-docs.deepseek.com/api/create-chat-completion/)

## 图谱如何帮助问答

**全文分块 → LLM 抽取 → 引文逐字验证 → 完整图谱 → 查询规划 → BM25 定位 → 两轮关系扩散 → 原文补充检索 → 带引用的回答。**

保留人物、地点、时间、物件、事件、证词和矛盾。原文不会先被删除，抽取遗漏的内容仍可通过原文补充检索找到。中文采用双字切分，英文按词匹配。

新图谱的节点和边引文必须逐字存在于对应块，关系保存字符位置。名字只做大小写/空白标准化；别名参与检索，不强行合并歧义人物。回答中不存在的引用会标记。

## 指标口径

| 指标 | 定义 |
| --- | --- |
| 节点数、边数 | 完整图谱总量，筛选子图后保持不变 |
| 孤立节点率 | 没有连接到其他节点的节点数 / 总节点数；自环不算连接到其他节点 |
| 节点原文覆盖率 | 节点证据在全文中的字符区间取并集 / 全文字符数；重叠只算一次 |
| 无法计算 | 缺少完整原文或位置，不能把摘录长度当作全文长度 |

旧 Demo 的完整小说与坐标没有保存，因此覆盖率显示「无法计算」。新导入小说可计算。引用覆盖率不等于问答准确率。

## 保存、复用与 Skill

- 「保存图谱与问答」导出 JSON，之后载入即可继续问。
- 「导出交互回放」生成自包含 HTML，可离线打开和分享。
- 网页导出同时写入本地 `outputs/exports/`。
- CLI 在问答前保存 `graph.json`，回答失败不丢失已完成的图谱。

将密钥放入环境变量 `NOVEL_API_KEY`，不要放在命令参数或提交到仓库。`NOVEL_API_BASE`、`NOVEL_API_MODEL` 可设置默认值。

```bash
python cli.py --novel novel.txt --question "凶手如何离开现场？" --base-url https://your-provider.example/v1 --model YOUR_MODEL --out outputs/my-novel
python cli.py --graph outputs/my-novel/graph.json --question "哪些证词相互矛盾？" --model YOUR_MODEL --out outputs/question-2
```

示例域名是占位符，请替换为实际 API。编码可用 `--encoding gb18030`。成功输出 `graph.json`、`session.json`、`replay.html`。

从 [Releases](https://github.com/fuxiaoji/novel-graph-lab/releases) 下载 `novel-graph-lab-skill.zip`，解压到如 `~/.codex/skills/` 的技能目录。使用 `$novel-graph-lab`，也可通过 `NOVEL_GRAPH_LAB_HOME` 指定项目位置。发布包包含可运行项目模板。

## 费用、隐私与边界

默认每块约 5,000 字符，未缓存块约 1 次建图请求，每个问题约 2 次模型请求；网络或限流可能触发有限重试。已完成分块缓存可复用。停止会等当前请求返回后生效。输入文件上限 20 MB，请求上限 40 MB。

Key 只保存在页面和当前任务内存，不写入缓存、日志或导出。运行后，小说分块与问题会发送到你配置的 API。缓存和导出图谱可能包含小说原文。服务只绑定 127.0.0.1，不适合直接公开部署成多人服务。

这是可运行的研究原型。固定召回预算、局部抽取、歧义名字可能导致漏检；引文存在不代表关系和答案必然正确。自动测试和本地模拟 API 已验证功能流程，**尚未宣称真实模型准确率、百万字性能或相对其他方法的提升**。历史动画按已存节点和真实边重建，不补造缺失的规划与日志。

## 开发与来源

```bash
python -m unittest discover -s tests -v
node tests/test_graph_utils.cjs
python tools/build_demo.py --public --out docs/index.html
```

Node 只用于前端测试。更多细节见 [英文文档](README.md)、[验证记录](QA.md)、[设计说明](docs/design.md) 和 [贡献指南](CONTRIBUTING.md)。

项目由作者的 [Novel KG Studio](https://github.com/fuxiaoji/novel-kg-studio) 研究演示提取，独立重写本地服务、证据验证、检索与界面。应用代码使用 [MIT License](LICENSE)，文学摘录见 [NOTICE.md](NOTICE.md)。

GitHub 自动测试尚未启用。[CI 模板](docs/tests.workflow.yml) 已提供；使用具备 workflow 权限的凭据将其复制到 `.github/workflows/tests.yml` 即可启用 Python 3.10 / 3.13 测试。
