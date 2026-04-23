"""
散户交易节点提示词批量生成器
工作流：
1. 读取 question.csv 中的所有问题
2. 对每个问题，调用 deepseek 生成专家级提示词
3. 每条成功后立即追加写入 md（中途中断不丢数据）

速率控制（防封IP）：
- 每个提示词间隔：10-15 秒
- 每 10 个提示词为 1 批，批次间暂停 5-10 分钟
- 83 条全量预计耗时：约 1.5-2 小时

运行：
  conda activate agent
  python sanhu_expt_prompt.py --stock 茅台
  python sanhu_expt_prompt.py --stock 茅台 --limit 5
  python sanhu_expt_prompt.py --stock 茅台 --think
  python sanhu_expt_prompt.py --stock 茅台 --model expert --think
"""

import warnings
warnings.filterwarnings('ignore')

import os
import re
import csv
import time
import random
import argparse
import subprocess
from datetime import datetime

# ==================== 速率控制参数 ====================

MIN_DELAY      = 10    # 每条间隔最小秒数
MAX_DELAY      = 15    # 每条间隔最大秒数
BATCH_SIZE     = 10    # 每批条数
BATCH_PAUSE_MIN = 300  # 批次间暂停最小秒（5分钟）
BATCH_PAUSE_MAX = 600  # 批次间暂停最大秒（10分钟）
MAX_RETRY      = 3     # 单条最大重试次数
TIMEOUT        = 300   # opencli 超时秒数（5分钟，给 deepseek 足够时间）
RETRY_WAIT_MIN = 30    # 重试前等待最小秒
RETRY_WAIT_MAX = 60    # 重试前等待最大秒


def rate_sleep(label: str = ""):
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    print(f"  [间隔] {label} 等待 {delay:.1f}s ...")
    time.sleep(delay)


def batch_pause(batch_num: int, total_batches: int):
    if batch_num >= total_batches:
        return
    pause = random.uniform(BATCH_PAUSE_MIN, BATCH_PAUSE_MAX)
    resume_at = datetime.fromtimestamp(time.time() + pause).strftime("%H:%M:%S")
    print(f"\n{'='*60}")
    print(f"⏸  第 {batch_num}/{total_batches} 批完成，暂停 {pause/60:.1f} 分钟（预计 {resume_at} 恢复）")
    print(f"{'='*60}\n")
    time.sleep(pause)


# ==================== opencli 调用 ====================

def opencli_ask(provider: str, prompt: str,
                enable_think: bool = False, model: str = "instant") -> str:
    for attempt in range(1, MAX_RETRY + 1):
        try:
            cmd = [
                "opencli", provider, "ask",
                "--timeout", str(TIMEOUT),
                "--format", "plain",
            ]
            if provider == "deepseek":
                cmd.extend(["--model", model])
                if enable_think:
                    cmd.extend(["--think", "true"])
            cmd.append(prompt)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT + 60,  # subprocess 比 opencli 多 60s 余量
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()

            err = result.stderr.strip() or result.stdout.strip() or "(无输出)"
            print(f"  [警告] 第{attempt}次失败: {err[:150]}")

        except subprocess.TimeoutExpired:
            print(f"  [警告] 第{attempt}次 subprocess 超时({TIMEOUT+60}s)")
        except FileNotFoundError:
            raise RuntimeError("未找到 opencli，请确认已安装并在 PATH 中")

        if attempt < MAX_RETRY:
            wait = random.uniform(RETRY_WAIT_MIN, RETRY_WAIT_MAX)
            print(f"  [重试] {wait:.0f}s 后第 {attempt+1} 次重试...")
            time.sleep(wait)

    raise RuntimeError(f"opencli {provider} 连续 {MAX_RETRY} 次失败，跳过本条")


def extract_assistant_response(text: str) -> str:
    marker = "Role: Assistant"
    idx = text.find(marker)
    if idx == -1:
        return text.strip()
    after = text[idx + len(marker):]
    after = re.sub(r"^\s*Text:\s*", "", after, count=1)
    return after.strip()


# ==================== 提示词生成 ====================

def generate_expert_prompt(stock_name: str, question: str,
                           enable_think: bool = False,
                           model: str = "instant") -> str:
    meta_prompt = (
        f"你是一名资深提示词工程师且具备A股投研最佳实践。"
        f"将问题「关于{stock_name}：{question}」转换为专家级AI提示词。"
        f"强制约束：只输出提示词正文，禁止任何解释、说明、备注。"
    )
    raw = opencli_ask("deepseek", meta_prompt,
                      enable_think=enable_think, model=model)
    return extract_assistant_response(raw).strip()


# ==================== CSV 读取 ====================

def load_questions(csv_path: str) -> list[dict]:
    questions = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append({
                "node":      row["节点名称"].strip(),
                "frequency": row["频次分层"].strip(),
                "question":  row["问题内容"].strip(),
            })
    return questions


# ==================== 即时写入（每条成功后追加）====================

def init_output_file(output_file: str, total: int):
    """创建 md 文件并写入头部"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 散户交易节点专家提示词库\n\n")
        f.write(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"> 共 {total} 条问题（实时追加，中断不丢数据）\n\n")
        f.write("---\n\n")


def append_result(output_file: str, item: dict):
    """每条完成后立即追加写入"""
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"## {item['node']}\n\n")
        f.write(f"### [{item['frequency']}] {item['question']}\n\n")
        if item.get("prompt"):
            f.write(item["prompt"] + "\n\n")
        else:
            f.write(f"> ⚠️ 生成失败：{item.get('error', '未知')}\n\n")
        f.write("---\n\n")


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description="散户交易节点提示词批量生成器")
    parser.add_argument("--stock",      default="茅台",     help="股票名称")
    parser.add_argument("--limit",      type=int, default=0, help="只处理前N条（0=全部）")
    parser.add_argument("--model",      default="instant",  choices=["instant", "expert"])
    parser.add_argument("--think",      action="store_true", help="开启 DeepThink 思考模式")
    parser.add_argument("--output-dir",
                        default="/Users/max/Documents/08_algo_copilot/01_ai_wechat/topic_02_baisc/promo_test_auto",
                        help="输出目录")
    args = parser.parse_args()

    csv_path = "/Users/max/Documents/08_algo_copilot/01_ai_wechat/topic_02_baisc/promo_test_auto/question.csv"
    questions = load_questions(csv_path)
    if args.limit > 0:
        questions = questions[:args.limit]

    total         = len(questions)
    total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
    timestamp     = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file   = os.path.join(args.output_dir, f"sanhu_prompts_{timestamp}.md")

    os.makedirs(args.output_dir, exist_ok=True)
    init_output_file(output_file, total)

    print(f"\n{'='*60}")
    print(f"股票：{args.stock}  |  共 {total} 条  |  分 {total_batches} 批")
    print(f"模型：{args.model}  |  思考模式：{'开启' if args.think else '关闭'}")
    print(f"超时：{TIMEOUT}s/条  |  间隔：{MIN_DELAY}-{MAX_DELAY}s")
    print(f"输出：{output_file}")
    print(f"{'='*60}\n")

    success = 0
    for i, q in enumerate(questions, 1):
        batch_num    = (i - 1) // BATCH_SIZE + 1
        in_batch_pos = (i - 1) % BATCH_SIZE + 1
        batch_size_actual = min(BATCH_SIZE, total - (batch_num - 1) * BATCH_SIZE)

        print(f"[{i}/{total}] 批次{batch_num}/{total_batches} 第{in_batch_pos}/{batch_size_actual}条 "
              f"| {q['node']} {q['frequency']} | {q['question'][:28]}...")

        item = {**q}
        try:
            prompt = generate_expert_prompt(
                args.stock, q["question"],
                enable_think=args.think, model=args.model,
            )
            item["prompt"] = prompt
            success += 1
            print(f"  [OK] {len(prompt)} 字 → 已写入")
        except Exception as e:
            item["prompt"] = None
            item["error"]  = str(e)
            print(f"  [跳过] {e}")

        # 每条完成立即写入
        append_result(output_file, item)

        if i < total:
            # 批次间暂停（先暂停再间隔，避免重复等待）
            if i % BATCH_SIZE == 0:
                batch_pause(batch_num, total_batches)
            else:
                rate_sleep(f"下一条 {i+1}/{total}")

    print(f"\n{'='*60}")
    print(f"完成！成功 {success}/{total} 条")
    print(f"结果：{output_file}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
