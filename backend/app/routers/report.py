"""周报路由：生成可打印/可存 PDF 的 HTML 饮食周报"""
import html
import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import HistoryItem, User, UserPlan
from ..routers.auth import get_current_user
from ..routers.plan import default_macro_goals, parse_macros

router = APIRouter(prefix="/api/report", tags=["report"])

GOAL_EMOJI = {"减脂": "🔥", "控糖": "🍬", "增肌": "💪", "均衡饮食": "⚖️"}
MEAL_COLORS = {"早餐": "#f59e0b", "午餐": "#3ba56f", "晚餐": "#2e8b57", "加餐": "#ff8c42", "饮品": "#64776c"}


@router.get("", response_class=HTMLResponse)
def weekly_report(days: int = 7, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    days = max(1, min(int(days), 90))
    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    target = (plan.target_calories if plan and plan.target_calories else 2000)
    goal = (plan.goal or "均衡饮食") if plan else "均衡饮食"

    today = date.today()
    start = today - timedelta(days=days - 1)

    # 周期内全部记录
    items = (
        db.query(HistoryItem)
        .filter(HistoryItem.user_id == user.id, HistoryItem.date >= start.isoformat(), HistoryItem.date <= today.isoformat())
        .order_by(HistoryItem.date.asc(), HistoryItem.created_at.asc())
        .all()
    )

    # 逐日聚合
    daily = []
    macro_sum = {"protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        day_items = [x for x in items if x.date == d.isoformat()]
        total = sum(x.calories or 0 for x in day_items)
        for x in day_items:
            m = parse_macros(x.result_json)
            for k in macro_sum:
                macro_sum[k] += m[k]
        daily.append({"date": d, "label": _fmt_date(d), "total": total, "target": target, "items": day_items})

    # 餐次分布
    meal_rows = (
        db.query(HistoryItem.meal_type, func.sum(HistoryItem.calories))
        .filter(HistoryItem.user_id == user.id, HistoryItem.date >= start.isoformat())
        .group_by(HistoryItem.meal_type)
        .all()
    )
    meal_dist = [{"meal_type": k or "未分类", "calories": int(v or 0)} for k, v in meal_rows if v]
    meal_dist.sort(key=lambda m: -m["calories"])

    # 达标天数（±20%）
    within = sum(1 for d in daily if d["total"] and abs(d["total"] - target) <= target * 0.2)
    total_sum = sum(d["total"] for d in daily)
    avg = round(total_sum / days, 1) if days else 0

    # 本周 vs 上周
    week_start = today - timedelta(days=today.weekday())
    last_week_start = week_start - timedelta(days=7)

    def avg_between(s, e):
        t = db.query(HistoryItem).filter(
            HistoryItem.user_id == user.id,
            HistoryItem.date >= s.isoformat(),
            HistoryItem.date < e.isoformat(),
        ).with_entities(func.coalesce(func.sum(HistoryItem.calories), 0)).scalar() or 0
        return round(t / 7, 1)

    this_week_avg = avg_between(week_start, today + timedelta(days=1))
    last_week_avg = avg_between(last_week_start, week_start)

    # 周内所有 AI 分析的宏量记录（供平均展示）
    macro_days = sum(1 for d in daily if any(parse_macros(x.result_json).get("protein") for x in d["items"]))
    macro_avg = {k: round(v / max(macro_days, 1), 1) for k, v in macro_sum.items()}

    # 最高热量一天
    top_day = max(daily, key=lambda d: d["total"]) if any(d["total"] for d in daily) else None

    html_doc = _render(user.username, goal, target, avg, within, days, daily, meal_dist,
                       this_week_avg, last_week_avg, macro_avg, top_day)
    return HTMLResponse(content=html_doc)


def _fmt_date(d: date) -> str:
    week = "一二三四五六日"[d.weekday()]
    return f"{d.month}月{d.day}日 周{week}"


def _render(username, goal, target, avg, within, days, daily, meal_dist, this_week_avg, last_week_avg, macro_avg, top_day) -> str:
    # 逐日柱状图：高度按目标比例
    bars = []
    for d in daily:
        pct = min(d["total"] / target * 100, 100) if target else 0
        over = d["total"] > target * 1.2
        color = "#f97316" if over else "#3ba56f"
        count = len(d["items"])
        bars.append(f'''
        <div class="bar-col">
          <div class="bar-val">{d["total"] or ""}</div>
          <div class="bar" style="height:{max(pct, 2)}%;background:{color}"></div>
          <div class="bar-label">{d["label"]}</div>
          <div class="bar-sub">{count} 条记录</div>
        </div>''')

    meal_rows_html = ""
    max_cal = max((m["calories"] for m in meal_dist), default=1)
    for m in meal_dist:
        w = round(m["calories"] / max_cal * 100, 1)
        c = MEAL_COLORS.get(m["meal_type"], "#64776c")
        meal_rows_html += f'''
        <div class="meal-row">
          <div class="meal-name">{html.escape(m["meal_type"])}</div>
          <div class="meal-bar-bg"><div class="meal-bar" style="width:{w}%;background:{c}"></div></div>
          <div class="meal-kcal">{m["calories"]} kcal</div>
        </div>'''

    macro_avg_html = ""
    if macro_days := sum(1 for d in daily if d["total"]):
        md = macro_avg
        macro_avg_html = f'''
        <div class="macro-grid">
          <div class="macro-card"><div class="macro-num">{md["protein"]}g</div><div class="macro-name">🥩 蛋白质</div></div>
          <div class="macro-card"><div class="macro-num">{md["carbs"]}g</div><div class="macro-name">🍚 碳水</div></div>
          <div class="macro-card"><div class="macro-num">{md["fat"]}g</div><div class="macro-name">🥑 脂肪</div></div>
        </div>'''

    trend = "📈 本周比上周"
    trend_color = "#f97316"
    if this_week_avg < last_week_avg:
        trend = "📉 本周比上周"
        trend_color = "#3ba56f"

    top_day_html = ""
    if top_day and top_day["total"]:
        top_day_html = f'''
        <div class="note-card">
          <span class="note-icon">⚠️</span>
          <span><b>摄入最高的一天</b>：{top_day["label"]}（{top_day["total"]} kcal）。这天吃了 {len(top_day["items"])} 条记录，如果想控制体重，可以回顾一下当天的加餐和饮品~</span>
        </div>'''

    today_str = date.today().strftime("%Y年%m月%d日")
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>NutriVision 饮食周报</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif; color:#17251d; background:#eef3ef; padding:32px 16px; }}
  .page {{ max-width:820px; margin:0 auto; background:#fff; border-radius:20px; overflow:hidden; box-shadow:0 10px 40px rgba(23,37,29,.08); }}
  .header {{ background:linear-gradient(135deg,#1d4a32,#2e8b57 55%,#3ba56f); color:#fff; padding:36px 44px; }}
  .header h1 {{ font-size:26px; font-weight:800; letter-spacing:1px; }}
  .header .sub {{ margin-top:6px; font-size:13px; opacity:.85; }}
  .header .meta {{ margin-top:16px; font-size:12px; opacity:.75; }}
  .body {{ padding:32px 44px 40px; }}
  .stat-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
  .stat {{ background:#f4f9f6; border:1px solid #e3efe8; border-radius:14px; padding:16px 12px; text-align:center; }}
  .stat .num {{ font-size:24px; font-weight:800; color:#1d4a32; }}
  .stat .lbl {{ font-size:11px; color:#64776c; margin-top:4px; }}
  h2 {{ font-size:16px; font-weight:700; color:#17251d; margin:30px 0 14px; display:flex; align-items:center; gap:8px; }}
  h2 .line {{ flex:1; height:1px; background:#e9f0ec; }}
  .chart {{ height:200px; display:flex; align-items:flex-end; gap:12px; padding:8px 4px 0; }}
  .bar-col {{ flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%; }}
  .bar-val {{ font-size:11px; color:#17251d; font-weight:700; margin-bottom:4px; }}
  .bar {{ width:70%; max-width:44px; border-radius:6px 6px 0 0; min-height:3px; }}
  .bar-label {{ font-size:11px; color:#64776c; margin-top:6px; }}
  .bar-sub {{ font-size:9px; color:#9db0a6; margin-top:1px; }}
  .meal-row {{ display:flex; align-items:center; gap:12px; margin-bottom:10px; }}
  .meal-name {{ width:52px; font-size:13px; font-weight:600; }}
  .meal-bar-bg {{ flex:1; height:12px; background:#f4f9f6; border-radius:8px; overflow:hidden; }}
  .meal-bar {{ height:100%; border-radius:8px; }}
  .meal-kcal {{ width:74px; text-align:right; font-size:12px; color:#64776c; }}
  .macro-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }}
  .macro-card {{ background:#fffdf5; border:1px solid #f0e8d0; border-radius:14px; padding:14px; text-align:center; }}
  .macro-num {{ font-size:20px; font-weight:800; color:#1d4a32; }}
  .macro-name {{ font-size:12px; color:#64776c; margin-top:3px; }}
  .note-card {{ display:flex; gap:10px; background:#fff8f0; border:1px solid #ffe4c2; border-radius:12px; padding:14px 16px; font-size:13px; color:#7c4a03; line-height:1.6; }}
  .note-icon {{ font-size:16px; }}
  .footer {{ text-align:center; font-size:11px; color:#9db0a6; padding:0 44px 30px; }}
  @media print {{
    body {{ background:#fff; padding:0; }}
    .page {{ box-shadow:none; border-radius:0; }}
    .header {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
    .bar, .meal-bar {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
  }}
</style>
</head>
<body>
  <div class="page">
    <div class="header">
      <h1>🥗 NutriVision 饮食周报</h1>
      <div class="sub">@ {html.escape(username)} · {GOAL_EMOJI.get(goal, "⚖️")} 目标：{html.escape(goal)}</div>
      <div class="meta">统计周期：近 {days} 天（{daily[0]["label"]} ~ {daily[-1]["label"]}） · 生成于 {today_str}</div>
    </div>
    <div class="body">
      <div class="stat-grid">
        <div class="stat"><div class="num">{avg}</div><div class="lbl">日均摄入 kcal</div></div>
        <div class="stat"><div class="num">{target}</div><div class="lbl">每日目标 kcal</div></div>
        <div class="stat"><div class="num">{within}/{days}</div><div class="lbl">达标天数</div></div>
        <div class="stat"><div class="num" style="color:{trend_color}">{this_week_avg}</div><div class="lbl">本周日均 kcal</div></div>
      </div>

      <h2>📊 每日摄入 <span class="line"></span></h2>
      <div class="chart">{''.join(bars)}</div>
      <p style="font-size:11px;color:#9db0a6;margin-top:8px;">绿色柱 = 在目标 ±20% 内 · 橙色柱 = 超出目标 · 柱高按目标百分比</p>

      <h2>🍱 餐次热量分布 <span class="line"></span></h2>
      {meal_rows_html if meal_rows_html else '<p style="font-size:13px;color:#9db0a6;">近 ' + str(days) + ' 天暂无餐次记录</p>'}

      <h2>🥩 平均宏量营养素（有 AI 分析的日子） <span class="line"></span></h2>
      {macro_avg_html if macro_avg_html else '<p style="font-size:13px;color:#9db0a6;">暂无 AI 分析记录，用「食物分析」上传图片后即可统计</p>'}

      <h2>📉 本周 vs 上周 <span class="line"></span></h2>
      <div class="stat-grid">
        <div class="stat"><div class="num">{this_week_avg}</div><div class="lbl">本周日均 kcal</div></div>
        <div class="stat"><div class="num">{last_week_avg}</div><div class="lbl">上周日均 kcal</div></div>
        <div class="stat" style="grid-column:span 2"><div class="num" style="font-size:18px;color:{trend_color}">{trend} {abs(round(this_week_avg - last_week_avg, 1))} kcal</div><div class="lbl">变化幅度</div></div>
      </div>

      {top_day_html}
    </div>
    <div class="footer">NutriVision · AI 健康饮食改造师 · 本报告由你的饮食记录自动生成，仅供参考，不构成医疗建议</div>
  </div>
</body>
</html>'''
