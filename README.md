# NutriVision - AI 健康饮食改造师

基于视觉语言大模型（VLM）的个性化健康饮食方案系统：用户上传一张食物照片，系统自动识别菜品成分并估算克重，结合用户的健康目标（减脂 / 控糖 / 增肌 / 均衡饮食）与可选个人档案（身高/体重/年龄等），生成个性化的烹饪改造方案与预期效果，并输出改造后的"健康版"菜品效果图。

> AI 健康饮食改造师 · NutriVision

## ✨ 功能亮点

- **V5 成分级标注**：Prompt 引导 VLM 输出食材及克重（weight_g），再查内置营养数据库逐项核算热量
- **用户健康档案（选填）**：填写身高/体重/年龄/性别/活动量后，系统计算 BMI 与每日建议摄入（TDEE）
- **预期效果量化**：改造建议附带预期效果（如"每餐减少约 310 kcal，坚持 1 个月可减重约 1.2 kg"）
- **多模型对比**：支持通义千问 VL、智谱 GLM-4V、豆包 Vision 三大视觉模型
- **文生图效果预览**：通过通义万相生成改造后健康菜品效果图

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/NutriVision.git
cd NutriVision
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

复制 `.env.example` 为 `.env`，填入你的 API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxx    # 阿里云 DashScope（必需）
ZHIPU_API_KEY=xxxxxxxxxxxxx           # 智谱 AI（可选）
DOUBAO_API_KEY=xxxxxxxxxxxxx          # 火山引擎豆包（可选）
```

### 4. 启动应用

```bash
streamlit run app.py
```

## 🏗️ 系统架构

| 模块 | 文件 | 功能 | 使用模型 |
|------|------|------|----------|
| 配置中心 | `config.py` | API 端点、模型注册、缓存路径、系统限制 | — |
| 公共工具 | `modules/common.py` | API Key 加载、JSON 解析、重试机制、缓存 | — |
| Module A | `modules/vision_analyzer.py` | VLM 视觉分析（菜名/食材+克重/烹饪方式/热量/风险标签） | qwen-vl-plus / glm-4v / doubao |
| 营养数据库 | `modules/nutrition_db.py` | 成分表法核算热量明细、BMI/TDEE 计算 | — |
| Module B | `modules/health_advisor.py` | 结合健康目标与用户档案生成改造方案 + 预期效果 | qwen-plus |
| Module C | `modules/image_generator.py` | 文生图生成"健康版"菜品效果图 | wanx-v1（通义万相） |
| 前端 | `app.py` | Streamlit 交互 Demo | — |
| 日志配置 | `logging_config.py` | 统一日志初始化 | — |

## 📁 项目结构

```
NutriVision/
├── app.py                      # Streamlit 主应用
├── config.py                   # 集中配置（API端点、模型、限制等）
├── logging_config.py           # 日志配置
├── requirements.txt            # Python 依赖
├── .env.example                # API Key 模板
├── .gitignore                  # Git 忽略规则
├── LICENSE                     # MIT 许可证
├── README.md                   # 本文件
├── modules/
│   ├── __init__.py
│   ├── common.py               # 公共工具函数
│   ├── vision_analyzer.py      # 多模型视觉分析
│   ├── nutrition_db.py         # 营养数据库
│   ├── health_advisor.py       # 健康建议生成
│   └── image_generator.py      # 文生图
├── filter_food.py              # 数据集食物筛选
├── annotate_dataset.py         # 数据集标注
├── prompt_experiment.py         # Prompt 对比实验
└── output/                     # 缓存与输出目录
```

## 🔧 配置说明

所有配置集中在 `config.py` 中：

- **API_ENDPOINTS**：各模型 API 端点地址
- **MODELS**：模型注册表（provider、type、endpoint_id）
- **CACHE_FILES**：缓存文件路径
- **LIMITS**：系统限制（重试次数、超时时间等）

## 📄 License

MIT License. See [LICENSE](LICENSE).


