#!/usr/bin/env bash
# ============================================================
# render.sh — 生成可直接粘贴给任意 AI 的提示词
# 用法：bash render.sh <命令名> <股票名称> <股票代码> [补充情况]
# 示例：bash render.sh buy-q1 统联精密 301168 今天回调了8%
# ============================================================

export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CMD_DIR="$REPO_DIR/.claude/commands/gu"

CMD="$1"
STOCK="$2"
CODE="$3"
EXTRA="${4:-}"

# ── 参数校验 ──────────────────────────────────────────────
if [[ -z "$CMD" ]]; then
    echo "用法：bash render.sh <命令名> <股票名称> <股票代码> [补充情况]"
    echo ""
    echo "可用命令："
    ls "$CMD_DIR" | sed 's/\.md//' | column
    exit 1
fi

if [[ -z "$STOCK" || -z "$CODE" ]]; then
    echo "错误：股票名称和代码不能为空"
    echo "示例：bash render.sh buy-q1 统联精密 301168"
    exit 1
fi

CMD_FILE="$CMD_DIR/${CMD}.md"
if [[ ! -f "$CMD_FILE" ]]; then
    echo "错误：找不到命令文件 $CMD_FILE"
    echo "可用命令："
    ls "$CMD_DIR" | sed 's/\.md//'
    exit 1
fi

# ── 提取分析框架（跳过 frontmatter 和执行说明，只保留框架正文）
# 文件结构：
#   --- frontmatter ---
#   ## $ARGUMENTS 解析  （跳过）
#   ## 执行             （跳过）
#   --- 分隔线 ---
#   <分析框架正文>      ← 我们要的
#   ---
#   > 免责声明
# ──────────────────────────────────────────────────────────
FRAMEWORK=$(python3 - "$CMD_FILE" "$STOCK" "$CODE" "$EXTRA" <<'PYEOF'
import sys, re

cmd_file = sys.argv[1]
stock    = sys.argv[2]
code     = sys.argv[3]
extra    = sys.argv[4] if len(sys.argv) > 4 else ""

with open(cmd_file, encoding="utf-8") as f:
    content = f.read()

# 去掉 frontmatter（第一个 --- 到第二个 ---）
content = re.sub(r'^---\n.*?\n---\n', '', content, count=1, flags=re.DOTALL)

# 去掉 ## $ARGUMENTS 解析 和 ## 执行 两个 section（到下一个 --- 为止）
content = re.sub(r'## \$ARGUMENTS 解析.*?---\n', '', content, flags=re.DOTALL)
content = re.sub(r'## 执行.*?---\n', '', content, flags=re.DOTALL)

# 去掉末尾的免责声明行
content = re.sub(r'\n> ⚠️.*', '', content)

# 替换变量
content = content.replace('$STOCK', stock).replace('$CODE', code)

# 注入补充情况
if extra:
    content = f"补充情况：{extra}\n\n" + content.lstrip()

print(content.strip())
PYEOF
)

# ── 输出 ──────────────────────────────────────────────────
echo "# ${STOCK}（${CODE}）"
echo ""
echo "$FRAMEWORK"
echo ""
echo "> ⚠️ 本回答由 AI 生成，内容仅供参考，不构成投资建议，请仔细甄别。"
