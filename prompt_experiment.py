"""
prompt_experiment.py — Prompt Engineering 对比实验

4 版 prompt 策略在 20 张食物图片上做对比：
  V1: Baseline（基础零样本）
  V2: Role + Constraints（角色 + 输出约束）
  V3: Few-shot + Role（少样本示例 + 角色）
  V4: Chain of Thought + Role（思维链 + 角色）

输出: pe_results/V{1-4}/ 分别保存每版的 JSONL 结果 + 评估摘要
"""

import argparse
import json
import os
import re
import time
from pathlib import Path

import dashscope
from dashscope import MultiModalConversation

BASE = Path(__file__).resolve().parent

# ─── 4 版 Prompt ─────────────────────────────────────────────────

PROMPT_V1 = (
    "分析这张食物图片，输出 JSON：\n"
    "{\n"
    '  "dish_name": "菜名",\n'
    '  "ingredients": ["食材1", "食材2"],\n'
    '  "cooking_method": "烹饪方式",\n'
    '  "health_risk_tags": ["high oil", "high sugar"],\n'
    '  "visual_description": "英文视觉描述"\n'
    "}"
)

PROMPT_V2 = (
    "你是一位专业的营养师兼美食摄影师。请仔细观察这张食物图片，"
    "严格按照以下 JSON 格式输出分析结果，**不要输出任何其他文字、解释或 markdown 标记**：\n\n"
    "{\n"
    '  "dish_name": "菜名，同时给出中文和英文，如 \\"宫保鸡丁 Kung Pao Chicken\\"",\n'
    '  "ingredients": ["主要食材1", "主要食材2", "主要食材3"],\n'
    '  "cooking_method": "烹饪方式的英文描述，如 deep-fried, steamed, stir-fried, braised, roasted",\n'
    '  "health_risk_tags": ["high oil", "high sugar", "high sodium", "high calorie", "processed meat", "low fiber"],\n'
    '  "visual_description": "A detailed English description of the dish for image generation purposes. '\
    'Describe the appearance, colors, texture, plating style, garnishes, lighting, and overall composition. '\
    'This will be used as a prompt for Stable Diffusion to recreate a similar-looking dish."\n'
    "}\n\n"
    "注意事项：\n"
    "1. ingredients 列出你能识别到的所有主要食材（3-8 个），用中文。\n"
    "2. health_risk_tags 从以下候选中选择适用的标签："\
    '"high oil", "high sugar", "high sodium", "high calorie", "processed meat", '\
    '"low fiber", "high carb", "contains allergens"。如果菜品整体健康，可以为空列表 []。\n'
    "3. visual_description 必须用英文撰写，要详细描述菜品外观、颜色、质感、摆盘方式、"\
    "配菜装饰、光线和整体构图，以便后续用于文生图模型重建类似的菜品图片。\n"
    "4. 只输出 JSON，不要输出 ```json 代码块标记，不要输出任何额外文字。"
)

PROMPT_V3 = (
    "你是一位专业的营养师兼美食摄影师。请仔细观察这张食物图片，"
    "严格按照以下 JSON 格式输出分析结果，**不要输出任何其他文字**：\n\n"
    "{\n"
    '  "dish_name": "菜名（中英文）",\n'
    '  "ingredients": ["食材1", "食材2", "食材3"],\n'
    '  "cooking_method": "烹饪方式英文",\n'
    '  "health_risk_tags": ["标签1", "标签2"],\n'
    '  "visual_description": "英文视觉描述"\n'
    "}\n\n"
    "--- 示例 ---\n\n"
    "输入图片：一盘红烧肉\n"
    "输出：\n"
    "{\n"
    '  "dish_name": "红烧肉 Braised Pork Belly",\n'
    '  "ingredients": ["五花肉", "酱油", "冰糖", "料酒", "生姜", "八角"],\n'
    '  "cooking_method": "braised",\n'
    '  "health_risk_tags": ["high oil", "high sugar", "high sodium", "high calorie", "processed meat"],\n'
    '  "visual_description": "A close-up overhead shot of glossy, amber-brown braised pork belly chunks '\
    'arranged in a white ceramic bowl. The meat glistens with a rich, dark soy-based sauce, '\
    'with visible layers of fat and lean meat. The dish is garnished with a few green scallion rings. '\
    'Warm, natural lighting highlights the caramelized glaze."\n'
    "}\n\n"
    "注意事项：\n"
    "1. ingredients 列出 3-8 个主要食材，用中文。\n"
    "2. health_risk_tags 从以下候选中选择："\
    '"high oil", "high sugar", "high sodium", "high calorie", "processed meat", '\
    '"low fiber", "high carb", "contains allergens"。健康菜品可写 []。\n'
    "3. visual_description 必须用英文，详细描述外观、颜色、质感、摆盘、装饰、光线和构图，"\
    "用于 Stable Diffusion 重建类似菜品。\n"
    "4. 只输出 JSON，不要 markdown 标记。"
)

PROMPT_V4 = (
    "你是一位专业的营养师兼美食摄影师。请按以下步骤分析这张食物图片：\n\n"
    "**第一步：观察识别**\n"
    "仔细观察图片中的菜品，识别：这是什么菜？有哪些食材？用了什么烹饪方式？"\
    "摆盘和视觉特征是什么？\n\n"
    "**第二步：健康评估**\n"
    "从营养角度评估这道菜：它可能有哪些健康风险？"\
    "候选标签：high oil, high sugar, high sodium, high calorie, processed meat, low fiber, high carb, contains allergens\n\n"
    "**第三步：英文视觉描述**\n"
    "用英文撰写一段详细的视觉描述，涵盖：菜品外观、颜色、质感、摆盘方式、"\
    "配菜装饰、光线和整体构图。这段描述将用于 Stable Diffusion 重建类似菜品。\n\n"
    "**第四步：输出 JSON**\n"
    "将以上分析结果整合为严格的 JSON 格式输出，不要输出任何其他文字：\n"
    "{\n"
    '  "dish_name": "菜名（中英文）",\n'
    '  "ingredients": ["食材1", "食材2", "食材3"],\n'
    '  "cooking_method": "烹饪方式英文",\n'
    '  "health_risk_tags": ["标签1", "标签2"],\n'
    '  "visual_description": "英文视觉描述"\n'
    "}\n\n"
    "注意事项：\n"
    "1. ingredients 列出 3-8 个主要食材，用中文。\n"
    "2. 只输出最终 JSON，不要输出思考过程。"
)

PROMPT_V5 = (
    "你是一位专业的营养师兼美食摄影师。请仔细观察这张食物图片，"
    "估算每种食材的克重，严格按照以下 JSON 格式输出分析结果，**不要输出任何其他文字**：\n\n"
    "{\n"
    '  "dish_name": "菜名（中英文）",\n'
    '  "ingredients": [\n'
    '    {"name": "鸡胸肉", "weight_g": 150},\n'
    '    {"name": "食用油", "weight_g": 20}\n'
    "  ],\n"
    '  "cooking_method": "烹饪方式英文",\n'
    '  "health_risk_tags": ["标签1", "标签2"],\n'
    '  "model_calories": 整份估算热量（整数）,\n'
    '  "visual_description": "英文视觉描述"\n'
    "}\n\n"
    "注意事项：\n"
    "1. ingredients 逐项列出主要食材及估算克重 weight_g（整数，熟重），食用油/酱料也要单列；\n"
    "2. health_risk_tags 从以下候选中选择："
    '"high oil", "high sugar", "high sodium", "high calorie", "processed meat", '
    '"low fiber", "high carb", "contains allergens"。健康菜品可写 []。\n'
    "3. visual_description 必须用英文，详细描述外观、颜色、质感、摆盘、装饰、光线和构图。\n"
    "4. 只输出 JSON，不要 markdown 标记。"
)

PROMPTS = {
    "v1_baseline": PROMPT_V1,
    "v2_role_constraints": PROMPT_V2,
    "v3_few_shot": PROMPT_V3,
    "v4_chain_of_thought": PROMPT_V4,
    "v5_ingredient_weight": PROMPT_V5,
}

SYSTEM_PROMPT = "你是专业营养师和美食摄影师，只输出JSON。"

# ─── Experiment images ────────────────────────────────────────────
EXPERIMENT_IMAGES = [
    "1.jpg", "66.jpg", "263.jpg", "417.jpg", "646.jpg",
    "693.jpg", "729.jpg", "784.jpg", "996.jpg", "1186.jpg",
    "1269.jpg", "1353.jpg", "1440.jpg", "1602.jpg", "1781.jpg",
    "1947.jpg", "2090.jpg", "2169.jpg", "2279.jpg", "2351.jpg",
]
IMAGE_DIR = BASE / "food_merged"


# ─── Helpers ──────────────────────────────────────────────────────
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


def parse_json_response(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return {"_raw_output": text[:500], "_parse_error": True}


def call_vlm(image_path: str, prompt: str, model: str) -> dict:
    messages = [
        {"role": "system", "content": [{"text": SYSTEM_PROMPT}]},
        {
            "role": "user",
            "content": [
                {"image": f"file://{image_path}", "max_pixels": 518144},
                {"text": prompt},
            ],
        },
    ]
    last_err = None
    for attempt in range(3):
        try:
            resp = MultiModalConversation.call(model=model, messages=messages)
            if resp.status_code != 200:
                raise RuntimeError(f"status={resp.status_code} code={resp.code} msg={resp.message}")
            text = resp.output.choices[0].message.content[0]["text"]
            return parse_json_response(text)
        except Exception as e:
            last_err = e
            time.sleep(2 ** attempt)
    return {"_error": str(last_err)}


# ─── Evaluation ───────────────────────────────────────────────────
def evaluate_result(result: dict) -> dict:
    """评估单条标注的质量"""
    scores = {}

    # 1. JSON 解析是否成功
    scores["json_valid"] = not result.get("_parse_error") and not result.get("_error")

    # 2. 字段完整性
    required = ["dish_name", "ingredients", "cooking_method", "health_risk_tags", "visual_description"]
    scores["fields_present"] = sum(1 for f in required if f in result and result[f]) / len(required)

    # 3. dish_name 质量（中英文都有）
    dn = result.get("dish_name", "")
    has_cn = any("一" <= c <= "鿿" for c in dn)
    has_en = any(c.isascii() and c.isalpha() for c in dn)
    scores["dish_name_bilingual"] = float(has_cn and has_en)

    # 4. ingredients 数量
    ing = result.get("ingredients", [])
    scores["ingredient_count"] = len(ing)
    scores["ingredient_sufficient"] = 1.0 if 3 <= len(ing) <= 8 else 0.5 if len(ing) > 0 else 0.0

    # 5. cooking_method 是否为英文
    cm = result.get("cooking_method", "")
    scores["cooking_method_english"] = 1.0 if cm and all(c.isascii() or c.isspace() or c == "-" for c in cm) else 0.0

    # 6. health_risk_tags 是否从候选集中选择
    valid_tags = {"high oil", "high sugar", "high sodium", "high calorie", "processed meat", "low fiber", "high carb", "contains allergens"}
    tags = result.get("health_risk_tags", [])
    if tags:
        scores["tags_valid"] = sum(1 for t in tags if t in valid_tags) / len(tags)
    else:
        scores["tags_valid"] = 1.0  # 空列表也算合理

    # 7. visual_description 长度和质量
    vd = result.get("visual_description", "")
    scores["vd_length"] = len(vd)
    scores["vd_sufficient"] = 1.0 if len(vd) > 100 else 0.5 if len(vd) > 30 else 0.0

    return scores


def run_experiment(prompt_name: str, prompt: str, images: list, model: str, out_dir: Path):
    """运行单个 prompt 版本的实验"""
    print(f"\n{'='*60}")
    print(f"  开始实验: {prompt_name}")
    print(f"{'='*60}")

    jsonl_path = out_dir / f"{prompt_name}.jsonl"
    results = []
    all_scores = []

    for i, img_name in enumerate(images, 1):
        img_path = str(IMAGE_DIR / f"ff_{Path(img_name).stem}_000.jpg")
        print(f"  [{i}/{len(images)}] {img_name} ... ", end="", flush=True)

        result = call_vlm(img_path, prompt, model)
        record = {"image": img_name, **result}
        scores = evaluate_result(result)
        all_scores.append(scores)

        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        status = "OK" if scores["json_valid"] else "FAIL"
        print(f"{status} (fields={scores['fields_present']:.0%}, vd_len={scores['vd_length']})")

        results.append(record)

    # 汇总统计
    avg = {}
    for key in all_scores[0]:
        avg[key] = sum(s[key] for s in all_scores) / len(all_scores)

    summary = {
        "prompt_name": prompt_name,
        "total_images": len(images),
        "avg_scores": avg,
        "json_valid_rate": avg["json_valid"],
        "avg_fields_present": avg["fields_present"],
        "avg_ingredient_count": avg["ingredient_count"],
        "avg_vd_length": avg["vd_length"],
    }

    summary_path = out_dir / f"{prompt_name}_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n  ✅ {prompt_name} 完成: valid_rate={avg['json_valid']:.0%}, "
          f"fields={avg['fields_present']:.0%}, "
          f"avg_ingredients={avg['ingredient_count']:.1f}, "
          f"avg_vd_len={avg['vd_length']:.0f}")

    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen-vl-plus")
    ap.add_argument("--version", default="all", choices=["v1", "v2", "v3", "v4", "v5", "all"])
    args = ap.parse_args()

    dashscope.api_key = load_api_key()

    out_dir = BASE / "pe_results"
    out_dir.mkdir(exist_ok=True)

    ver_suffix = {
        "v1": "baseline", "v2": "role_constraints", "v3": "few_shot",
        "v4": "chain_of_thought", "v5": "ingredient_weight",
    }
    versions_to_run = []
    if args.version == "all":
        versions_to_run = list(PROMPTS.keys())
    else:
        versions_to_run = [f"{args.version}_{ver_suffix[args.version]}"]

    summaries = []
    for vname, prompt in PROMPTS.items():
        if vname not in versions_to_run:
            continue
        summary = run_experiment(vname, prompt, EXPERIMENT_IMAGES, args.model, out_dir)
        summaries.append(summary)

    # 总对比表
    print(f"\n{'='*60}")
    print("  对比总结")
    print(f"{'='*60}")
    print(f"{'Prompt':<25} {'JSON Valid':<12} {'Fields':<10} {'Ingredients':<14} {'VD Length':<12} {'Tags Valid':<12}")
    print("-" * 85)
    for s in summaries:
        a = s["avg_scores"]
        print(f"{s['prompt_name']:<25} {a['json_valid']:<12.0%} {a['fields_present']:<10.0%} "
              f"{a['ingredient_count']:<14.1f} {a['vd_length']:<12.0f} {a['tags_valid']:<12.2f}")

    comparison_path = out_dir / "comparison.json"
    with open(comparison_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)

    print(f"\n对比结果已保存到 {comparison_path}")


if __name__ == "__main__":
    main()
