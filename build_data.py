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

# 1. 找所有模板文件，按文件名排序保证节点顺序
md_files = sorted(glob.glob(os.path.join(template_dir, "*_template.md")))
if not md_files:
    print(f"错误：未找到模板文件，请检查目录 {template_dir}")
    exit(1)
print(f"找到 {len(md_files)} 个模板文件")

# 2. 解析每个模板文件
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

# 3. 生成 HTML
data_json = json.dumps(prompts, ensure_ascii=False, indent=2)
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
    <div class="filter-wrap" id="filterWrap"></div>
    <div class="stats" id="stats"></div>
    <div class="card-list" id="cardList"></div>

    <div class="footer">⚠️ 本工具仅为决策辅助，不构成任何投资建议 · 生成时间：{gen_time}</div>

<script>
const promptData = {data_json};

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
            <div class="prompt-box" id="pb-${{i}}">${{item.prompt}}</div>
        `;
        container.appendChild(card);
    }});
    // 保存当前渲染的数据引用，供点击事件使用
    container._data = data;
}}

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
        copyText(item.prompt).then(ok => {{
            btn.textContent = ok ? '✅ 已复制' : '⚠️ 请手动复制';
            setTimeout(() => btn.textContent = '复制', 2000);
        }});
    }}
    if (btn.classList.contains('btn-yuanbao')) {{
        copyText(item.prompt).then(() => {{
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
