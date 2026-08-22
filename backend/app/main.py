"""NutriVision FastAPI 后端入口"""
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from .database import Base, SessionLocal, engine
from .routers import analyze, auth, compensate, history, plan, products, profile, report, tips, water

Base.metadata.create_all(bind=engine)

# 轻量迁移：给已有的表补列（老库升级用）
def _migrate():
    with SessionLocal() as db:
        insp = inspect(engine)
        if "history" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("history")}
            for col, ddl in [("date", "VARCHAR(10) DEFAULT ''"), ("meal_type", "VARCHAR(10) DEFAULT ''")]:
                if col not in cols:
                    db.execute(text(f"ALTER TABLE history ADD COLUMN {col} {ddl}"))
        if "user_plans" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("user_plans")}
            for col, ddl in [
                ("reminder_enabled", "INTEGER DEFAULT 0"),
                ("protein_goal", "FLOAT"),
                ("carb_goal", "FLOAT"),
                ("fat_goal", "FLOAT"),
                ("height_cm", "FLOAT"),
                ("weight_kg", "FLOAT"),
                ("age", "INTEGER"),
                ("gender", "VARCHAR(10) DEFAULT '男'"),
                ("activity", "VARCHAR(10) DEFAULT '轻度'"),
                ("calorie_mode", "VARCHAR(10) DEFAULT 'auto'"),
                ("adjustment", "INTEGER DEFAULT 0"),
                ("water_goal", "INTEGER DEFAULT 2000"),
            ]:
                if col not in cols:
                    db.execute(text(f"ALTER TABLE user_plans ADD COLUMN {col} {ddl}"))
        db.commit()

_migrate()

app = FastAPI(title="NutriVision API", version="2.1.0", description="AI 健康饮食改造师 - 前后端分离后端")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段放开；上线前收紧
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(history.router)
app.include_router(plan.router)
app.include_router(products.router)
app.include_router(profile.router)
app.include_router(report.router)
app.include_router(compensate.router)
app.include_router(tips.router)
app.include_router(water.router)


@app.get("/")
def root():
    return {"name": "NutriVision API", "version": "2.1.0", "docs": "/docs"}