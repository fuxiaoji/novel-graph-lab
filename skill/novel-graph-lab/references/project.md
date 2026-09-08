# 配套项目

项目位置可通过环境变量 `NOVEL_GRAPH_LAB_HOME` 指定。启动脚本依次检查该变量、技能所在仓库、当前目录和技能目录中的自包含 `assets/project`。

`assets/project` 是可复制的精简项目模板，包含 core.py、kernel_build.py、kernel_retrieve.py、research_prompts.py、server.py、cli.py、web、examples、tools 和 tests。第一次复制到新目录后，可以运行 `python server.py --open`。新内核 Demo 的 `examples/demo.json` 已经打包；如需单 HTML，可从网页导出，或调用 `tools.extract_demo.standalone`。

主要文件：

- `core.py`：API、分块、BM25 与新内核入口。
- `kernel_build.py` / `research_prompts.py`：双遍关系优先建图、人物归并与质量报告。
- `kernel_retrieve.py`：AGM-S/R/D、BGE-M3 接口、逐节点工具导航和引用验证。
- `server.py`：仅本机访问、后台任务、阶段事件和停止标记。
- `web/app.js`：Canvas 三维投影、事件驱动光点、证据面板、离线导出。
- `tools/extract_demo.py`：从原附件静态 JSON 提取，不运行附件 JS。
- `cli.py`：批处理，密钥只读环境变量，先保存图谱再生成回答。

模型请求使用 Chat Completions JSON 内容协议。用户指定的服务须支持 `messages`、`model`、`max_tokens`，并遵循 JSON 输出指令；如果接口错误、输出截断或格式无效，保留缓存并报告实际错误，不以模拟结果替代。

项目定位不是自动授权修改任意旧研究工程。默认在独立项目或其副本中操作。缓存包含小说派生内容，输出会包含原文证据。用户未请求清理时保留这些可复用成果。
