# HANDOFF — 项目交接文档

> 本文件给 3 号位（录 Demo 视频）和 4 号位（写小组报告）及其 **AI agent** 阅读，用于理解 1 号位 + 2 号位已完成的工作。请 agent 先通读本文件再继续。

---

## 0. 三句话概括

- 项目：**AI 健康饮食改造师**——上传食物照片 → VLM 识别食材克重 → 营养库核算热量 → 结合用户健康目标与档案给出改造方案 + 预期效果 + 食材替换建议 → 文生图生成"健康版"菜品。
- 技术栈：Python 3.12 + Streamlit + Plotly + 阿里百炼 / 智谱 / 豆包三方 VLM + 通义万相文生图。
- 当前状态：**主链路 + 跨模型对比 + 营养仪表盘 + 导出报告 + 历史记录 + 多页面导航全部完成**，Demo 运行于 `http://localhost:8501`。

## 1. 你的任务

### 3 号位：录 Demo 视频（<3 分钟）
- 演示完整流程：上传图片 → 多模型分析 → 仪表盘 → 替换建议 → 生成效果图 → 导出报告 → 保存历史 → 查看历史记录
- 建议用 OBS 或系统自带录屏，包含语音讲解

### 4 号位：写小组总体报告（LaTeX，≤20 页）
- 报告模板在 `report/report.tex`
- 需包含：系统架构、Prompt 设计、跨模型对比实验、Demo 截图、个人贡献
- 参考 `README.md` 和本文件了解全貌

## 2. 已完成工作（勿重复）

### 1 号位完成

| 交付物 | 位置 | 说明 |
|--------|------|------|
| 食物筛选脚本 | `filter_food.py` | 2369→232 张食物图，支持断点续传 |
| 标注脚本 | `annotate_dataset.py` | 全量结构化标注，V5 版输出克重 |
| V5 标注数据 | `output/annotations_v5.jsonl` | 362/362 条，含食材克重（首选数据） |
| 旧标注数据 | `output/annotations.jsonl` | V2 版 362 条（保留对比用） |
| 食物图库 | `food_merged/` | 362 张（ff_=课程数据，fe_=Food-101） |
| Prompt 实验 | `prompt_experiment.py` + `pe_results/` | 5 版 Prompt × 20 图，含 `comparison.json` |
| Module A | `modules/vision_analyzer.py` | V5 分析 + is_food 校验 + 缓存 |
| 营养库 | `modules/nutrition_db.py` | 成分表法热量、BMI/TDEE、未收录兜底 |
| Module B | `modules/health_advisor.py` | 改造方案 + 用户档案 + 预期效果 + 缓存 |
| Module C | `modules/image_generator.py` | wanx 文生图 |
| 原始 Demo | `app.py`（1 号位版） | Streamlit 基础单页面 |

### 2 号位完成（本次交接新增）

| 交付物 | 位置 | 说明 |
|--------|------|------|
| 多模型选择器 | `app.py` 侧边栏 | 4 个模型可选多选：qwen-vl-plus / qwen-vl-max / glm-4v / doubao-seed-2.0 |
| GLM-4V 适配器 | `modules/vision_analyzer.py` | 智谱 API 集成（base64 图片 + HTTP 调用） |
| 豆包适配器 | `modules/vision_analyzer.py` | 火山引擎 Ark 集成（ep-20260815154546-cz6bs） |
| 多模型 Tab 展示 | `app.py` | 每模型一个 Tab，并排对比 |
| 模型对比表 | `app.py` | 菜名/食材数/热量/风险标签 并排 |
| 营养仪表盘 | `app.py` | Plotly 环形图（食材占比）+ 柱状图（模型对比）+ TDEE 环形图 |
| 食材替换建议 | `modules/health_advisor.py` | `generate_swap_suggestions()`：LLM 给出具体替换方案 |
| 导出报告 | `app.py` | `build_report_html()`：HTML 报告下载（含图片 base64） |
| 多页面导航 | `app.py` 侧边栏 | 食物分析 / 历史记录 / 关于项目 |
| 历史记录 | `app.py` + `output/history.json` | 保存/折叠回看/删除/清空，最多 50 条 |
| API Key 配置 | `.env` | 新增 `ZHIPU_API_KEY`、`DOUBAO_API_KEY` |

## 3. 技术要点（agent 开发必读）

### 3.1 Prompt 设计（V5 视觉分析）
- System：`你是一名资深营养师兼专业美食摄影师…只输出严格的 JSON`
- User 要求输出：`dish_name` / `ingredients[{name, weight_g}]` / `cooking_method` / `health_risk_tags` / `model_calories` / `visual_description`
- 核心技巧：**角色扮演 + 嵌套 JSON 强约束 + 克重估算 + 枚举白名单 + 禁止 markdown**

### 3.2 热量核算
- 公式：`总热量 = Σ (weight_g/100 × 每100g热量) + 烹饪油量调整`
- 油炸补 30g 油、炒制补 15g 油（未列油时）；未收录食材按 120 kcal/100g 兜底并提示。

### 3.3 API 配置
- `.env` 文件包含以下 Key：
  - `DASHSCOPE_API_KEY`：阿里百炼（qwen-vl-plus/max、qwen-plus、wanx-v1）
  - `ZHIPU_API_KEY`：智谱 GLM-4V
  - `DOUBAO_API_KEY`：火山引擎豆包（ep-20260815154546-cz6bs）
- **缓存**：`output/analysis_cache.json`（按 `图片哈希_模型名` 缓存）、`output/plan_cache.json`（按分析+目标哈希）
- 缓存 key 包含模型名，不同模型不会串缓存

### 3.4 跨模型适配器架构
- `vision_analyzer.py` 中 `analyze_with_check` 按模型名路由：
  - `glm-*` → 智谱 API（HTTP POST + base64 图片）
  - `ep-*` 或 `doubao-*` → 豆包 Ark API（HTTP POST + base64 + MIME 前缀）
  - 其余 → 阿里百炼 DashScope SDK
- 新增模型只需在 `app.py` 的 `MODELS` 字典添加映射，并在 `vision_analyzer.py` 添加路由

### 3.5 常见坑
- Windows 控制台 GBK：跑 Python 脚本前设 `$env:PYTHONIOENCODING="utf-8"`（脚本内有 emoji 打印）
- Streamlit 按钮：点击即整页重跑，状态必须用 `st.session_state`（不要嵌套按钮逻辑）
- 营养库匹配：按"最长子串"匹配食材名，单字 key 会被跳过
- 豆包 API：必须用推理接入点 ID（ep-xxxx），不能直接用模型名；图片必须带 `data:image/jpeg;base64,` MIME 前缀
- 智谱 API：图片需 base64 编码，通过 HTTP POST 调用

## 4. 待办事项

- [ ] **3 号位** 录 Demo 视频（<3 分钟，展示完整流程 + 多模型对比 + 新功能）
- [ ] **4 号位** 写小组总体报告（LaTeX，≤20 页）
- [ ] 报告补 **Demo 截图**（`report/report.tex` 6.3 节）——含仪表盘、替换建议、历史记录等新功能截图
- [ ] `个人贡献报告.md` 填姓名学号
- [ ] （可选）跑 `prompt_experiment.py` 的跨模型对比实验，产出量化对比表用于报告

## 5. 运行命令

```bash
# 启动 Demo（http://localhost:8501）
streamlit run app.py

# 跨模型对比实验（可选，用于报告量化数据）
python prompt_experiment.py --version all --model qwen-vl-max

# 重新标注（V5，含克重）
python annotate_dataset.py
```

## 6. Demo 功能全景

| 功能 | 位置 | 说明 |
|------|------|------|
| 食物分析 | 侧边栏 → 食物分析 | 上传图片 → 多模型分析 → 仪表盘 → 替换建议 → 效果图 → 导出报告 → 保存历史 |
| 历史记录 | 侧边栏 → 历史记录 | 折叠列表，支持回看/删除/清空 |
| 关于项目 | 侧边栏 → 关于项目 | 项目简介 + 技术栈 + 模块说明 |
| 模型选择 | 侧边栏 | 四选多：qwen-vl-plus/max、glm-4v、doubao-seed-2.0 |
| 营养仪表盘 | 分析结果下方 | Plotly 环形图 + 柱状图 + TDEE 占比 |
| 食材替换 | 点击按钮 | LLM 生成具体替换方案 |
| 导出报告 | 分析结果下方 | HTML 下载，含图片 base64 |

## 7. 数据规模与成本

- 食物图库 362 张；每张 V5 分析约 1300 token（max_pixels 控制分辨率）
- 免费额度：qwen-vl-plus 新账号约 100 万 token，跑完全部标注/实验尚有富余
- 智谱 GLM-4V 新账号有免费 token
- 豆包 Doubao-Seed-2.0 新账号有免费额度
- 生图仅 Demo 点击时调用，按张计费（约 0.2 元/张）

> 有任何疑问：先查 `README.md`，再查本文件，最后看各模块源码。