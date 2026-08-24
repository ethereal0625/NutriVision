import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, getToken } from '../api.js'

const QUICK = [
  { to: '/analyze', icon: '📸', label: '食物分析', desc: '拍照识别营养' },
  { to: '/plan', icon: '🎯', label: '每日计划', desc: '热量目标安排' },
  { to: '/water', icon: '⏰', label: '提醒', desc: '喝水 / 吃药' },
  { to: '/history', icon: '📅', label: '饮食记录', desc: '历史与统计' },
  { to: '/badges', icon: '🏆', label: '成就', desc: '打卡里程碑' },
  { to: '/tips', icon: '💡', label: '健康科普', desc: '营养小知识' },
]

export default function Home() {
  const nav = useNavigate()
  const token = getToken()
  const [day, setDay] = useState(null)
  const [water, setWater] = useState(null)
  const [recent, setRecent] = useState([])

  useEffect(() => {
    if (!token) return
    api.getDay().then(setDay).catch(() => {})
    api.getWaterToday().then(setWater).catch(() => {})
    api.history().then((list) => setRecent((list || []).slice(0, 5))).catch(() => {})
  }, [token])

  if (!token) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-20 sm:py-28 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium text-brand-600 bg-brand-50 border border-brand-100">
          <span className="w-1.5 h-1.5 rounded-full bg-accent-500" />
          AI 健康饮食助手
        </div>
        <h1 className="mt-7 text-4xl sm:text-5xl font-black tracking-tight text-ink-900">拍一拍，吃得健康一点</h1>
        <p className="mt-5 max-w-xl mx-auto text-ink-500 leading-relaxed">
          食物识别、热量核算、健康改造，还有喝水吃药提醒，一站式管理你的日常健康。
        </p>
        <div className="mt-9 flex flex-wrap items-center justify-center gap-4">
          <button onClick={() => nav('/register')} className="px-9 py-4 rounded-full text-base font-semibold text-white bg-brand-600 hover:bg-brand-500 transition-all shadow-lg shadow-brand-900/10">
            免费注册
          </button>
          <Link to="/login" className="px-9 py-4 rounded-full text-base font-semibold text-ink-700 bg-white border border-ink-200 hover:border-ink-300 transition-all">
            登录
          </Link>
        </div>
      </div>
    )
  }

  const now = new Date()
  const hour = now.getHours()
  const greet = hour < 6 ? '夜深了' : hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'
  const percent = day?.percent ?? 0
  const waterPct = water?.percent ?? 0

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 py-6 pb-16 md:pb-6">
      <div className="mb-5">
        <div className="text-sm text-ink-400">{now.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })}</div>
        <h1 className="mt-1 text-2xl sm:text-3xl font-black text-ink-800">{greet}，今天也好好吃饭 🥗</h1>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-6">
        <Link to="/plan" className="rounded-2xl bg-gradient-to-br from-brand-600 to-brand-500 text-white p-5 shadow-md shadow-brand-500/20">
          <div className="text-xs opacity-80 mb-1">今日热量</div>
          <div className="text-2xl font-black">{day ? day.total_calories : '--'}<span className="text-sm font-normal opacity-80 ml-1">/ {day ? day.target_calories : '--'} kcal</span></div>
          <div className="mt-3 h-2 bg-white/25 rounded-full overflow-hidden">
            <div className="h-full bg-white rounded-full transition-all duration-500" style={{ width: `${Math.min(percent, 100)}%` }} />
          </div>
        </Link>
        <Link to="/water" className="rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 text-white p-5 shadow-md shadow-blue-500/20">
          <div className="text-xs opacity-80 mb-1">今日饮水</div>
          <div className="text-2xl font-black">{water ? water.total : '--'}<span className="text-sm font-normal opacity-80 ml-1">/ {water ? water.goal : '--'} ml</span></div>
          <div className="mt-3 h-2 bg-white/25 rounded-full overflow-hidden">
            <div className="h-full bg-white rounded-full transition-all duration-500" style={{ width: `${Math.min(waterPct, 100)}%` }} />
          </div>
        </Link>
      </div>

      <h2 className="text-sm font-bold text-ink-600 mb-3">快捷入口</h2>
      <div className="grid grid-cols-3 gap-3 mb-7">
        {QUICK.map((q) => (
          <Link key={q.to} to={q.to} className="card-soft p-4 text-center hover:-translate-y-0.5 hover:shadow-md transition-all">
            <div className="text-2xl">{q.icon}</div>
            <div className="mt-2 text-sm font-bold text-ink-800">{q.label}</div>
            <div className="mt-1 text-[11px] leading-tight text-ink-400">{q.desc}</div>
          </Link>
        ))}
      </div>

      <div className="card-soft p-5 mb-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-ink-600">今日饮食</h2>
          <Link to="/history" className="text-xs text-brand-600 font-medium">全部记录 →</Link>
        </div>
        {day?.meals?.length ? (
          <div className="space-y-2">
            {day.meals.map((m) => (
              <div key={m.id} className="flex items-center justify-between py-2 border-b border-ink-100 last:border-0">
                <div>
                  <div className="text-sm font-semibold text-ink-800">{m.dish_name}</div>
                  <div className="text-xs text-ink-400">{m.meal_type} · {m.time}</div>
                </div>
                <div className="text-sm font-bold text-ink-700">{m.calories} kcal</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-4 text-center text-sm text-ink-400">
            今天还没记录，拍张照片开始吧
            <Link to="/analyze" className="block mt-2 text-brand-600 font-semibold">去分析 →</Link>
          </div>
        )}
      </div>

      {recent.length > 0 && (
        <div className="card-soft p-5">
          <h2 className="text-sm font-bold text-ink-600 mb-3">最近记录</h2>
          <div className="space-y-2">
            {recent.map((item) => (
              <div key={item.id} className="flex items-center justify-between py-2 border-b border-ink-100 last:border-0">
                <div>
                  <div className="text-sm font-semibold text-ink-800">{item.dish_name}</div>
                  <div className="text-xs text-ink-400">{item.date} · {item.meal_type}</div>
                </div>
                <div className="text-sm font-bold text-ink-700">{item.calories} kcal</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
