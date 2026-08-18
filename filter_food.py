import argparse
import json
import os
import re
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import dashscope
from dashscope import MultiModalConversation

BASE = Path(__file__).resolve().parent

FILTER_PROMPT = (
    "你是一个食物图片筛选助手。判断图片的主体是否为食物、菜肴、食材或饮品。"
    "只输出 JSON {\"is_food\": true} 或 {\"is_food\": false}，不要输出任何其他文字。"
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
    raise SystemExit(
        "未检测到 DASHSCOPE_API_KEY。请设置环境变量，"
        "或在项目根目录 .env 文件中写入 DASHSCOPE_API_KEY=sk-xxx"
    )


def parse_bool(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"无法解析模型输出: {text[:100]}")
    return bool(json.loads(m.group(0))["is_food"])


def call_vlm(image: Path, model: str):
    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"file://{image.as_posix()}", "max_pixels": 262144},
                {"text": FILTER_PROMPT},
            ],
        }
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
            return parse_bool(text)
        except Exception as e:
            last_err = e
            time.sleep(2**attempt)
    raise last_err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-dir", default=str(BASE / "Train"))
    ap.add_argument("--model", default="qwen-vl-plus")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    dashscope.api_key = load_api_key()

    image_dir = Path(args.image_dir)
    out_dir = BASE / "output"
    out_dir.mkdir(exist_ok=True)
    jsonl = out_dir / "food_filter.jsonl"

    done = set()
    if jsonl.exists():
        with open(jsonl, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["image"])
                except Exception:
                    pass

    images = sorted(image_dir.glob("*.jpg"), key=lambda p: int(p.stem))
    images = [p for p in images if p.name not in done]
    if args.limit:
        images = images[: args.limit]
    print(f"待处理: {len(images)} 张 (已跳过 {len(done)} 张)")

    lock = threading.Lock()
    stats = {"food": 0, "non_food": 0, "fail": 0}

    def work(img: Path):
        is_food = call_vlm(img, args.model)
        with lock:
            with open(jsonl, "a", encoding="utf-8") as f:
                f.write(json.dumps({"image": img.name, "is_food": is_food}, ensure_ascii=False) + "\n")
            if is_food:
                stats["food"] += 1
            else:
                stats["non_food"] += 1

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, img): img for img in images}
        for i, fut in enumerate(as_completed(futs), 1):
            img = futs[fut]
            try:
                fut.result()
            except Exception as e:
                stats["fail"] += 1
                with lock:
                    with open(out_dir / "failed.txt", "a", encoding="utf-8") as f:
                        f.write(f"{img.name}\t{e}\n")
            if i % 100 == 0:
                print(f"进度 {i}/{len(images)} {stats}")

    print(f"完成 {stats}")

    food_dir = BASE / "food_filtered"
    food_dir.mkdir(exist_ok=True)
    search_dirs = [BASE / "Train", BASE / "Val"]
    n = 0
    with open(jsonl, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if not rec.get("is_food"):
                continue
            dst = food_dir / rec["image"]
            if dst.exists():
                n += 1
                continue
            for d in search_dirs:
                src = d / rec["image"]
                if src.exists():
                    shutil.copy2(src, dst)
                    n += 1
                    break
    print(f"食物图片共 {n} 张，已复制到 {food_dir}")


if __name__ == "__main__":
    main()
