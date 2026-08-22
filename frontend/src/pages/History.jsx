import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, getToken } from '../api.js'

export default function History() {
  const nav = useNavigate()
  const [token] = useState(getToken())
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) { nav('/login'); return }
    api.history()
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [token])

  const remove = async (id) => {
    await api.deleteHistory(id)
    setItems(items.filter((i) => i.id !== id))
  }

  const [reporting, setReporting] = useState(false)

  const exportReport = async () => {
    setReporting(true)
    try {
      const html = await api.getReport(7)
      const win = window.open('', '_blank')
      if (!win) { setError('浏览器拦截了弹窗，请允许本站打开新窗口'); return }
      win.document.write(html)
      win.document.close()
      setTimeout(() => { try { win.focus(); win.print() } catch {} }, 600)
    } catch (e) { setError(e.message) } finally { setReporting(false) }
  }

  const clearAll = async () => {
    if (!window.confirm('确定清空全部历史记录吗？')) return
    await api.clearHistory()
    setItems([])
  }

  if (loading) return <div className="py-24 text-center text-ink-400">加载中...</div>

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-black text-ink-800">📋 历史记录</h1>
          <p className="mt-1 text-ink-500">你的每一次分析，都在这里</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={exportReport} disabled={reporting}
            className="px-4 py-2 rounded-xl text-sm font-semibold text-white bg-brand-600 hover:bg-brand-500 hover:shadow-lg hover:shadow-brand-900/15 transition-all disabled:opacity-60">
            {reporting ? '生成中...' : '📊 导出周报'}
          </button>
          {items.length > 0 && (
            <button onClick={clearAll} className="px-4 py-2 rounded-xl text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 transition">
              🗑️ 清空全部
            </button>
          )}
        </div>
      </div>

      {error && <div className="mb-6 px-4 py-3 rounded-xl bg-red-50 text-red-600 text-sm">{error}</div>}

      {!loading && items.length === 0 && (
        <div className="text-center py-20">
          <div className="text-5xl mb-4">📭</div>
          <p className="text-ink-500">暂无历史记录</p>
          <Link to="/analyze" className="inline-block mt-5 px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-brand-600 to-brand-500 hover:shadow-lg transition-all">
            去分析第一道菜 →
          </Link>
        </div>
      )}

      <div className="space-y-4">
        {items.map((item) => {
          let parsed = {}
          try { parsed = JSON.parse(item.result_json || '{}') } catch {}
          const primary = parsed.results?.[parsed.primary_model] || {}
          return (
            <div key={item.id} className="rounded-2xl bg-white border border-ink-200/70 shadow-sm p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-bold text-ink-800 truncate">{item.dish_name || primary.dish_name || '未命名'}</h3>
                    <span className="shrink-0 px-2.5 py-0.5 rounded-full bg-brand-50 text-brand-700 text-xs font-semibold">{item.goal}</span>
                  </div>
                  <p className="mt-1.5 text-sm text-ink-500">
                    {new Date(item.created_at).toLocaleString('zh-CN')} · 热量 <span className="font-semibold text-ink-700">{item.calories} kcal</span>
                    {item.models ? ` · 模型 ${item.models.split(',').length} 个` : ''}
                  </p>
                </div>
                <button onClick={() => remove(item.id)} className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-400 hover:text-red-600 hover:bg-red-50 transition">
                  🗑️
                </button>
              </div>
              {primary.visual_description && (
                <p className="mt-3 text-sm text-ink-500 line-clamp-2">{primary.visual_description}</p>
              )}
              {parsed.plan?.healthy_dish_name && (
                <div className="mt-3 px-4 py-2.5 rounded-xl bg-ink-100 text-sm text-ink-600">
                  改造方案 → <span className="font-semibold text-brand-700">{parsed.plan.healthy_dish_name}</span>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
