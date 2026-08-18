import argparse
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import dashscope
from dashscope import MultiModalConversation

BASE = Path(__file__).resolve().parent

SYSTEM_PROMPT = (
    "你是一名资深营养师兼专业美食摄影师。"
    "请分析图片中的食物，只输出一个严格的 JSON 对象，不要输出任何其他文字。"
)

USER_PROMPT = (
    "请输出以下 JSON 格式：\n"
    "{\n"
    '  "dish_name": "菜名（中文）",\n'
    '  "ingredients": [\n'
    '    {"name": "鸡胸肉", "weight_g": 150},\n'
    '    {"name": "食用油", "weight_g": 20}\n'
    "  ],\n"
    '  "cooking_method": "烹饪方式（英文，如 deep fried / steamed / braised / stir-fried）",\n'
    '  "health_risk_tags": ["high oil","high sugar","high salt","high calorie","refined carb","processed meat"] 中选择，若健康则为 [] ,\n'
    '  "model_calories": 整份估算热量（整数，单位 kcal，供参考）,\n'
    '  "visual_description": "English visual description for text-to-image generation, including dish, plating, tableware, colors, lighting"\n'
    "}\n"
    "要求：\n"
    "1. ingredients 逐项列出主要食材及**估算克重** weight_g（整数，熟重），食用油/酱料也要单列；\n"
    "2. 克重代表该食材在整份菜品中的用量；\n"
    "3. 只输出 JSON，不要使用 markdown 代码块。"
)


def load_api_key():
    key = os.environ.get("DASHSCOPE_API_KEY")
    if key:
        return key
    env_file = BASE / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DASHSCOPE_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("未检测到 DASHSCOPE_API_KEY")


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"无法解析模型输出: {text[:100]}")
    return json.loads(m.group(0))


def call_vlm(image: Path, model: str):
    messages = [
        {"role": "system", "content": [{"text": SYSTEM_PROMPT}]},
        {
            "role": "user",
            "content": [
                {"image": f"file://{image.as_posix()}", "max_pixels": 1048576},
                {"text": USER_PROMPT},
            ],
        },
    ]
    last_err = None
    for attempt in range(4):
        try:
            resp = MultiModalConversation.call(model=model, messages=messages)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"status={resp.status_code} code={resp.code} msg={resp.message}"
                )
            text = resp.output.choices[0].message.content[0]["text"]
            return parse_json(text)
        except Exception as e:
            last_err = e
            time.sleep(2**attempt)
    raise last_err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-dir", default=str(BASE / "food_merged"))
    ap.add_argument("--model", default="qwen-vl-plus")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    dashscope.api_key = load_api_key()

    image_dir = Path(args.image_dir)
    out_dir = BASE / "output"
    out_dir.mkdir(exist_ok=True)
    jsonl = out_dir / "annotations_v5.jsonl"

    done = set()
    if jsonl.exists():
        with open(jsonl, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["image"])
                except Exception:
                    pass

    images = sorted(image_dir.glob("*.jpg"), key=lambda p: p.name)
    images = [p for p in images if p.name not in done]
    if args.limit:
        images = images[: args.limit]
    print(f"待标注: {len(images)} 张 (已跳过 {len(done)} 张)")

    lock = threading.Lock()
    stats = {"ok": 0, "fail": 0}

    def work(img: Path):
        data = call_vlm(img, args.model)
        rec = {"image": img.name, **data}
        with lock:
            with open(jsonl, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            stats["ok"] += 1

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, img): img for img in images}
        for i, fut in enumerate(as_completed(futs), 1):
            img = futs[fut]
            try:
                fut.result()
            except Exception as e:
                stats["fail"] += 1
                with lock:
                    with open(out_dir / "annotate_failed.txt", "a", encoding="utf-8") as f:
                        f.write(f"{img.name}\t{e}\n")
            if i % 50 == 0:
                print(f"进度 {i}/{len(images)} {stats}")

    print(f"完成 {stats}，结果在 {jsonl}")


if __name__ == "__main__":
    main()
