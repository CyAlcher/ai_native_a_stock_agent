"""
解析 prompt_template/ 目录下的 md 文件，生成可直接访问的 index.html
运行：python build_data.py
"""
import re
import glob
import json
import os
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(script_dir, "prompt_template")
expert_dir = os.path.join(script_dir, "expert_views")

# 1. 找所有模板文件，按文件名排序保证节点顺序
md_files = sorted(glob.glob(os.path.join(template_dir, "*_template.md")))
if not md_files:
    print(f"错误：未找到模板文件，请检查目录 {template_dir}")
    exit(1)
print(f"找到 {len(md_files)} 个模板文件")

# 2. 加载 expert_views/*.md 里的"一段话压缩"段落，供前端切换
def load_expert_view(slug: str, label: str) -> str:
    path = os.path.join(expert_dir, f"{slug}.md")
    if not os.path.exists(path):
        return ""
    text = open(path, "r", encoding="utf-8").read()
    # 抓取 "## 一段话压缩" 下面的第一段
    m = re.search(r"## 一段话压缩[^\n]*\n+([^\n#][^\n]*(?:\n[^\n#][^\n]*)*)", text)
    if not m:
        print(f"  警告：{label}（{slug}）未解析到'一段话压缩'段，跳过。")
        return ""
    return m.group(1).strip()

EXPERTS = [
    {"slug": "",               "label": "不指定（通用分析师）", "body": ""},
    {"slug": "duan-yongping",  "label": "段永平",             "body": load_expert_view("duan-yongping", "段永平")},
    {"slug": "dan-bin",        "label": "但斌",               "body": load_expert_view("dan-bin", "但斌")},
    {"slug": "li-lu",          "label": "李录",               "body": load_expert_view("li-lu", "李录")},
]
print(f"已加载 {sum(1 for e in EXPERTS if e['body'])} 份专家视角")

# 3. 解析每个模板文件
# 格式：# 节点：XXX｜提示词模板
#       ## 问题N｜频次
#       **"问题文本"**
#       ```提示词内容```
prompts = []

for md_path in md_files:
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 从文件名或 h1 标题提取节点名
    h1_match = re.search(r"^# 节点：(.+?)｜", content, re.MULTILINE)
    if h1_match:
        node = h1_match.group(1).strip()
    else:
        # 降级：从文件名提取，如 04_买入建仓_template.md -> 买入建仓
        basename = os.path.basename(md_path)
        node = re.sub(r"^\d+_(.+)_template\.md$", r"\1", basename)

    # 按 ## 问题N｜频次 分块
    blocks = re.split(r"\n## ", content)
    for block in blocks[1:]:
        # 第一行：问题N｜频次
        first_line = block.split("\n")[0].strip()
        freq_match = re.search(r"[｜|](.+)$", first_line)
        frequency = freq_match.group(1).strip() if freq_match else "未知"

        # 问题文本：**"..."**
        q_match = re.search(r'\*\*[「""](.+?)[」""]\*\*', block)
        if not q_match:
            # 兼容无引号格式 **问题文本**
            q_match = re.search(r'\*\*(.+?)\*\*', block)
        if not q_match:
            continue
        question = q_match.group(1).strip()

        # 提示词：``` ... ``` 代码块内容
        code_match = re.search(r"```\n([\s\S]+?)\n```", block)
        if not code_match:
            continue
        prompt_text = code_match.group(1).strip()

        # 去掉末尾免责声明行
        prompt_text = re.sub(r"\n本回答由 AI 生成.*$", "", prompt_text).strip()

        if prompt_text:
            prompts.append({
                "node": node,
                "frequency": frequency,
                "question": question,
                "prompt": prompt_text,
            })

    print(f"  {os.path.basename(md_path)} → 节点「{node}」{sum(1 for p in prompts if p['node'] == node)} 条")

print(f"解析到 {len(prompts)} 条提示词")
if not prompts:
    print("警告：未解析到任何数据，请检查 md 文件格式")
    exit(1)

# 4. 生成 HTML
data_json = json.dumps(prompts, ensure_ascii=False, indent=2)
experts_json = json.dumps(EXPERTS, ensure_ascii=False, indent=2)
gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股散户AI决策副驾 · 提示词库</title>
    <style>
        * {{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,-apple-system,sans-serif;}}
        body {{background:#f5f7fa;padding:20px;max-width:1100px;margin:0 auto;color:#333;}}
        .header {{text-align:center;margin-bottom:24px;}}
        .title {{font-size:22px;font-weight:700;margin-bottom:6px;}}
        .subtitle {{font-size:13px;color:#888;}}
        .search-input {{width:100%;padding:12px 16px;border:1px solid #ddd;border-radius:8px;font-size:15px;margin-bottom:14px;outline:none;}}
        .search-input:focus {{border-color:#2563eb;}}
        .filter-wrap {{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px;}}
        .filter-btn {{padding:6px 14px;border-radius:20px;border:1px solid #2563eb;color:#2563eb;cursor:pointer;background:#fff;font-size:13px;transition:all .15s;}}
        .filter-btn.active {{background:#2563eb;color:#fff;}}
        .stats {{font-size:13px;color:#888;margin-bottom:12px;}}
        .card-list {{display:grid;gap:12px;}}
        .card {{background:#fff;padding:18px;border-radius:10px;border:1px solid #eee;transition:box-shadow .15s;}}
        .card:hover {{box-shadow:0 2px 12px rgba(0,0,0,.08);}}
        .card-meta {{display:flex;align-items:center;gap:8px;margin-bottom:10px;}}
        .node-tag {{font-size:12px;color:#555;background:#f0f0f0;padding:2px 8px;border-radius:4px;}}
        .freq-badge {{font-size:11px;padding:2px 8px;border-radius:10px;font-weight:500;}}
        .freq-高频 {{background:#fee2e2;color:#b91c1c;}}
        .freq-中频 {{background:#fef3c7;color:#b45309;}}
        .freq-低频 {{background:#f0f0f0;color:#555;}}
        .question {{font-size:15px;line-height:1.6;margin-bottom:12px;}}
        .btn-group {{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;}}
        .btn {{padding:5px 14px;font-size:13px;border-radius:5px;border:none;cursor:pointer;transition:opacity .15s;}}
        .btn:hover {{opacity:.85;}}
        .btn-expand {{background:#eef2ff;color:#2563eb;}}
        .btn-copy {{background:#2563eb;color:#fff;}}
        .btn-yuanbao {{background:#1a56db;color:#fff;}}
        .prompt-box {{background:#f8fafc;padding:16px;border-radius:6px;white-space:pre-wrap;font-size:13px;line-height:1.9;display:none;border-left:3px solid #2563eb;margin-top:4px;}}
        .prompt-box.show {{display:block;}}
        .empty {{text-align:center;padding:60px;color:#aaa;font-size:15px;}}
        .footer {{margin-top:40px;text-align:center;font-size:12px;color:#bbb;padding-bottom:20px;}}
        .stock-bar {{display:flex;gap:10px;align-items:center;background:#fff;border:1px solid #e0e7ff;border-radius:10px;padding:12px 16px;margin-bottom:14px;flex-wrap:wrap;}}
        .stock-bar label {{font-size:13px;color:#555;white-space:nowrap;}}
        .stock-input {{flex:1;min-width:80px;padding:6px 10px;border:1px solid #ddd;border-radius:6px;font-size:14px;outline:none;}}
        .stock-input:focus {{border-color:#2563eb;}}
        .stock-hint {{font-size:12px;color:#aaa;margin-left:auto;white-space:nowrap;}}
        .placeholder-tag {{display:inline-block;background:#e0e7ff;color:#3730a3;border-radius:3px;padding:0 3px;font-family:monospace;font-size:12px;}}
        .expert-bar {{display:flex;gap:10px;align-items:center;background:#fff;border:1px solid #fde68a;border-radius:10px;padding:12px 16px;margin-bottom:14px;flex-wrap:wrap;}}
        .expert-bar label {{font-size:13px;color:#555;white-space:nowrap;font-weight:500;}}
        .expert-select {{padding:6px 10px;border:1px solid #ddd;border-radius:6px;font-size:14px;outline:none;min-width:200px;background:#fff;}}
        .expert-select:focus {{border-color:#d97706;}}
        .expert-hint {{font-size:12px;color:#b45309;margin-left:auto;white-space:nowrap;}}
        .expert-preview {{flex-basis:100%;font-size:12px;color:#666;line-height:1.7;margin-top:6px;padding:10px 12px;background:#fffbeb;border-radius:6px;display:none;}}
        .expert-preview.show {{display:block;}}
        .subst-stock {{background:#dcfce7;color:#15803d;padding:0 3px;border-radius:3px;font-weight:500;}}
        .subst-expert {{background:#fef3c7;color:#b45309;padding:0 3px;border-radius:3px;}}
        .subst-pending {{background:#f1f5f9;color:#64748b;padding:0 3px;border-radius:3px;font-family:monospace;font-size:12px;}}
        @media(max-width:600px){{
            body{{padding:12px;}}
            .filter-btn{{padding:5px 10px;font-size:12px;}}
            .btn{{padding:5px 10px;font-size:12px;}}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="title">A股散户AI决策副驾 · 提示词库</div>
        <div class="subtitle">真实散户问题 × 专家级AI提示词 · 覆盖交易全周期</div>
    </div>

    <input class="search-input" id="searchInput" placeholder="🔍 搜索问题或关键词...">
    <div class="expert-bar">
        <label>专家视角</label>
        <select class="expert-select" id="expertSelect"></select>
        <span class="expert-hint">切换后，复制的提示词自动带上这位投资人的思考立场</span>
        <div class="expert-preview" id="expertPreview"></div>
    </div>
    <div class="stock-bar">
        <label>分析标的</label>
        <input class="stock-input" id="stockName" placeholder="股票名称，如 贵州茅台" style="max-width:180px;">
        <input class="stock-input" id="stockCode" placeholder="股票代码，如 600519" style="max-width:130px;">
        <span class="stock-hint">填入后复制的提示词自动替换 <span class="placeholder-tag">{{{{股票名称}}}}</span> <span class="placeholder-tag">{{{{股票代码}}}}</span></span>
    </div>
    <div class="filter-wrap" id="filterWrap"></div>
    <div class="stats" id="stats"></div>
    <div class="card-list" id="cardList"></div>

    <div class="footer">⚠️ 本工具仅为决策辅助，不构成任何投资建议 · 生成时间：{gen_time}</div>

<script>
const promptData = {data_json};
const expertList = {experts_json};

// 初始化专家下拉
const expertSelect = document.getElementById('expertSelect');
expertList.forEach((e, i) => {{
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = e.label;
    expertSelect.appendChild(opt);
}});
const expertPreview = document.getElementById('expertPreview');
function renderExpertPreview() {{
    const e = expertList[expertSelect.value];
    if (e && e.body) {{
        expertPreview.textContent = e.body;
        expertPreview.classList.add('show');
    }} else {{
        expertPreview.classList.remove('show');
    }}
}}
expertSelect.addEventListener('change', renderExpertPreview);
renderExpertPreview();

// 统计节点
const nodeCount = {{}};
promptData.forEach(d => {{ nodeCount[d.node] = (nodeCount[d.node] || 0) + 1; }});

// 渲染筛选按钮
const filterWrap = document.getElementById('filterWrap');
function buildFilters() {{
    filterWrap.innerHTML = `<button class="filter-btn active" data-node="all">全部(${{promptData.length}})</button>`;
    Object.entries(nodeCount).forEach(([node, cnt]) => {{
        filterWrap.innerHTML += `<button class="filter-btn" data-node="${{node}}">${{node}}(${{cnt}})</button>`;
    }});
}}
buildFilters();

// 渲染卡片
function renderCards(data) {{
    const container = document.getElementById('cardList');
    const stats = document.getElementById('stats');
    stats.textContent = `显示 ${{data.length}} 条`;
    if (!data.length) {{
        container.innerHTML = '<div class="empty">没有找到匹配的提示词</div>';
        return;
    }}
    container.innerHTML = '';
    data.forEach((item, i) => {{
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <div class="card-meta">
                <span class="node-tag">${{item.node}}</span>
                <span class="freq-badge freq-${{item.frequency}}">${{item.frequency}}</span>
            </div>
            <div class="question">💬 ${{item.question}}</div>
            <div class="btn-group">
                <button class="btn btn-expand" data-i="${{i}}">展开提示词</button>
                <button class="btn btn-copy" data-i="${{i}}">复制</button>
                <button class="btn btn-yuanbao" data-i="${{i}}">去 DeepSeek 用 →</button>
            </div>
            <div class="prompt-box" id="pb-${{i}}">${{renderPromptHTML(item.prompt)}}</div>
        `;
        container.appendChild(card);
    }});
    // 保存当前渲染的数据引用，供点击事件使用
    container._data = data;
}}

// 把提示词渲染成带高亮的 HTML：股票名/代码/专家视角的替换处加高亮
function renderPromptHTML(text) {{
    const name = document.getElementById('stockName').value.trim();
    const code = document.getElementById('stockCode').value.trim();
    const expertBody = expertList[expertSelect.value]?.body || '';
    const expertLabel = expertList[expertSelect.value]?.label || '';

    // 先转义 HTML 再做替换
    let html = escapeHtml(text);

    if (name) {{
        html = html.split('{{股票名称}}').join(`<span class="subst-stock">${{escapeHtml(name)}}</span>`);
    }} else {{
        html = html.split('{{股票名称}}').join(`<span class="subst-pending">{{股票名称}}</span>`);
    }}
    if (code) {{
        html = html.split('{{股票代码}}').join(`<span class="subst-stock">${{escapeHtml(code)}}</span>`);
    }} else {{
        html = html.split('{{股票代码}}').join(`<span class="subst-pending">{{股票代码}}</span>`);
    }}
    if (expertBody) {{
        const tag = `<span class="subst-expert" title="来自：${{escapeHtml(expertLabel)}}">${{escapeHtml(expertBody)}}</span>`;
        html = html.split('{{专家视角}}').join(tag);
    }} else {{
        html = html.split('{{专家视角}}').join(`<span class="subst-pending">{{专家视角}}（当前：未指定）</span>`);
    }}
    return html;
}}

function escapeHtml(s) {{
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}}

// 当输入/下拉变化时，只更新已渲染卡片的预览框内容（保留展开/滚动状态）
function refreshPromptBoxes() {{
    const container = document.getElementById('cardList');
    const data = container._data || [];
    data.forEach((item, i) => {{
        const box = document.getElementById('pb-' + i);
        if (box) box.innerHTML = renderPromptHTML(item.prompt);
    }});
}}

document.getElementById('stockName').addEventListener('input', refreshPromptBoxes);
document.getElementById('stockCode').addEventListener('input', refreshPromptBoxes);
expertSelect.addEventListener('change', refreshPromptBoxes);

renderCards(promptData);

// 筛选
filterWrap.addEventListener('click', e => {{
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const node = btn.dataset.node;
    applyFilters(node, document.getElementById('searchInput').value.trim());
}});

// 搜索
document.getElementById('searchInput').addEventListener('input', e => {{
    const activeNode = document.querySelector('.filter-btn.active')?.dataset.node || 'all';
    applyFilters(activeNode, e.target.value.trim());
}});

function applyFilters(node, keyword) {{
    let data = node === 'all' ? promptData : promptData.filter(d => d.node === node);
    if (keyword) {{
        const kw = keyword.toLowerCase();
        data = data.filter(d => d.question.toLowerCase().includes(kw) || d.prompt.toLowerCase().includes(kw));
    }}
    renderCards(data);
}}

// clipboard 兼容方案：优先用现代 API，降级用 execCommand
function copyText(text) {{
    if (navigator.clipboard && navigator.clipboard.writeText) {{
        return navigator.clipboard.writeText(text).then(() => true).catch(() => fallbackCopy(text));
    }}
    return Promise.resolve(fallbackCopy(text));
}}
function fallbackCopy(text) {{
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(ta);
    return ok;
}}

// 用用户输入替换提示词中的占位符
function applyStock(text) {{
    const name = document.getElementById('stockName').value.trim();
    const code = document.getElementById('stockCode').value.trim();
    if (name) text = text.split('{{股票名称}}').join(name);
    if (code) text = text.split('{{股票代码}}').join(code);
    const expertBody = expertList[expertSelect.value]?.body || '';
    text = text.split('{{专家视角}}').join(expertBody);
    return text;
}}

// 展开 / 复制 / 跳转
document.addEventListener('click', e => {{
    const btn = e.target.closest('.btn');
    if (!btn) return;
    const i = btn.dataset.i;
    const container = document.getElementById('cardList');
    const item = container._data?.[i];
    if (!item) return;

    if (btn.classList.contains('btn-expand')) {{
        const box = document.getElementById('pb-' + i);
        box.classList.toggle('show');
        btn.textContent = box.classList.contains('show') ? '收起提示词' : '展开提示词';
    }}
    if (btn.classList.contains('btn-copy')) {{
        copyText(applyStock(item.prompt)).then(ok => {{
            btn.textContent = ok ? '✅ 已复制' : '⚠️ 请手动复制';
            setTimeout(() => btn.textContent = '复制', 2000);
        }});
    }}
    if (btn.classList.contains('btn-yuanbao')) {{
        copyText(applyStock(item.prompt)).then(() => {{
            window.open('https://chat.deepseek.com/', '_blank');
        }});
    }}
}});
</script>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ 生成完成：index.html（{len(prompts)} 条提示词）")
print(f"启动服务：python -m http.server 8000")
print(f"访问地址：http://localhost:8000")
