"""后端配置"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
PROJECT_ROOT = BASE_DIR.parent                             # handoff/
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.environ.get("NUTRIVISION_DB", f"sqlite:///{DATA_DIR / 'nutrivision.db'}")
SECRET_KEY = os.environ.get("NUTRIVISION_SECRET", "change-me-in-production-9f8a7b6c5d")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7
