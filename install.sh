#!/usr/bin/env bash
# ============================================================
# A股AI决策副驾 — 一键安装脚本
# 支持：Claude Code / Codex CLI / Gemini CLI / Cursor / 通用
# 用法：bash install.sh [--tool claude|codex|gemini|cursor|all]
# ============================================================

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMANDS_SRC="$REPO_DIR/.claude/commands/gu"
TOOL="${1:-}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${CYAN}[info]${NC} $*"; }
success() { echo -e "${GREEN}[done]${NC} $*"; }
warn()    { echo -e "${YELLOW}[warn]${NC} $*"; }

# ── 检测已安装的工具 ──────────────────────────────────────
detect_tools() {
    DETECTED=()
    command -v claude  &>/dev/null && DETECTED+=("claude")
    command -v codex   &>/dev/null && DETECTED+=("codex")
    command -v gemini  &>/dev/null && DETECTED+=("gemini")
    command -v cursor  &>/dev/null && DETECTED+=("cursor")
    # Cursor 也可能只是目录存在
    [[ -d "$HOME/.cursor" ]] && [[ ! " ${DETECTED[*]} " =~ "cursor" ]] && DETECTED+=("cursor")
}

# ── Claude Code ───────────────────────────────────────────
install_claude() {
    DEST="$HOME/.claude/commands/gu"
    info "安装到 Claude Code → $DEST"
    mkdir -p "$DEST"
    cp -r "$COMMANDS_SRC/." "$DEST/"
    # 同时复制顶层入口文件
    cp "$REPO_DIR/.claude/commands/stock.md" "$HOME/.claude/commands/stock.md" 2>/dev/null || true
    success "Claude Code 安装完成（$(ls "$DEST" | wc -l | tr -d ' ') 个命令）"
    echo "   使用方式：/gu/buy-q1 统联精密 301168 今天回调了8%"
}

# ── Codex CLI ─────────────────────────────────────────────
install_codex() {
    DEST="$HOME/.codex/commands/gu"
    info "安装到 Codex CLI → $DEST"
    mkdir -p "$DEST"
    cp -r "$COMMANDS_SRC/." "$DEST/"
    # Codex 用 AGENTS.md 作为项目入口
    cp "$REPO_DIR/AGENTS.md" "$REPO_DIR/AGENTS.md"
    success "Codex CLI 安装完成（$(ls "$DEST" | wc -l | tr -d ' ') 个命令）"
    echo "   使用方式：在项目目录下运行 codex，直接输入问题即可"
}

# ── Gemini CLI ────────────────────────────────────────────
install_gemini() {
    DEST="$HOME/.gemini/commands/gu"
    info "安装到 Gemini CLI → $DEST"
    mkdir -p "$DEST"
    cp -r "$COMMANDS_SRC/." "$DEST/"
    success "Gemini CLI 安装完成（$(ls "$DEST" | wc -l | tr -d ' ') 个命令）"
    echo "   使用方式：在项目目录下运行 gemini，直接输入问题即可"
}

# ── Cursor ────────────────────────────────────────────────
install_cursor() {
    # Cursor 通过 .cursorrules 或 .cursor/rules 加载上下文
    RULES_DIR="$REPO_DIR/.cursor/rules"
    info "安装到 Cursor → $RULES_DIR"
    mkdir -p "$RULES_DIR"
    # 把路由规则写成 cursorrules
    cp "$REPO_DIR/CLAUDE.md" "$RULES_DIR/a-stock-agent.mdc"
    # 把所有框架文件也放进去，Cursor 按需引用
    mkdir -p "$RULES_DIR/gu"
    cp -r "$COMMANDS_SRC/." "$RULES_DIR/gu/"
    success "Cursor 安装完成"
    echo "   使用方式：在 Cursor 中打开项目，直接在 Chat 里输入问题"
}

# ── 通用（复制到项目本地，任何工具都能用）────────────────
install_local() {
    info "本地安装（工具无关）→ $REPO_DIR"
    # 框架文件已在 .claude/commands/gu/，无需额外操作
    success "本地安装完成，框架文件在 .claude/commands/gu/"
    echo "   使用方式：把任意 .claude/commands/gu/*.md 的内容粘贴给任何 AI"
}

# ── 主流程 ────────────────────────────────────────────────
echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   A股AI决策副驾 — 一键安装           ║"
echo "  ║   83个问题 · 11个交易节点             ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

detect_tools

# 解析参数
case "$TOOL" in
    --tool=claude|claude)  install_claude ;;
    --tool=codex|codex)    install_codex  ;;
    --tool=gemini|gemini)  install_gemini ;;
    --tool=cursor|cursor)  install_cursor ;;
    --tool=all|all)
        install_claude
        install_codex
        install_gemini
        install_cursor
        ;;
    "")
        # 自动检测
        if [[ ${#DETECTED[@]} -eq 0 ]]; then
            warn "未检测到已安装的 AI 工具，执行本地安装"
            install_local
        elif [[ ${#DETECTED[@]} -eq 1 ]]; then
            info "检测到：${DETECTED[0]}"
            install_${DETECTED[0]}
        else
            info "检测到多个工具：${DETECTED[*]}"
            echo ""
            echo "请选择安装目标："
            select CHOICE in "${DETECTED[@]}" "全部安装" "退出"; do
                case "$CHOICE" in
                    "全部安装")
                        for t in "${DETECTED[@]}"; do install_$t; done
                        break ;;
                    "退出") exit 0 ;;
                    *) install_$CHOICE; break ;;
                esac
            done
        fi
        ;;
    *)
        echo "用法：bash install.sh [claude|codex|gemini|cursor|all]"
        exit 1
        ;;
esac

echo ""
echo "  ─────────────────────────────────────"
echo "  快速上手："
echo "  统联精密 301168 今天回调了8%，能建底仓吗？"
echo "  五粮液 000858 赚了5个点，要止盈吗？"
echo "  ─────────────────────────────────────"
echo ""
