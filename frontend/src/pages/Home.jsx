import { Link } from 'react-router-dom'

const features = [
  { icon: '🔍', title: '多模型视觉识别', desc: '通义千问 / 智谱 GLM-4V / 豆包，四款视觉模型可选，食材与克重级识别，一键对比。' },
  { icon: '🥗', title: '成分级热量核算', desc: '658 种食材营养库 + 成分表法，逐项核算热量明细，可追溯、可解释。' },
  { icon: '💡', title: '个性化改造方案', desc: '结合健康目标与个人档案（BMI / TDEE），生成步骤化改造与量化预期效果。' },
  { icon: '🔄', title: '食材替换建议', desc: 'AI 逐项分析，给出更健康的替代食材与替换理由。' },
  { icon: '📊', title: '营养仪表盘', desc: '食材热量占比、多模型对比、每日摄入占比，一目了然的可视化。' },
  { icon: '🎯', title: '每日目标与记录', desc: '按身体数据智能推荐热量缺口 / 盈余，记录每一餐，坚持看得见。' },
  { icon: '💧', title: '饮水打卡', desc: '记录每日饮水量，连续打卡日历，打卡后鼓励话语让你更有动力。' },
  { icon: '⚖️', title: '膳食动态补偿', desc: '午餐吃多了？AI 自动建议晚餐怎么吃，帮你拉回每日目标。' },
]

const steps = [
  { n: '01', title: '上传照片', desc: '上传一张食物图片，支持拖拽' },
  { n: '02', title: 'AI 识别', desc: 'VLM 识别菜名、食材与克重' },
  { n: '03', title: '健康改造', desc: '营养核算 + 生成个性化方案' },
  { n: '04', title: '持续记录', desc: '记入每日计划，追踪你的目标' },
]

export default function Home() {
  return (
    <div>
      {/* Hero：奶油底大留白，Zoe 式克制排版 */}
      <section className="relative overflow-hidden">
        <div className="mx-auto max-w-6xl px-6 pt-24 pb-20 sm:pt-32 sm:pb-28 text-center">
          <div className="fade-up inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium text-brand-600 bg-brand-50 border border-brand-100">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-500" />
            AI 健康饮食改造师
          </div>
          <h1 className="fade-up-1 mt-8 text-5xl sm:text-7xl font-black leading-[1.05] tracking-tight text-ink-900">
            让每一餐
            <br />
            都更<span className="text-gradient">健康一点</span>
          </h1>
          <p className="fade-up-2 mt-7 max-w-2xl mx-auto text-lg text-ink-500 leading-relaxed">
            上传食物照片，AI 识别食材与克重，核算热量，结合你的身体数据生成个性化健康改造方案。
          </p>
          <div className="fade-up-3 mt-11 flex flex-wrap items-center justify-center gap-4">
            <Link to="/analyze"
              className="px-9 py-4 rounded-full text-base font-semibold text-white bg-brand-600 hover:bg-brand-500 hover:-translate-y-0.5 transition-all shadow-lg shadow-brand-900/10">
              立即体验
            </Link>
            <Link to="/about"
              className="px-9 py-4 rounded-full text-base font-semibold text-ink-700 bg-white border border-ink-200 hover:border-ink-300 hover:bg-ink-100 transition-all">
              了解更多
            </Link>
          </div>
        </div>
      </section>

      {/* 数据条：轻边框克制呈现 */}
      <section className="mx-auto max-w-6xl px-6">
        <div className="card-soft grid grid-cols-2 sm:grid-cols-5 divide-x divide-ink-200/60 overflow-hidden">
          {[['658', '营养库食材'], ['411', '食物图片'], ['4', '视觉模型'], ['3', '模型平台'], ['100%', 'JSON 合规率']].map(([num, label]) => (
            <div key={label} className="p-8 text-center">
              <div className="text-3xl font-black text-brand-600">{num}</div>
              <div className="mt-1.5 text-sm text-ink-500">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* 核心功能 */}
      <section className="mx-auto max-w-6xl px-6 py-24">
        <div className="max-w-2xl mb-16">
          <div className="text-sm font-semibold text-accent-600 tracking-[0.2em] uppercase">Features</div>
          <h2 className="mt-3 text-4xl font-black tracking-tight text-ink-900">核心功能</h2>
          <p className="mt-4 text-ink-500 leading-relaxed">从"识别"到"改造"再到"记录"，一站式管理你的饮食健康。</p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f) => (
            <div key={f.title}
              className="group card-soft p-8 hover:-translate-y-1 hover:shadow-lg hover:shadow-brand-900/5 transition-all duration-300">
              <div className="w-11 h-11 rounded-xl bg-brand-50 flex items-center justify-center text-xl group-hover:scale-110 transition-transform">
                {f.icon}
              </div>
              <h3 className="mt-5 text-lg font-bold text-ink-900">{f.title}</h3>
              <p className="mt-2.5 text-sm leading-relaxed text-ink-500">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 工作原理 */}
      <section className="border-y border-ink-200/70 bg-white/60">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="max-w-2xl mb-16">
            <div className="text-sm font-semibold text-accent-600 tracking-[0.2em] uppercase">How it works</div>
            <h2 className="mt-3 text-4xl font-black tracking-tight text-ink-900">工作原理</h2>
            <p className="mt-4 text-ink-500">四步完成"从照片到健康方案"。</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {steps.map((s) => (
              <div key={s.n} className="card-soft p-8 hover:shadow-lg transition-shadow">
                <div className="text-5xl font-black text-brand-200 tracking-tight">{s.n}</div>
                <h3 className="mt-6 text-lg font-bold text-ink-900">{s.title}</h3>
                <p className="mt-2 text-sm text-ink-500">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA：陶土橙强调 */}
      <section className="mx-auto max-w-6xl px-6 py-24">
        <div className="relative overflow-hidden rounded-3xl bg-brand-800 px-8 py-20 text-center">
          <div className="absolute inset-0 opacity-10" style={{
            backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,.6) 1px, transparent 0)',
            backgroundSize: '24px 24px',
          }} />
          <div className="relative">
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-white">准备好让每顿饭更健康了吗？</h2>
            <p className="mt-4 text-white/70">上传一张照片，立即获取你的个性化健康改造方案</p>
            <div className="mt-9">
              <Link to="/analyze"
                className="inline-block px-10 py-4 rounded-full text-base font-bold text-white bg-accent-500 hover:bg-accent-400 hover:-translate-y-0.5 transition-all shadow-xl shadow-black/20">
                开始分析 →
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
