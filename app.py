import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from logging_config import setup_logging
setup_logging()


import streamlit as st

from modules.health_advisor import GOALS, generate_plan
from modules.image_generator import generate_image
from modules.nutrition_db import bmi, bmi_category, compute_calories, tdee
from modules.vision_analyzer import analyze_with_check

st.set_page_config(page_title="AI 健康饮食改造师", layout="wide", page_icon="🥗")

CSS = """
<style>
:root {
  --green: #2e8b57;
  --green-light: #e8f5ee;
  --accent: #ff8c42;
  --text: #1f2d3d;
}
/* 背景与字体 */
.stApp {
  background: linear-gradient(160deg, #f6fbf8 0%, #eef4f1 100%);
}
html, body, [class*="css"] {
  font-family: "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
  color: var(--text);
}
/* 标题区 */
.hero {
  background: linear-gradient(120deg, #2e8b57, #3ba56f 60%, #5cb98a);
  color: white;
  border-radius: 18px;
  padding: 28px 34px;
  margin-bottom: 22px;
  box-shadow: 0 8px 24px rgba(46,139,87,.25);
}
.hero h1 { margin: 0; font-size: 2rem; font-weight: 700; }
.hero p { margin: 6px 0 0; opacity: .92; font-size: .98rem; }
/* 卡片 */
.card {
  background: #ffffff;
  border-radius: 14px;
  padding: 20px 22px;
  box-shadow: 0 3px 12px rgba(31,45,61,.07);
  border: 1px solid #eef2f0;
  margin-bottom: 16px;
}
.card h3 {
  margin: 0 0 12px;
  font-size: 1.05rem;
  color: var(--green);
  border-left: 4px solid var(--green);
  padding-left: 10px;
}
/* 标签 chips */
.chip {
  display: inline-block;
  background: #fff1e8;
  color: #c4551d;
  border: 1px solid #ffd9c2;
  border-radius: 999px;
  padding: 2px 12px;
  margin: 3px 4px 3px 0;
  font-size: .82rem;
}
.chip.good {
  background: #e8f5ee;
  color: #2e8b57;
  border-color: #c7e8d8;
}
/* 按钮 */
.stButton>button, .stDownloadButton>button {
  border-radius: 10px;
  font-weight: 600;
  border: none;
  background: linear-gradient(120deg, #2e8b57, #3ba56f);
  color: white;
  padding: .5rem 1.2rem;
  box-shadow: 0 4px 12px rgba(46,139,87,.25);
  transition: transform .12s ease;
}
.stButton>button:hover {
  transform: translateY(-1px);
  color: white;
  background: linear-gradient(120deg, #267a4c, #34915f);
}
/* 侧边栏 */
[data-testid="stSidebar"] {
  background: #ffffff;
  border-right: 1px solid #edf1ef;
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  color: var(--green);
}
/* 指标 */
[data-testid="stMetric"] {
  background: white;
  border-radius: 12px;
  padding: 14px 16px;
  border: 1px solid #eef2f0;
  box-shadow: 0 2px 8px rgba(31,45,61,.05);
}
[data-testid="stMetricValue"] { color: var(--green); }
/* 进度条 */
.stProgress > div > div > div > div { background: linear-gradient(90deg, #2e8b57, #ff8c42); }
/* 上传区 */
[data-testid="stFileUploaderDropzone"] {
  border: 2px dashed var(--green);
  border-radius: 14px;
  background: #f4faf6;
}
/* spinner 颜色 */
[data-testid="stSpinner"] { color: var(--green); }
hr { border-color: #e5ece8; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
      <h1>🥗 AI 健康饮食改造师</h1>
      <p>上传食物照片 → VLM 视觉分析 → 个性化健康改造方案 → 文生图效果预览</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("🎯 健康目标")
    goal = st.radio("目标", GOALS, label_visibility="collapsed")

    st.header("👤 个人资料（选填）")
    use_profile = st.toggle("使用个人资料", value=False)
    if use_profile:
        height = st.number_input("身高 (cm)", 100.0, 250.0, 170.0)
        weight = st.number_input("体重 (kg)", 30.0, 300.0, 65.0)
        age = st.number_input("年龄", 10, 100, 22)
        gender = st.selectbox("性别", ["男", "女"])
        activity = st.selectbox("活动水平", ["久坐", "轻度", "中度", "高强度"])
    else:
        st.caption("不填写则仅给出食物建议")

uploaded = st.file_uploader("上传食物图片", type=["jpg", "jpeg", "png"])

if uploaded and st.button("开始分析", type="primary"):
    suffix = Path(uploaded.name).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        st.session_state["tmp_path"] = tmp.name

    with st.spinner("🔍 Module A：视觉分析中..."):
        result = analyze_with_check(st.session_state["tmp_path"])
        st.session_state["analyze_result"] = result
    st.session_state["plan"] = None
    st.session_state["plan_key"] = None
    st.session_state.pop("generated", None)

if "analyze_result" in st.session_state:
    result = st.session_state["analyze_result"]

    if not result.get("is_food"):
        st.error("⚠️ 未检测到食物：请上传包含食物、菜肴、食材或饮品的图片。")
        st.stop()

    analysis = result.get("analysis") or {}
    tmp_path = st.session_state["tmp_path"]

    computed_calories, breakdown, unlisted = compute_calories(analysis)

    if unlisted:
        st.warning(
            "ℹ️ 以下食材营养库未收录，已按 120 kcal/100g 估算："
            + "、".join(unlisted)
        )

    profile = None
    if use_profile:
        profile = {
            "height": height,
            "weight": weight,
            "age": age,
            "gender": gender,
            "activity": activity,
            "bmi": bmi(height, weight),
            "tdee": tdee(height, weight, age, gender, activity),
        }

    plan_key = (goal, bool(profile))
    if st.session_state.get("plan_key") != plan_key:
        with st.spinner("🧠 Module B：生成改造方案中..."):
            st.session_state["plan"] = generate_plan(
                analysis, goal, profile=profile, computed_calories=computed_calories
            )
            st.session_state["plan_key"] = plan_key
    plan = st.session_state["plan"]

    st.image(tmp_path, caption="原图", width=320)

    c_left, c_right = st.columns([3, 2])

    with c_left:
        st.markdown('<div class="card"><h3>🔬 原图分析</h3>', unsafe_allow_html=True)
        st.markdown(f"**菜名**：{analysis.get('dish_name', '-')}")
        st.markdown(f"**烹饪方式**：{analysis.get('cooking_method', '-')}")

        m1, m2, m3 = st.columns(3)
        m1.metric("模型估算", f"{analysis.get('model_calories', '-')} kcal", "Qwen-VL 直觉")
        m2.metric("营养库核算", f"{computed_calories} kcal", "成分表法")
        model_c = analysis.get("model_calories") or 0
        diff = computed_calories - model_c
        m3.metric("偏差", f"{diff:+d} kcal", "核算−模型")

        st.markdown("**风险标签**")
        tags = analysis.get("health_risk_tags", [])
        if tags:
            chips = "".join(f'<span class="chip">{t}</span>' for t in tags)
            st.markdown(chips, unsafe_allow_html=True)
        else:
            st.markdown('<span class="chip good">无明显风险</span>', unsafe_allow_html=True)

        if breakdown:
            st.markdown("**热量明细（成分表法）**")
            st.table([{
                "食材": b["name"], "克重(g)": b["weight_g"],
                "每100g(kcal)": b["kcal_per_100g"], "小计(kcal)": b["calories"],
            } for b in breakdown])
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown('<div class="card"><h3>🎨 视觉描述（英文）</h3>', unsafe_allow_html=True)
        st.write(analysis.get("visual_description", "-"))
        st.markdown("</div>", unsafe_allow_html=True)

        if profile:
            st.markdown('<div class="card"><h3>👤 用户健康档案</h3>', unsafe_allow_html=True)
            m1, m2 = st.columns(2)
            m1.metric("BMI", profile["bmi"], bmi_category(profile["bmi"]))
            m2.metric("每日建议摄入", f"{profile['tdee']} kcal")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>💡 「%s」改造方案 → %s</h3>'
                % (goal, plan.get("healthy_dish_name", "")) , unsafe_allow_html=True)
    st.markdown("**不健康点**")
    for p in plan.get("risk_points", []):
        st.markdown(f"- 🔴 {p}")
    st.markdown("**改造步骤**")
    for i, s in enumerate(plan.get("modification_plan", []), 1):
        st.markdown(f"{i}. ✅ {s}")
    effects = plan.get("expected_effects", "")
    if effects:
        st.markdown("**预期效果**")
        st.success(effects)
    st.markdown("**生图 Prompt（Module C 用）**")
    st.code(plan.get("image_prompt", ""), language="text")
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("🖼️ Module C：改造后效果图预览")
    if st.button("生成改造后效果图", type="secondary"):
        with st.spinner("🎨 通义万相文生图中（约 1-2 分钟）..."):
            try:
                out_path = st.session_state["tmp_path"] + "_healthy.jpg"
                generate_image(plan.get("image_prompt", ""), out_path)
                st.session_state["generated"] = out_path
            except Exception as e:
                st.error(f"生图失败：{e}")

    if "generated" in st.session_state:
        st.image(st.session_state["generated"], caption=plan.get("healthy_dish_name", "健康版"), width=400)
