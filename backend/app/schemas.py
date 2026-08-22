"""Pydantic 请求/响应模型"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str = ""


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryCreate(BaseModel):
    dish_name: str = ""
    calories: int = 0
    models: str = ""
    goal: str = ""
    result_json: str = "{}"
    date: str = ""
    meal_type: str = ""


class HistoryOut(BaseModel):
    id: int
    dish_name: str
    calories: int
    models: str
    goal: str
    result_json: str
    date: str
    meal_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class PlanUpdate(BaseModel):
    target_calories: int = 2000
    goal: str = "均衡饮食"
    reminder_enabled: Optional[bool] = None
    protein_goal: Optional[float] = None
    carb_goal: Optional[float] = None
    fat_goal: Optional[float] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    activity: Optional[str] = None
    calorie_mode: Optional[str] = None
    adjustment: Optional[int] = None


class PlanOut(BaseModel):
    target_calories: int
    goal: str
    reminder_enabled: bool = False
    protein_goal: Optional[float] = None
    carb_goal: Optional[float] = None
    fat_goal: Optional[float] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    activity: Optional[str] = None
    calorie_mode: str = "auto"
    adjustment: int = 0
    # 计算信息（get_plan 附加，非数据库字段）
    tdee: Optional[int] = None
    recommended_adjustment: Optional[int] = None
    target_note: str = ""

    class Config:
        from_attributes = True


class DayMeal(BaseModel):
    id: int
    dish_name: str
    calories: int
    meal_type: str
    models: str
    time: str
    macros: Optional[dict] = None


class DayOut(BaseModel):
    date: str
    target_calories: int
    goal: str
    total_calories: int
    remaining: int
    percent: float
    meals: List[DayMeal]
    macros: dict = {}
    macro_targets: dict = {}


class ProductOut(BaseModel):
    id: int
    brand: str
    name: str
    serving: str
    kcal: int
    note: str

    class Config:
        from_attributes = True
