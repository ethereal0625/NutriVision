"""认证路由：注册 / 登录 / 当前用户"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from ..security import create_access_token, decode_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    username = req.username.strip()
    if len(username) < 2 or len(username) > 30:
        raise HTTPException(400, "用户名长度需在 2-30 个字符之间")
    if len(req.password) < 6:
        raise HTTPException(400, "密码至少 6 位")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, "用户名已被注册")
    user = User(username=username, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.username)
    return TokenResponse(access_token=token, username=user.username)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username.strip()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    token = create_access_token(user.id, user.username)
    return TokenResponse(access_token=token, username=user.username)


def get_current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "未登录")
    try:
        payload = decode_access_token(authorization[7:])
        user = db.get(User, int(payload["sub"]))
    except Exception:
        raise HTTPException(401, "登录已过期，请重新登录")
    if not user:
        raise HTTPException(401, "用户不存在")
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
