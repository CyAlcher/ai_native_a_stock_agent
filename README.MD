# A股AI决策副驾

> 83个问题 · 11个交易节点 · 支持 Claude Code / Codex CLI / Gemini CLI / Cursor

散户交易全周期的AI提示词库。覆盖从空仓观望到复盘总结的每一个决策节点，输入股票名称直接输出结构化分析。

---

## 一键安装

```bash
git clone https://github.com/CyAlcher/ai_native_a_stock_agent.git
cd ai_native_a_stock_agent
bash install.sh
```

脚本自动检测你安装了哪个 AI 工具，直接装好。也可以指定：

```bash
bash install.sh claude    # Claude Code
bash install.sh codex     # Codex CLI
bash install.sh gemini    # Gemini CLI
bash install.sh cursor    # Cursor
bash install.sh all       # 全部安装
```

---

## 使用方式

安装后，在对应工具里直接输入：

```
统联精密 301168 今天回调了8%，能建底仓吗？
五粮液 000858 赚了5个点，要不要止盈？
贵州茅台 600519 破了20日线，要出来吗？
```

或者用命令直接指定节点和问题编号：

```
/gu/buy-q1   统联精密 301168 今天回调了8%
/gu/hold-q2  五粮液 000858 跌了3个点
/gu/profit-q1 贵州茅台 600519 赚了5个点
```

每个命令背后都是一套结构化的提示词模板，AI 会按预设的分析维度输出结论：

<p align="center">
  <img src="imgs/prompt_template.png" alt="提示词模板示例" width="800">
</p>

---

## 11个交易节点 · 83个问题

| # | 节点 | 命令前缀 | 问题数 | 典型问题 |
|---|------|---------|--------|---------|
| 01 | 空仓观望 | `/gu/watch-q*` | 7 | 现在能进场吗？感觉要踏空了 |
| 02 | 信息搜集 | `/gu/research-q*` | 9 | 帮我看看这只票，群里老师推荐的 |
| 03 | 分析决策 | `/gu/analyze-q*` | 8 | 这个位置还能买吗？是不是太高了 |
| 04 | 买入建仓 | `/gu/buy-q*` | 8 | 现在回调了，是不是可以建底仓了 |
| 05 | 持仓波动 | `/gu/hold-q*` | 8 | 跌了3个点了，要不要补仓摊低成本 |
| 06 | 盈利管理 | `/gu/profit-q*` | 8 | 赚了5个点了，要不要落袋为安 |
| 07 | 亏损管理 | `/gu/loss-q*` | 7 | 跌了20%了，还有必要割肉吗 |
| 08 | 触发止损止盈 | `/gu/trigger-q*` | 7 | 破了20日线了，是不是趋势走坏了 |
| 09 | 离场执行 | `/gu/exit-q*` | 7 | 刚卖完就涨停了，要不要追回来 |
| 10 | 复盘总结 | `/gu/review-q*` | 7 | 这次亏了这么多，下次我一定要拿住 |
| 11 | 等待下一次机会 | `/gu/wait-q*` | 7 | 休息了几天手又痒了，现在有什么票能买 |

---

## 各工具详细说明

### Claude Code

```bash
bash install.sh claude
```

安装后，在任意项目目录下打开 Claude Code，直接输入问题或使用 `/gu/*` 命令。

### Codex CLI

```bash
bash install.sh codex
```

安装后，在本项目目录下运行 `codex`，`AGENTS.md` 自动加载路由规则，直接输入问题。

### Gemini CLI

```bash
bash install.sh gemini
```

安装后，在本项目目录下运行 `gemini`，`GEMINI.md` 自动加载，直接输入问题。

### Cursor

```bash
bash install.sh cursor
```

安装后，用 Cursor 打开本项目，在 Chat 面板直接输入问题。框架规则通过 `.cursor/rules/` 自动加载。

### 任意 AI（DeepSeek / Kimi / 豆包 / ChatGPT）

不需要安装，直接复制框架文件内容：

```bash
# 查看某个问题的框架
cat .claude/commands/gu/buy-q1.md

# 把内容粘贴到任意 AI 的对话框，替换股票名称后发送
```

或者用这个脚本生成可直接粘贴的版本：

```bash
bash render.sh buy-q1 统联精密 301168
```

---

## 文件结构

```
.
├── install.sh                  # 一键安装脚本
├── render.sh                   # 生成可粘贴版本（任意AI用）
├── CLAUDE.md                   # Claude Code 路由规则
├── AGENTS.md                   # Codex CLI 路由规则
├── GEMINI.md                   # Gemini CLI 路由规则
├── .claude/commands/gu/        # 83个分析框架文件（主数据源）
│   ├── buy-q1.md
│   ├── hold-q2.md
│   └── ...
├── prompt_template/            # 原始模板（含变量占位符）
├── question.csv                # 83条问题原始数据
├── sanhu_expt_prompt.py        # 用 DeepSeek 批量生成提示词
└── build_data.py               # 生成 index.html 静态检索页
```

---

## 关注作者

左边是公众号，更新项目动态与 AI × A股 的实战内容；右边是我的个人微信，交流、反馈、提 bug 都欢迎。

<table>
  <tr>
    <td align="center">
      <img src="imgs/gongzhonghao.jpg" alt="微信公众号" width="200"><br>
      <sub>微信公众号</sub>
    </td>
    <td align="center">
      <img src="imgs/kefu.png" alt="个人微信" width="200"><br>
      <sub>个人微信（交流 / 反馈）</sub>
    </td>
  </tr>
</table>

---

## 免责声明

本工具仅为决策辅助，所有输出内容由 AI 生成，不构成任何投资建议。投资有风险，入市需谨慎。
