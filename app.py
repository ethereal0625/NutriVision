"""
app.py - NutriVision 多页面网站
页面：首页（落地页）/ 食物分析 / 历史记录 / 关于项目
每个页面有独立 URL：/home  /analyze  /history  /about
"""
import base64
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from logging_config import setup_logging
setup_logging()

import streamlit as st
import plotly.graph_objects as go

from config import CACHE_FILES, LIMITS, MODELS
from modules.health_advisor import GOALS, generate_plan, generate_swap_suggestions
from modules.image_generator import generate_image
from modules.composition_preserve import generate_with_composition
from modules.nutrition_db import bmi, bmi_category, compute_calories, tdee
from modules.vision_analyzer import analyze_with_check

st.set_page_config(page_title="AI 健康饮食改造师", layout="wide", page_icon="🥗")

MODEL_LABELS = {
    "qwen-vl-plus": "通义千问 Qwen-VL-Plus",
    "qwen-vl-max": "通义千问 Qwen-VL-Max",
    "glm-4v": "智谱 GLM-4V",
    "doubao-seed-2.0": "豆包 Seed",
}

def model_label(m: str) -> str:
    return MODEL_LABELS.get(m, m)

HISTORY_FILE = CACHE_FILES["history"]

def _load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def _save_history(entry: dict) -> None:
    hist = _load_history()
    hist.insert(0, entry)
    del hist[LIMITS["max_history_items"]:]
    HISTORY_FILE.write_text(json.dumps(hist, ensure_ascii=False), encoding="utf-8")

def _img_to_b64(path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(Path(path).read_bytes()).decode("utf-8")

CSS = """
<style>
:root {
  --green: #2e8b57;
  --green-light: #e8f5ee;
  --accent: #ff8c42;
  --text: #1f2d3d;
}
.stApp {
  background: linear-gradient(160deg, #f6fbf8 0%, #eef4f1 100%);
}
html, body, [class*="css"] {
  font-family: "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
  color: var(--text);
}
/* ===== 顶部导航（网站式 Navbar）===== */
[data-testid="stHeader"] { background: rgba(255,255,255,.92); backdrop-filter: blur(8px); }
[data-testid="stNavigationTop"] {
  background: rgba(255,255,255,.95);
  border-bottom: 1px solid #e5ece8;
  padding: 6px 18px;
}
[data-testid="stNavigationTop"] a {
  color: var(--text) !important;
  font-weight: 600;
  padding: 8px 16px !important;
  border-radius: 999px;
  transition: all .15s ease;
}
[data-testid="stNavigationTop"] a:hover { background: var(--green-light); color: var(--green) !important; }
[data-testid="stNavigationTop"] a[aria-current="page"], [data-testid="stNavigationTop"] a.active {
  background: linear-gradient(120deg, #2e8b57, #3ba56f) !important;
  color: #fff !important;
  box-shadow: 0 4px 12px rgba(46,139,87,.25);
}
/* ===== 通用组件 ===== */
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
[data-testid="stSidebar"] {
  background: #ffffff;
  border-right: 1px solid #edf1ef;
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  color: var(--green);
}
[data-testid="stMetric"] {
  background: white;
  border-radius: 12px;
  padding: 14px 16px;
  border: 1px solid #eef2f0;
  box-shadow: 0 2px 8px rgba(31,45,61,.05);
}
[data-testid="stMetricValue"] { color: var(--green); }
.stProgress > div > div > div > div { background: linear-gradient(90deg, #2e8b57, #ff8c42); }
[data-testid="stFileUploaderDropzone"] {
  border: 2px dashed var(--green);
  border-radius: 14px;
  background: #f4faf6;
}
[data-testid="stSpinner"] { color: var(--green); }
hr { border-color: #e5ece8; }
/* ===== 首页落地页 ===== */
.landing-hero {
  text-align: center;
  padding: 72px 24px 56px;
  background: radial-gradient(1200px 500px at 50% -10%, #d9f0e4 0%, rgba(246,251,248,0) 60%);
}
.landing-badge {
  display: inline-block;
  background: #e8f5ee;
  color: #2e8b57;
  border: 1px solid #c7e8d8;
  border-radius: 999px;
  padding: 5px 14px;
  font-size: .85rem;
  font-weight: 600;
  margin-bottom: 18px;
}
.landing-hero h1 {
  font-size: clamp(2rem, 5vw, 3.4rem);
  line-height: 1.25;
  margin: 0 0 16px;
  color: var(--text);
  font-weight: 800;
}
.landing-hero p {
  font-size: clamp(1rem, 2vw, 1.2rem);
  color: #5a6b5f;
  max-width: 680px;
  margin: 0 auto 28px;
}
.landing-cta {
  display: inline-block;
  background: linear-gradient(120deg, #2e8b57, #3ba56f);
  color: #fff !important;
  font-size: 1.05rem;
  font-weight: 700;
  padding: 14px 36px;
  border-radius: 999px;
  text-decoration: none !important;
  box-shadow: 0 8px 24px rgba(46,139,87,.35);
  transition: transform .15s ease;
}
.landing-cta:hover { transform: translateY(-2px); color: #fff !important; }
.stats {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 18px;
  margin: 8px 0 40px;
}
.stat-box {
  background: #fff;
  border: 1px solid #eef2f0;
  border-radius: 14px;
  padding: 18px 26px;
  min-width: 130px;
  text-align: center;
  box-shadow: 0 3px 12px rgba(31,45,61,.06);
}
.stat-box .num { font-size: 1.7rem; font-weight: 800; color: var(--green); }
.stat-box .lbl { font-size: .85rem; color: #8492a6; margin-top: 2px; }
.feat-card {
  background: #fff;
  border: 1px solid #eef2f0;
  border-radius: 16px;
  padding: 22px;
  height: 100%;
  box-shadow: 0 3px 12px rgba(31,45,61,.06);
  transition: transform .15s ease, box-shadow .15s ease;
}
.feat-card:hover { transform: translateY(-3px); box-shadow: 0 10px 24px rgba(31,45,61,.1); }
.feat-card .ico { font-size: 2rem; }
.feat-card h4 { margin: 10px 0 6px; color: var(--text); font-size: 1.05rem; }
.feat-card p { margin: 0; color: #5a6b5f; font-size: .9rem; line-height: 1.6; }
.step-num {
  width: 44px; height: 44px; border-radius: 50%;
  background: linear-gradient(120deg, #2e8b57, #3ba56f);
  color: #fff; font-weight: 800; font-size: 1.1rem;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 10px;
}
.section-title { text-align: center; margin: 40px 0 20px; }
.section-title h2 { font-size: 1.7rem; font-weight: 800; margin: 0 0 6px; }
.section-title p { color: #8492a6; margin: 0; }
.footer {
  text-align: center; color: #8492a6; font-size: .85rem;
  padding: 40px 0 24px; margin-top: 40px; border-top: 1px solid #e5ece8;
}
/* ===== 移动端 ===== */
@media (max-width: 768px) {
  .hero { padding: 20px 18px; border-radius: 14px; padding-top: calc(20px + env(safe-area-inset-top)); }
  .hero h1 { font-size: 1.5rem; }
  .card { padding: 16px 14px; }
  [data-testid="stMetric"] { padding: 10px 12px; }
  .landing-hero { padding: 48px 16px 36px; }
  [data-testid="stNavigationTop"] { padding: 4px 8px; overflow-x: auto; }
  [data-testid="stNavigationTop"] a { padding: 7px 12px !important; font-size: .88rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def _render_analysis_card(analysis: dict, model_name: str):
    """渲染单个模型的原图分析卡片，返回 (核算热量, 明细, 未收录)。"""
    computed_calories, breakdown, unlisted = compute_calories(analysis)
    st.markdown(f'<div class="card"><h3>🔬 原图分析（{model_label(model_name)}）</h3>', unsafe_allow_html=True)
    st.markdown(f"**菜名**：{analysis.get('dish_name', '-')}")
    st.markdown(f"**烹饪方式**：{analysis.get('cooking_method', '-')}")
    m1, m2, m3 = st.columns(3)
    m1.metric("模型估算", f"{analysis.get('model_calories', '-')} kcal", f"{model_label(model_name)} 直觉")
    m2.metric("营养库核算", f"{computed_calories} kcal", "成分表法")
    model_c = analysis.get("model_calories") or 0
    m3.metric("偏差", f"{computed_calories - model_c:+d} kcal", "核算−模型")
    if unlisted:
        st.warning("ℹ️ 以下食材营养库未收录，已按 120 kcal/100g 估算：" + "、".join(unlisted))
    st.markdown("**风险标签**")
    tags = analysis.get("health_risk_tags", [])
    if tags:
        st.markdown("".join(f'<span class="chip">{t}</span>' for t in tags), unsafe_allow_html=True)
    else:
        st.markdown('<span class="chip good">无明显风险</span>', unsafe_allow_html=True)
    if breakdown:
        st.markdown("**热量明细（成分表法）**")
        st.table([{
            "食材": b["name"], "克重(g)": b["weight_g"],
            "每100g(kcal)": b["kcal_per_100g"], "小计(kcal)": b["calories"],
        } for b in breakdown])
    st.markdown("</div>", unsafe_allow_html=True)
    return computed_calories, breakdown, unlisted


def build_report_html(tmp_path, food_results, primary, computed_calories, breakdown, unlisted, plan, profile) -> str:
    """生成可下载的 HTML 报告（含原图与效果图 base64、模型对比表等）。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    img_b64 = _img_to_b64(tmp_path) if Path(tmp_path).exists() else ""
    img_html = f'<div class="img-row"><img src="{img_b64}" alt="原图"></div>' if img_b64 else "<p>无图片</p>"
    gen_b64 = ""
    if "generated" in st.session_state and Path(st.session_state["generated"]).exists():
        gen_b64 = _img_to_b64(st.session_state["generated"])
    risk = "、".join(primary.get("health_risk_tags", [])) or "无明显风险"
    ing_rows = "".join(
        f"<tr><td>{b['name']}</td><td>{b['weight_g']}</td><td>{b['kcal_per_100g']}</td><td>{b['calories']}</td></tr>"
        for b in breakdown
    )
    unlisted_html = (
        f'<p class="unlisted">⚠ 未收录食材（按120kcal/100g估算）：{"、".join(unlisted)}</p>' if unlisted else ""
    )
    model_rows = "".join(
        f"<tr><td>{model_label(m)}</td><td>{food_results[m]['analysis'].get('dish_name','-')}</td>"
        f"<td>{len(food_results[m]['analysis'].get('ingredients',[]))}</td>"
        f"<td>{food_results[m]['analysis'].get('model_calories','-')}</td>"
        f"<td>{'、'.join(food_results[m]['analysis'].get('health_risk_tags',[])) or '无明显风险'}</td></tr>"
        for m in food_results
    )
    profile_html = ""
    if profile:
        profile_html = (
            '<div class="section"><h2>👤 用户健康档案</h2><div class="metrics">'
            f'<div class="metric"><span class="label">BMI</span><span class="value">{profile["bmi"]}</span>'
            f'<span class="sub">{bmi_category(profile["bmi"])}</span></div>'
            f'<div class="metric"><span class="label">每日建议摄入</span><span class="value">{profile["tdee"]} kcal</span></div>'
            "</div></div>"
        )
    risks = "".join(f"<li class='risk'>🔴 {p}</li>" for p in plan.get("risk_points", []))
    steps = "".join(f"<li>✅ {s}</li>" for s in plan.get("modification_plan", []))
    effects = (
        f'<div class="effects"><strong>预期效果：</strong>{plan.get("expected_effects", "")}</div>'
        if plan.get("expected_effects") else ""
    )
    gen_html = (
        f'<div class="section"><h2>🖼️ 改造后效果图</h2><div class="img-row"><img src="{gen_b64}" alt="健康版"></div></div>'
        if gen_b64 else ""
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>AI 健康饮食改造报告</title>
<style>
body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #f4f7f5; margin: 0; padding: 24px; color: #1f2d3d; }}
.wrap {{ max-width: 860px; margin: 0 auto; background: #fff; border-radius: 14px; padding: 32px 36px; box-shadow: 0 4px 16px rgba(0,0,0,.08); }}
h1 {{ color: #2e8b57; margin: 0 0 4px; }}
.meta {{ color: #8492a6; font-size: 13px; margin-bottom: 18px; }}
.section {{ margin: 22px 0; }}
.section h2 {{ color: #2e8b57; border-left: 4px solid #2e8b57; padding-left: 10px; font-size: 18px; }}
.img-row img {{ max-width: 100%; border-radius: 10px; }}
.metrics {{ display: flex; gap: 12px; flex-wrap: wrap; }}
.metric {{ background: #f4faf6; border-radius: 10px; padding: 12px 16px; flex: 1; min-width: 140px; }}
.metric .label {{ display: block; color: #8492a6; font-size: 12px; }}
.metric .value {{ font-size: 20px; font-weight: 700; color: #2e8b57; }}
.metric .sub {{ display: block; font-size: 12px; color: #8492a6; }}
table {{ width: 100%; border-collapse: collapse; margin: 8px 0; }}
th, td {{ border: 1px solid #e5ece8; padding: 8px 10px; text-align: left; font-size: 14px; }}
th {{ background: #e8f5ee; color: #2e8b57; }}
.risk {{ color: #c4551d; }}
.plan li {{ margin: 4px 0; }}
.effects {{ background: #e8f5ee; border-radius: 10px; padding: 12px 16px; margin: 10px 0; color: #2e8b57; }}
.unlisted {{ color: #b08a2e; font-size: 13px; }}
.footer {{ margin-top: 26px; padding-top: 14px; border-top: 1px solid #e5ece8; color: #8492a6; font-size: 12px; text-align: center; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>🥗 AI 健康饮食改造报告</h1>
  <div class="meta">生成时间：{now}</div>
  <div class="section">
    <h2>📸 原始食物图片</h2>
    {img_html}
  </div>
  <div class="section">
    <h2>🔬 食物分析</h2>
    <p><strong>菜名：</strong>{primary.get('dish_name', '-')}</p>
    <p><strong>烹饪方式：</strong>{primary.get('cooking_method', '-')}</p>
    <div class="metrics">
      <div class="metric"><span class="label">模型估算</span><span class="value">{primary.get('model_calories', '-')} kcal</span></div>
      <div class="metric"><span class="label">营养库核算</span><span class="value">{computed_calories} kcal</span></div>
      <div class="metric"><span class="label">偏差</span><span class="value">{computed_calories - (primary.get('model_calories') or 0)} kcal</span></div>
    </div>
    <p style="margin-top:10px"><strong>风险标签：</strong>{risk}</p>
    {unlisted_html}
    <table><tr><th>食材</th><th>克重(g)</th><th>每100g(kcal)</th><th>小计(kcal)</th></tr>{ing_rows}</table>
  </div>
  <div class="section">
    <h2>📊 模型对比</h2>
    <table><tr><th>模型</th><th>菜名</th><th>食材数</th><th>模型热量(kcal)</th><th>风险标签</th></tr>{model_rows}</table>
  </div>
  {profile_html}
  <div class="section">
    <h2>💡 改造方案 → {plan.get('healthy_dish_name', '')}</h2>
    <h3 style="color:#c4551d;margin:12px 0 6px">不健康点</h3>
    <ul>{risks}</ul>
    <h3 style="color:#2e8b57;margin:12px 0 6px">改造步骤</h3>
    <ol class="plan">{steps}</ol>
    {effects}
    <p style="margin-top:10px"><strong>生图 Prompt：</strong><code>{plan.get('image_prompt', '')}</code></p>
  </div>
  {gen_html}
  <div class="footer">
    <p>AI 健康饮食改造师 · AI 健康饮食改造师 · NutriVision</p>
  </div>
</div>
</body>
</html>"""


def _render_dashboard_calories(analysis: dict):
    computed_calories, breakdown, unlisted = compute_calories(analysis)
    if breakdown:
        labels = [b["name"] for b in breakdown]
        values = [b["calories"] for b in breakdown]
        fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.45, textinfo="label+percent"))
        fig.update_layout(title="🔥 食材热量占比", height=320, margin=dict(t=50, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(fig, width="stretch", key="donut_calories")
    else:
        st.caption("暂无食材明细")
    return computed_calories, breakdown, unlisted


def _render_dashboard_models(food_results: dict, computed_by_model: dict):
    models_bar = [model_label(m) for m in food_results]
    cals_bar = [computed_by_model[m] for m in food_results]
    fig = go.Figure(go.Bar(x=models_bar, y=cals_bar, marker_color="#ff8c42"))
    fig.update_layout(title="📊 各模型营养库核算热量", height=320, margin=dict(t=50, b=10, l=10, r=10), yaxis_title="kcal")
    st.plotly_chart(fig, width="stretch", key="bar_models")


def _render_dashboard_tdee(primary_cc: int, profile: dict):
    tdee_val = profile.get("tdee") or 0
    ratio = primary_cc / tdee_val * 100 if tdee_val else 0
    remaining = max(tdee_val - primary_cc, 0)
    fig = go.Figure(go.Pie(
        labels=["本餐热量", "剩余额度"], values=[primary_cc, remaining], hole=0.6,
        textinfo="label+percent", marker=dict(colors=["#2e8b57", "#e8f5ee"]),
    ))
    fig.update_layout(title=f"🎯 占每日建议摄入比例（{ratio:.1f}%）", height=280, margin=dict(t=50, b=10, l=10, r=10), showlegend=False)
    st.plotly_chart(fig, width="stretch", key="donut_tdee")


def home_page():
    st.markdown(
        """
        <div class="landing-hero">
          <div class="landing-badge">AI 健康饮食改造师 · NutriVision</div>
          <h1>拍一张照片，<br>AI 帮你的菜"改健康"</h1>
          <p>上传食物照片 → 识别食材与克重 → 营养库核算热量 → 生成个性化健康改造方案 → 输出"健康版"效果图</p>
          <a class="landing-cta" href="/analyze">🚀 立即体验</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="stats">
          <div class="stat-box"><div class="num">658</div><div class="lbl">营养库食材</div></div>
          <div class="stat-box"><div class="num">411</div><div class="lbl">食物图片</div></div>
          <div class="stat-box"><div class="num">4</div><div class="lbl">视觉模型</div></div>
          <div class="stat-box"><div class="num">3</div><div class="lbl">模型平台</div></div>
          <div class="stat-box"><div class="num">100%</div><div class="lbl">JSON 合规率</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-title"><h2>✨ 核心功能</h2><p>从"识别"到"改造"再到"可视化"的一站式方案</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="feat-card"><div class="ico">🔍</div><h4>多模型视觉识别</h4><p>通义千问 / 智谱 GLM-4V / 豆包三大视觉模型可选，食材与克重级识别。</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="feat-card"><div class="ico">🥗</div><h4>成分级热量核算</h4><p>658 种食材营养库 + 成分表法，逐项核算热量，可追溯、可解释。</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="feat-card"><div class="ico">💡</div><h4>个性化改造方案</h4><p>结合健康目标与个人档案（BMI/TDEE），给出步骤化改造与预期效果。</p></div>', unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown('<div class="feat-card"><div class="ico">🔄</div><h4>食材替换建议</h4><p>AI 逐项给出更健康的替代食材与理由。</p></div>', unsafe_allow_html=True)
    with c5:
        st.markdown('<div class="feat-card"><div class="ico">📊</div><h4>营养仪表盘</h4><p>食材热量占比、模型对比、每日摄入占比一目了然。</p></div>', unsafe_allow_html=True)
    with c6:
        st.markdown('<div class="feat-card"><div class="ico">🎨</div><h4>构图保持效果图</h4><p>本地 Stable Diffusion + ControlNet，保持原图构图生成"健康版"。</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title"><h2>🛠️ 工作原理</h2><p>四步完成"从照片到健康方案"</p></div>', unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown('<div class="feat-card"><div class="step-num">1</div><h4>上传照片</h4><p>上传一张食物图片</p></div>', unsafe_allow_html=True)
    with s2:
        st.markdown('<div class="feat-card"><div class="step-num">2</div><h4>AI 识别</h4><p>VLM 识别菜名、食材与克重</p></div>', unsafe_allow_html=True)
    with s3:
        st.markdown('<div class="feat-card"><div class="step-num">3</div><h4>健康改造</h4><p>营养库核算 + 生成改造方案</p></div>', unsafe_allow_html=True)
    with s4:
        st.markdown('<div class="feat-card"><div class="step-num">4</div><h4>效果预览</h4><p>ControlNet 生成"健康版"效果图</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title"><h2>🏗️ 技术栈</h2></div>', unsafe_allow_html=True)
    st.markdown(
        """
        | 组件 | 技术 |
        |------|------|
        | 前端 | Streamlit + Plotly（PWA，可安装到手机主屏幕） |
        | 视觉模型 | Qwen-VL-Plus / Qwen-VL-Max / GLM-4V / Doubao-Seed-2.0 |
        | 文本模型 | Qwen-Plus |
        | 文生图 | 通义万相（云端） / Stable Diffusion + ControlNet（本地 GPU） |
        | 营养数据 | 658 种食材成分库（中国食物成分表 / USDA 口径） |
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="footer">
          <p>🥗 AI 健康饮食改造师 · AI 健康饮食改造师 · NutriVision</p>
          <p>© 2026 · 数据与代码见 <a href="/about">关于项目</a></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def analyze_page():
    with st.sidebar:
        st.header("🧠 视觉模型")
        vision_models = {m: info for m, info in MODELS.items() if info.get("type") == "vision"}
        selected_models = st.multiselect(
            "视觉模型（可多选对比）",
            list(vision_models),
            default=["qwen-vl-plus"],
            format_func=model_label,
        )
        if not selected_models:
            st.warning("请至少选择一个模型")
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

    st.markdown(
        """
        <div class="hero">
          <h1>🍽️ 食物分析</h1>
          <p>上传食物照片 → VLM 视觉分析 → 个性化健康改造方案 → 文生图效果预览</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader("上传食物图片", type=["jpg", "jpeg", "png"])
    if uploaded and st.button("开始分析", type="primary"):
        if not selected_models:
            st.error("请至少选择一个视觉模型")
            st.stop()
        suffix = Path(uploaded.name).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.read())
            st.session_state["tmp_path"] = tmp.name
        with st.spinner(f"🔍 Module A：{len(selected_models)} 个模型视觉分析中..."):
            results = {}
            for m in selected_models:
                results[m] = analyze_with_check(st.session_state["tmp_path"], model=m)
            st.session_state["analyze_results"] = results
        st.session_state["plan_key"] = None
        st.session_state["plan"] = None
        st.session_state.pop("swap_suggestions", None)
        st.session_state.pop("generated", None)

    if "analyze_results" in st.session_state:
        results = st.session_state["analyze_results"]
        food_results = {m: r for m, r in results.items() if r.get("is_food") and r.get("analysis")}
        if not food_results:
            st.error("⚠️ 未检测到食物：请上传包含食物、菜肴、食材或饮品的图片。")
            st.stop()
        not_food = [m for m, r in results.items() if not (r.get("is_food") and r.get("analysis"))]
        if not_food:
            st.info("部分模型未检测到食物，仅展示检测到食物的模型：" + "、".join(model_label(m) for m in not_food))
        primary_model = list(food_results)[0]
        primary = food_results[primary_model]["analysis"]
        tmp_path = st.session_state["tmp_path"]
        profile = None
        if use_profile:
            profile = {
                "height": height, "weight": weight, "age": age,
                "gender": gender, "activity": activity,
                "bmi": bmi(height, weight),
                "tdee": tdee(height, weight, age, gender, activity),
            }
        st.image(tmp_path, caption="原图", width=320)
        tabs = st.tabs([model_label(m) for m in food_results])
        computed_by_model = {}
        for tab, m in zip(tabs, food_results):
            with tab:
                cc, bd, ul = _render_analysis_card(food_results[m]["analysis"], m)
                computed_by_model[m] = cc
        primary_cc = computed_by_model[primary_model]

        st.markdown("### 📊 模型对比")
        cmp_rows = []
        for m in food_results:
            a = food_results[m]["analysis"]
            cmp_rows.append({
                "模型": model_label(m),
                "菜名": a.get("dish_name", "-"),
                "食材数": len(a.get("ingredients", [])),
                "模型热量(kcal)": a.get("model_calories", "-"),
                "营养库核算(kcal)": computed_by_model[m],
                "风险标签": "、".join(a.get("health_risk_tags", [])) or "无明显风险",
            })
        st.table(cmp_rows)

        st.markdown("### 📊 营养仪表盘")
        d1, d2 = st.columns(2)
        with d1:
            _, primary_breakdown, primary_unlisted = _render_dashboard_calories(primary)
        with d2:
            _render_dashboard_models(food_results, computed_by_model)
        if profile:
            _render_dashboard_tdee(primary_cc, profile)
        else:
            st.caption("👤 填写个人资料后可查看本餐占每日建议摄入的比例")

        plan_key = (goal, bool(profile), primary_model)
        if st.session_state.get("plan_key") != plan_key:
            with st.spinner("🧠 Module B：生成改造方案中..."):
                st.session_state["plan"] = generate_plan(
                    primary, goal, profile=profile, computed_calories=primary_cc
                )
                st.session_state["plan_key"] = plan_key
        plan = st.session_state["plan"]

        if profile:
            st.markdown('<div class="card"><h3>👤 用户健康档案</h3>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.metric("BMI", profile["bmi"], bmi_category(profile["bmi"]))
            c2.metric("每日建议摄入", f"{profile['tdee']} kcal")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card"><h3>💡 「%s」改造方案 → %s</h3>'
                    % (goal, plan.get("healthy_dish_name", "")), unsafe_allow_html=True)
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

        if st.button("🔄 分析可替换食材", type="secondary"):
            with st.spinner("🧠 分析可替换食材中..."):
                st.session_state["swap_suggestions"] = generate_swap_suggestions(primary, goal)
        if "swap_suggestions" in st.session_state:
            swaps = st.session_state["swap_suggestions"]
            if swaps:
                st.markdown('<div class="card"><h3>🔄 食材替换建议</h3>', unsafe_allow_html=True)
                for s in swaps:
                    st.markdown(
                        f"**{s.get('original')}** → 🟢 **{s.get('swap')}**"
                        f"  <small style='color:#8492a6'>（{s.get('reason')}）</small>",
                        unsafe_allow_html=True,
                    )
                st.markdown("</div>", unsafe_allow_html=True)

        report_html = build_report_html(
            tmp_path, food_results, primary, primary_cc,
            primary_breakdown, primary_unlisted, plan, profile,
        )
        st.download_button(
            "⬇️ 下载 HTML 报告",
            data=report_html.encode("utf-8"),
            file_name=f"健康饮食报告_{datetime.now():%Y%m%d_%H%M%S}.html",
            mime="text/html",
        )

        if st.button("💾 保存到历史记录"):
            entry = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "goal": goal,
                "dish_name": primary.get("dish_name", "-"),
                "calories": primary_cc,
                "model_count": len(food_results),
                "models": list(food_results),
                "results": {m: {"is_food": True, "analysis": food_results[m]["analysis"]} for m in food_results},
                "plan": plan,
                "profile": profile,
            }
            if "generated" in st.session_state and Path(st.session_state["generated"]).exists():
                entry["generated_b64"] = _img_to_b64(st.session_state["generated"])
            _save_history(entry)
            st.success("✅ 已保存到历史记录")

        st.subheader("🖼️ Module C：改造后效果图预览")
        gen_mode = st.radio(
            "生图方式",
            ["保持原图构图（ControlNet，本地 GPU）", "通义万相文生图（云端）"],
            horizontal=True,
        )
        if st.button("生成改造后效果图", type="secondary"):
            try:
                out_path = st.session_state["tmp_path"] + "_healthy.jpg"
                if gen_mode.startswith("保持原图构图"):
                    with st.spinner("🧠 ControlNet 构图保持生成中（本地 GPU，约 10-30 秒）..."):
                        generate_with_composition(
                            st.session_state["tmp_path"],
                            plan.get("image_prompt", ""),
                            out_path,
                        )
                else:
                    with st.spinner("🎨 通义万相文生图中（约 1-2 分钟）..."):
                        generate_image(plan.get("image_prompt", ""), out_path)
                st.session_state["generated"] = out_path
            except Exception as e:
                st.error(f"生图失败：{e}")
        if "generated" in st.session_state:
            st.image(st.session_state["generated"], caption=plan.get("healthy_dish_name", "健康版"), width=400)

def history_page():
    st.markdown(
        """
        <div class="hero">
          <h1>📋 历史记录</h1>
          <p>查看历次分析结果，回顾饮食改造历程</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    hist = _load_history()
    if not hist:
        st.info("暂无历史记录。去「食物分析」页面分析菜品后保存即可。")
    else:
        if st.button("🗑️ 清空全部历史"):
            HISTORY_FILE.write_text("[]", encoding="utf-8")
            st.rerun()
        for idx, entry in enumerate(hist):
            with st.expander(
                f"{entry.get('time', '')} | {entry.get('dish_name', '-')} | "
                f"{entry.get('calories')} kcal | 目标：{entry.get('goal', '')}"
            ):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if entry.get("generated_b64"):
                        st.markdown(
                            f'<img src="{entry["generated_b64"]}" style="width:100%;border-radius:10px">',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("（无效果图）")
                with c2:
                    st.markdown("**模型**：" + "、".join(entry.get("models", [])))
                    st.markdown(f"**热量**：{entry.get('calories')} kcal")
                    p = entry.get("profile")
                    if p:
                        st.markdown(f"**BMI**：{p.get('bmi')}）| **TDEE**：{p.get('tdee')}")
                    st.markdown("**改造菜名**：" + str((entry.get("plan") or {}).get("healthy_dish_name", "-")))
                    if st.button("🗑️ 删除此条", key=f"del_{idx}"):
                        cur = _load_history()
                        if idx < len(cur):
                            cur.pop(idx)
                            HISTORY_FILE.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8")
                        st.rerun()


def about_page():
    st.markdown(
        """
        <div class="hero">
          <h1>ℹ️ 关于项目</h1>
          <p>AI 健康饮食改造师 · NutriVision</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        ### 🎯 项目简介

        基于视觉语言大模型（VLM）的个性化健康饮食方案系统：
        上传食物照片 → 自动识别食材克重 → 营养库核算热量 → 结合用户健康目标
        生成个性化改造方案 → 文生图生成"健康版"菜品效果图。

        ### 🏗️ 技术栈

        | 组件 | 技术 |
        |------|------|
        | 前端 | Streamlit（PWA，可安装到手机主屏幕） |
        | 视觉模型 | Qwen-VL-Plus/Max、GLM-4V、Doubao-Seed-2.0 |
        | 文本模型 | Qwen-Plus |
        | 文生图 | 通义万相 wanx-v1 / 本地 Stable Diffusion + ControlNet |
        | 可视化 | Plotly |

        ### 📁 模块说明

        | 模块 | 功能 |
        |------|------|
        | Module A | VLM 视觉分析（食材+克重识别） |
        | 营养数据库 | 658 种食材成分表法热量核算、BMI/TDEE |
        | Module B | 健康改造方案 + 预期效果 + 食材替换 |
        | Module C | 文生图：通义万相 / ControlNet 构图保持 |

        ### 🧪 跨模型实验

        20 张食物图 × 4 视觉模型（V5 Prompt），全部模型 JSON 合规率 100%。
        详细结果见 `pe_results/cross_model/`。

        ### 📄 开源

        本项目已开源：MIT License，代码见 GitHub。
        """
    )


_nav = st.navigation(
    [
        st.Page(home_page, title="首页", icon="🏠", url_path="home", default=True),
        st.Page(analyze_page, title="食物分析", icon="🍽️", url_path="analyze"),
        st.Page(history_page, title="历史记录", icon="📋", url_path="history"),
        st.Page(about_page, title="关于项目", icon="ℹ️", url_path="about"),
    ],
    position="top",
)
_nav.run()
