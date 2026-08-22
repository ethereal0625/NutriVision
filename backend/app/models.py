"""数据库模型：用户 + 历史记录 + 每日计划 + 品牌商品"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(300), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    history = relationship("HistoryItem", back_populates="user", cascade="all, delete-orphan")
    plan = relationship("UserPlan", back_populates="user", cascade="all, delete-orphan", uselist=False)


class UserPlan(Base):
    """用户每日饮食计划：每日热量目标 + 目标类型"""
    __tablename__ = "user_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    target_calories = Column(Integer, default=2000)
    goal = Column(String(20), default="均衡饮食")
    reminder_enabled = Column(Integer, default=0)
    protein_goal = Column(Float, nullable=True)   # 每日蛋白质目标（克）
    carb_goal = Column(Float, nullable=True)     # 每日碳水目标（克）
    fat_goal = Column(Float, nullable=True)      # 每日脂肪目标（克）
    # 个人档案（用于 TDEE 计算）
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(10), default="男")
    activity = Column(String(10), default="轻度")
    # 热量目标模式：auto=按目标智能推荐  manual=手动设定缺口/盈余
    calorie_mode = Column(String(10), default="auto")
    adjustment = Column(Integer, default=0)     # 缺口/盈余（正=盈余，负=缺口，0=平衡）
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="plan")


class HistoryItem(Base):
    """饮食记录：关联日期与餐次"""
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    dish_name = Column(String(100), default="")
    calories = Column(Integer, default=0)
    models = Column(String(200), default="")
    goal = Column(String(50), default="")
    result_json = Column(Text, default="{}")
    date = Column(String(10), default="")        # YYYY-MM-DD
    meal_type = Column(String(10), default="")   # 早餐/午餐/晚餐/加餐/饮品
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="history")


class FoodProduct(Base):
    """品牌商品热量库（按每份记）"""
    __tablename__ = "food_products"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(50), default="")
    name = Column(String(100), nullable=False, index=True)
    serving = Column(String(50), default="")
    kcal = Column(Integer, default=0)
    note = Column(String(200), default="")

