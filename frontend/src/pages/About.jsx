const stack = [
  ['前端', 'React 18 · Vite · Tailwind CSS'],
  ['后端', 'FastAPI · SQLAlchemy · SQLite'],
  ['视觉模型', 'Qwen-VL-Plus / Max · GLM-4V · Doubao-Seed-2.0'],
  ['文本模型', 'Qwen-Plus'],
  ['文生图', '通义万相（云端） · Stable Diffusion + ControlNet（本地 GPU）'],
  ['营养数据', '658 种食材成分库（中国食物成分表 / USDA 口径）'],
]

const modules = [
  ['Module A', 'VLM 视觉分析：菜名 / 食材 / 克重 / 烹饪方式 / 风险标签'],
  ['营养数据库', '658 种食材成分表法热量核算、BMI / TDEE'],
  ['Module B', '健康改造方案 + 预期效果 + 食材替换建议'],
  ['Module C', '文生图：通义万相 / ControlNet 构图保持'],
]

export default function About() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <div className="text-center mb-12">
        <div className="text-5xl">🥗</div>
        <h1 className="mt-4 text-3xl sm:text-4xl font-black text-ink-800">关于 NutriVision</h1>
        <p className="mt-3 text-ink-500">AI 健康饮食改造师 · 前后端分离的完整系统</p>
      </div>

      <section className="rounded-2xl bg-white border border-ink-200/70 p-8 shadow-sm mb-8">
        <h2 className="text-xl font-bold text-ink-800 mb-3">🎯 项目简介</h2>
        <p className="leading-relaxed text-ink-600">
          基于视觉语言大模型（VLM）的个性化健康饮食方案系统：上传食物照片 →
          自动识别食材与克重 → 营养库核算热量 → 结合用户健康目标与个人档案
          生成个性化改造方案 → 生成"健康版"菜品效果图。支持多账号、每个用户独立保存分析历史。
        </p>
      </section>

      <section className="rounded-2xl bg-white border border-ink-200/70 p-8 shadow-sm mb-8">
        <h2 className="text-xl font-bold text-ink-800 mb-4">🏗️ 技术栈</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {stack.map(([k, v]) => (
            <div key={k} className="flex gap-3 items-start rounded-xl bg-ink-100 p-4">
              <span className="shrink-0 px-2.5 py-1 rounded-lg bg-brand-600 text-white text-xs font-bold">{k}</span>
              <span className="text-sm text-ink-600">{v}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl bg-white border border-ink-200/70 p-8 shadow-sm mb-8">
        <h2 className="text-xl font-bold text-ink-800 mb-4">📁 模块说明</h2>
        <div className="space-y-3">
          {modules.map(([k, v]) => (
            <div key={k} className="flex gap-3 items-start rounded-xl bg-ink-100 p-4">
              <span className="shrink-0 px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 text-xs font-bold">{k}</span>
              <span className="text-sm text-ink-600">{v}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl bg-white border border-ink-200/70 p-8 shadow-sm">
        <h2 className="text-xl font-bold text-ink-800 mb-3">🧪 跨模型实验</h2>
        <p className="text-ink-600">
          20 张食物图 × 4 视觉模型（V5 Prompt），全部模型 JSON 合规率 100%。
          详细对比数据见 <code className="px-1.5 py-0.5 rounded bg-ink-100 text-brand-700">pe_results/cross_model/</code>。
        </p>
      </section>
    </div>
  )
}
