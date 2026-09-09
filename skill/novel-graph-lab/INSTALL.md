# 把 Novel Graph Lab 装到你的 Agent 上

本技能是一个自包含目录：`SKILL.md`（工作流说明）、`references/`（项目模板说明）、`scripts/launch.py`（定位或拉起配套项目）和 `assets/project/`（可独立运行的精简项目，Python 3.10+ 标准库即可，无第三方依赖）。

## 安装

从 [Releases](https://github.com/fuxiaoji/novel-graph-lab/releases) 下载 `novel-graph-lab-skill.zip`，解压出 `novel-graph-lab` 文件夹，放进你所用 agent 的技能目录：

| Agent | 技能目录 |
|---|---|
| Codex CLI | `~/.codex/skills/novel-graph-lab` |
| Claude Code | `~/.claude/skills/novel-graph-lab` |
| 其他兼容 SKILL.md 约定的工具 | 其对应的 skills 目录 |

也可以克隆仓库后运行 `python tools/package.py --install-dir <技能目录>`，它会同步最新代码到 `assets/project` 并安装技能副本。

## 配置

- `NOVEL_API_KEY`：Chat Completions API 密钥（只从环境变量读取，绝不写入输出）。
- `NOVEL_API_BASE` / `NOVEL_API_MODEL`：`cli.py` 的默认服务地址与模型。
- `NOVEL_GRAPH_LAB_HOME`：指定某个项目 checkout；未设置时 `launch.py` 依次查找技能旁的仓库、当前目录和内置 `assets/project`。
- 可选：本机 Ollama 运行 `bge-m3` 以启用三路稠密检索（AGM-S/R/D 的 `--dense-mode required`）。

## 使用

安装后对 agent 说类似“用 novel-graph-lab 处理这本小说并回答……”，或直接命令行：

```bash
python cli.py --novel book.txt --question "Who did it and how?" \
  --method agm_s --base-url https://open.bigmodel.cn/api/coding/paas/v4 \
  --model glm-5.3 --pass1-group 24 --pass2-chars 6000 --build-max-tokens 1600 --workers 40
```

大上下文模型务必带 `--pass1-group/--pass2-chars` 批量参数，`--workers N` 可并发取独立批次（结果顺序不变）；小上下文模型用默认逐块模式。四种方法：`agm_s`（三路证据扩展）、`agm_r`（图谱候选重排）、`agm_d`（双阅读器仲裁）、`walk`（逐节点读取、逐边选择的工具导航）。输出 `graph.json`（可复用）、`session.json` 与单文件 `replay.html`。
