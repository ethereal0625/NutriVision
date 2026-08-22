import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'

const CAT_COLORS = {
  热量误区: 'bg-blue-50 text-blue-600 border-blue-200',
  减肥误区: 'bg-orange-50 text-orange-600 border-orange-200',
  饮食误区: 'bg-amber-50 text-amber-600 border-amber-200',
  营养误区: 'bg-brand-50 text-brand-700 border-brand-200',
  运动误区: 'bg-emerald-50 text-emerald-600 border-emerald-200',
  生活误区: 'bg-violet-50 text-violet-600 border-violet-200',
}

export default function Tips() {
  const [data, setData] = useState(null)
  const [category, setCategory] = useState('全部')
  const [query, setQuery] = useState('')
  const [openId, setOpenId] = useState(0)

  useEffect(() => {
    api.getTips().then(setData).catch(() => setData({ tips: [] }))
  }, [])

  const list = useMemo(() => {
    if (!data) return []
    let arr = data.tips
    if (category !== '全部') arr = arr.filter((t) => t.category === category)
    if (query.trim()) arr = arr.filter((t) => (t.myth + t.truth).includes(query.trim()))
    return arr
  }, [data, category, query])

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <div className="text-center mb-10">
        <div className="text-5xl">🧠</div>
        <h1 className="mt-4 text-3xl sm:text-4xl font-black text-ink-800">健康科普</h1>
        <p className="mt-3 text-ink-500">这些常见的"健康常识"，其实大多是误区</p>
      </div>

      {/* 分类 + 搜索 */}
      <div className="flex flex-wrap items-center justify-center gap-2 mb-6">
        {['全部', ...(data?.categories || [])].map((c) => (
          <button key={c} onClick={() => setCategory(c)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition ${category === c ? 'bg-brand-600 text-white shadow-md shadow-brand-600/25' : 'bg-white border border-ink-200 text-ink-600 hover:bg-ink-100'}`}>
            {c}
          </button>
        ))}
      </div>
      <div className="max-w-md mx-auto mb-8">
        <input value={query} onChange={(e) => setQuery(e.target.value)}
          className="w-full px-4 py-3 rounded-xl border border-ink-200 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition"
          placeholder="🔍 搜索误区，如：喝水、果汁、胆固醇..." />
      </div>

      {/* 误区卡片 */}
      <div className="space-y-4">
        {list.map((t, i) => {
          const open = openId === i
          return (
            <div key={i} className="rounded-2xl bg-white border border-ink-200/70 shadow-sm overflow-hidden">
              <button onClick={() => setOpenId(open ? -1 : i)}
                className="w-full text-left p-5 flex items-start gap-4 hover:bg-ink-100/40 transition">
                <span className="shrink-0 w-9 h-9 rounded-xl bg-red-50 text-red-500 flex items-center justify-center text-lg">❌</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`px-2 py-0.5 rounded-full border text-xs font-medium ${CAT_COLORS[t.category] || 'bg-ink-100 text-ink-600 border-ink-200'}`}>{t.category}</span>
                    <span className="text-xs text-ink-400">误区</span>
                  </div>
                  <div className="mt-1.5 font-bold text-ink-800">{t.myth}</div>
                </div>
                <span className={`shrink-0 text-ink-300 transition-transform ${open ? 'rotate-180' : ''}`}>▾</span>
              </button>
              {open && (
                <div className="px-5 pb-5 pl-[68px] fade-up">
                  <div className="flex items-start gap-3 rounded-xl bg-brand-50 border border-brand-100 p-4">
                    <span className="shrink-0 w-7 h-7 rounded-full bg-brand-600 text-white flex items-center justify-center text-sm">✅</span>
                    <div>
                      <div className="text-xs font-semibold text-brand-600 mb-1">真相</div>
                      <p className="text-sm leading-relaxed text-ink-700">{t.truth}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
        {list.length === 0 && <div className="text-center py-16 text-ink-400">没有找到相关误区</div>}
      </div>
    </div>
  )
}

