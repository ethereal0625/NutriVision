# -*- coding: utf-8 -*-
"""cross_model_experiment.py - 跨模型对比实验（V5 Prompt）
对同一批 20 张食物图，分别用 qwen-vl-plus / qwen-vl-max / glm-4v / doubao-seed-2.0
做 V5 成分级分析，评估各模型在 JSON 合规、字段完整性、食材数、视觉描述长度等指标上的表现。
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modules.vision_analyzer import analyze_image
from prompt_experiment import EXPERIMENT_IMAGES, IMAGE_DIR, evaluate_result

BASE = Path(__file__).resolve().parent
MODELS = ["qwen-vl-plus", "qwen-vl-max", "glm-4v", "doubao-seed-2.0"]
MODEL_LABELS = {
    "qwen-vl-plus": "通义千问 Qwen-VL-Plus",
    "qwen-vl-max": "通义千问 Qwen-VL-Max",
    "glm-4v": "智谱 GLM-4V",
    "doubao-seed-2.0": "豆包 Seed",
}

def run_model(model: str, images: list, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "results.jsonl"
    records = []
    scores_all = []
    print(f"\n{'='*64}\n  模型: {MODEL_LABELS.get(model, model)}\n{'='*64}")
    for i, img_name in enumerate(images, 1):
        img_path = str(IMAGE_DIR / f"ff_{Path(img_name).stem}_000.jpg")
        print(f"  [{i}/{len(images)}] {img_name} ... ", end="", flush=True)
        try:
            result = analyze_image(img_path, model=model)
            record = {"image": img_name, "model": model, "result": result}
            score = evaluate_result(result)
            status = "OK" if score["json_valid"] else "PARSE"
            print(f"{status} (ing={score['ingredient_count']}, vd={score['vd_length']})")
        except Exception as e:
            record = {"image": img_name, "model": model, "error": str(e)[:300]}
            score = None
            print(f"ERR {str(e)[:80]}")
        records.append(record)
        if score:
            scores_all.append(score)
        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        time.sleep(0.5)
    # 汇总
    n = len(scores_all)
    summary = {"model": model, "label": MODEL_LABELS.get(model, model), "total": len(images), "valid": n}
    if n:
        avg = {}
        keys = ["json_valid", "fields_present", "dish_name_bilingual", "ingredient_count",
                "ingredient_sufficient", "cooking_method_english", "tags_valid", "vd_length", "vd_sufficient"]
        for k in keys:
            avg[k] = sum(s[k] for s in scores_all) / n
        summary["avg_scores"] = avg
        summary["json_valid_rate"] = avg["json_valid"]
        summary["avg_fields_present"] = avg["fields_present"]
        summary["avg_ingredient_count"] = avg["ingredient_count"]
        summary["avg_vd_length"] = avg["vd_length"]
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20, help="用几张图（默认 20）")
    ap.add_argument("--model", default=None, help="只跑某个模型")
    args = ap.parse_args()

    images = EXPERIMENT_IMAGES[:args.limit]
    models = [args.model] if args.model else MODELS

    out_root = BASE / "pe_results" / "cross_model"
    out_root.mkdir(parents=True, exist_ok=True)

    summaries = []
    for m in models:
        s = run_model(m, images, out_root / m)
        summaries.append(s)
        print(f"  ✅ {MODEL_LABELS.get(m, m)} 完成: valid={s.get('json_valid_rate', 0):.0%}")

    # 对比表
    print(f"\n{'='*100}")
    print("  跨模型对比总结（V5 Prompt）")
    print(f"{'='*100}")
    hdr = f"{'模型':<22} {'JSON合规':<10} {'字段完整':<10} {'双语菜名':<10} {'食材数':<8} {'VD长度':<10} {'标签合规':<10}"
    print(hdr); print("-" * 100)
    for s in summaries:
        if "avg_scores" not in s:
            continue
        a = s["avg_scores"]
        print(f"{s['label']:<22} {a['json_valid']:<10.0%} {a['fields_present']:<10.0%} "
              f"{a['dish_name_bilingual']:<10.0%} {a['ingredient_count']:<8.1f} "
              f"{a['vd_length']:<10.0f} {a['tags_valid']:<10.2f}")
    (out_root / "comparison.json").write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n结果已保存到 {out_root}")

if __name__ == "__main__":
    main()
