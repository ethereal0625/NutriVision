# NutriVision 开发进度交接

> 更新时间：2026-08-22 · 最后提交：08137ae

## 服务启动方式

```bash
# 后端（端口 8000）
cd D:\VLP\handoff\backend && D:\Python\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端（端口 5173）
cd D:\VLP\handoff\frontend && npm run dev
```

测试账号：`user887840 / demo123456`

## 已完成功能（本轮优化）

| 优先级 | 功能 | 位置 | 状态 |
|--------|------|------|------|
| P0 | 营养评分系统（A/B/C/D） | `modules/nutrition_score.py` + analyze.py + Analyze.jsx | ✅ 完成 |
| P0 | 食物数据库扩充（+45 种中式菜） | `modules/nutrition_db.py` | ✅ 完成 |
| P1 | 宏量营养素雷达图 | Analyze.jsx（recharts） | ✅ 完成 |
| P1 | 近 7 天热量趋势图 | Plan.jsx（recharts AreaChart） | ✅ 完成 |
| P1 | 成就徽章系统（6 枚） | `backend/app/routers/badges.py` + Badges.jsx | ✅ 完成 |
| P2 | 分享卡片（Canvas 生成 PNG） | Analyze.jsx | ✅ 完成 |

另有早前完成的：膳食动态补偿（/api/compensate）、饮水打卡（/api/water/*）、PWA 移动端、改造前后对比卡片 + 难度分级。

## 剩余可做（未完成）

1. **P2 条码扫描**：需要 `html5-qrcode` 依赖 + 摄像头权限 + 扩充 `food_products` 品牌商品表。建议移动端真机验证。
2. **P2 社区/分享墙**：需要后端帖子/点赞/评论模型，工作量较大。
3. **前端大 chunk 优化**：构建提示 714KB 单 chunk，可做路由级代码分割（React.lazy）。
4. **Sealos 云部署**：下轮对话可直接用已安装的 sealos-deploy skill 部署。

## 注意

- `Analyze.jsx` 曾有重复评分卡片（4 份），已清理为 1 份，勿再重复插入。
- 修改 JSX/Python 文件时，推荐用 `apply_patch` 或写一次性 Python 脚本（避免 PowerShell 转义问题）。
- 数据库迁移在 main.py `_migrate()` 中维护（water_goal 等）。
- 本项目使用付费 API（通义千问/豆包），部署时密钥放环境变量，勿提交。
