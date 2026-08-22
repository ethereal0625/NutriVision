import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, getToken } from '../api.js'
import { Bar, CartesianGrid, Cell, ComposedChart, Legend, Line, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const MEAL_EMOJI = { 早餐: '🌅', 午餐: '☀️', 晚餐: '🌙', 加餐: '🍎', 饮品: '🥤' }
const MEAL_TYPES = ['早餐', '午餐', '晚餐', '加餐', '饮品']
const GOALS = ['减脂', '控糖', '增肌', '均衡饮食']

export default function Plan() {
  const nav = useNavigate()
  const [token] = useState(getToken())
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [day, setDay] = useState(null)
  const [stats, setStats] = useState(null)
  const [statsDays, setStatsDays] = useState(7)
  const [target, setTarget] = useState(2000)
  const [goal, setGoal] = useState('均衡饮食')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [dailyTip, setDailyTip] = useState(null)
  const [reminder, setReminder] = useState(false)
  const [proteinGoal, setProteinGoal] = useState(null)
  const [carbGoal, setCarbGoal] = useState(null)
  const [fatGoal, setFatGoal] = useState(null)
  const [reporting, setReporting] = useState(false)
  // 个人档案 + 热量目标模式
  const [height, setHeight] = useState('')
  const [weight, setWeight] = useState('')
  const [age, setAge] = useState('')
  const [gender, setGender] = useState('男')
  const [activity, setActivity] = useState('轻度')
  const [calorieMode, setCalorieMode] = useState('auto')
  const [adjustment, setAdjustment] = useState(0)
  const [tdee, setTdee] = useState(null)
  const [recommendedAdj, setRecommendedAdj] = useState(0)
  const [targetNote, setTargetNote] = useState('')

  // 手动添加 / 编辑
  const [showAdd, setShowAdd] = useState(false)
  const [editId, setEditId] = useState(null)
  const [form, setForm] = useState({ dish_name: '', calories: 300, meal_type: '午餐' })

  const load = async () => {
    setLoading(true); setError('')
    try {
      const [p, d, s] = await Promise.all([api.getPlan(), api.getDay(date), api.getStats(statsDays)])
      api.getTips().then((td) => { if (td?.tips?.length) setDailyTip(td.tips[Math.floor(Math.random() * td.tips.length)]) }).catch(() => {})
      setTarget(p.target_calories); setGoal(p.goal); setReminder(!!p.reminder_enabled);
      setProteinGoal(p.protein_goal ?? null); setCarbGoal(p.carb_goal ?? null); setFatGoal(p.fat_goal ?? null);
      setHeight(p.height_cm ?? ''); setWeight(p.weight_kg ?? ''); setAge(p.age ?? '');
      setGender(p.gender || '男'); setActivity(p.activity || '轻度');
      setCalorieMode(p.calorie_mode || 'auto'); setAdjustment(p.adjustment || 0);
      setTdee(p.tdee ?? null); setRecommendedAdj(p.recommended_adjustment ?? 0); setTargetNote(p.target_note || '');
      setDay(d); setStats(s)
    } catch (e) {
      if (e.message !== '登录已过期') setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!token) { nav('/login'); return }
    load()
  }, [token, date, statsDays])

  const savePlan = async () => {
    setSaved(false)
    try {
      const profile = (height && weight && age) ? { height_cm: Number(height), weight_kg: Number(weight), age: Number(age), gender, activity } : {}
      const p = await api.updatePlan(Number(target), goal, reminder, Number(proteinGoal) || null, Number(carbGoal) || null, Number(fatGoal) || null, profile, calorieMode, Number(adjustment) || 0)
      setTarget(p.target_calories); setGoal(p.goal);
      setProteinGoal(p.protein_goal ?? null); setCarbGoal(p.carb_goal ?? null); setFatGoal(p.fat_goal ?? null);
      setTdee(p.tdee ?? null); setRecommendedAdj(p.recommended_adjustment ?? 0); setTargetNote(p.target_note || '');
      setSaved(true); load()
    } catch (e) { setError(e.message) }
  }

  const addMeal = async () => {
    if (!form.dish_name.trim()) return
    try {
      await api.saveHistory({
        dish_name: form.dish_name.trim(), calories: Number(form.calories) || 0,
        models: '', goal, result_json: '{}', date, meal_type: form.meal_type,
      })
      setShowAdd(false); setForm({ dish_name: '', calories: 300, meal_type: '午餐' })
      load()
    } catch (e) { setError(e.message) }
  }

  const saveEdit = async (id) => {
    const orig = day.meals.find((m) => m.id === id)
    try {
      await api.updateHistory(id, {
        dish_name: form.dish_name, calories: Number(form.calories) || 0,
        models: orig.models || '', goal, result_json: '{}', date, meal_type: form.meal_type,
      })
      setEditId(null); load()
    } catch (e) { setError(e.message) }
  }

  const startEdit = (m) => { setEditId(m.id); setForm({ dish_name: m.dish_name, calories: m.calories, meal_type: m.meal_type }) }

  const removeMeal = async (id) => { await api.deleteHistory(id); load() }

  const today = new Date().toISOString().slice(0, 10)
  const isToday = date === today
  const pct = Math.min(day?.percent || 0, 100)
  const shiftDay = (delta) => {
    const d = new Date(date + 'T00:00:00'); d.setDate(d.getDate() + delta)
    setDate(d.toISOString().slice(0, 10))
  }

  const inputCls = 'w-full px-3 py-2 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition bg-white text-sm'

  if (loading) return <div className="py-24 text-center text-ink-400">加载中...</div>

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

  const chartData = stats?.daily || []

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-black text-ink-800">📅 每日计划</h1>
          <p className="mt-1 text-ink-500">设定每日目标，记录每一餐，坚持看得见</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          <button onClick={exportReport} disabled={reporting}
            className="px-4 py-2 rounded-xl text-sm font-semibold text-white bg-brand-600 hover:bg-brand-500 hover:shadow-lg hover:shadow-brand-900/15 transition-all disabled:opacity-60">
            {reporting ? '生成中...' : '📊 导出周报'}
          </button>
          <button onClick={() => shiftDay(-1)} className="w-9 h-9 rounded-full bg-white border border-ink-200 hover:bg-ink-100 transition">‹</button>
          <span className="px-3 py-1.5 rounded-xl bg-white border border-ink-200 text-sm font-semibold">{isToday ? '今天' : date}</span>
          <button onClick={() => shiftDay(1)} disabled={isToday} className="w-9 h-9 rounded-full bg-white border border-ink-200 hover:bg-ink-100 disabled:opacity-40 transition">›</button>
        </div>
      </div>

      {error && <div className="mb-6 px-4 py-3 rounded-xl bg-red-50 text-red-600 text-sm">{error}</div>}

      {reminder && isToday && (day?.total_calories || 0) < (day?.target_calories || target) && new Date().getHours() >= 18 && (
        <div className="mb-6 rounded-2xl bg-brand-50 border border-brand-200 px-5 py-4 flex flex-wrap items-center justify-between gap-3 fade-up">
          <div className="text-sm text-brand-800">
            <span className="font-bold">🔔 今日打卡提醒</span>
            <span className="ml-2">今天已摄入 {day.total_calories} kcal，还可吃 {day.remaining} kcal 达标，记得记录你的晚餐~</span>
          </div>
          <Link to="/analyze" className="px-4 py-2 rounded-xl text-sm font-semibold text-white bg-brand-600 hover:bg-brand-500 transition">去记录</Link>
        </div>
      )}

      {/* 今日热量提示：基于目标 + 已摄入 */}
      {day && (
        <div className="mb-6 rounded-2xl bg-white border border-ink-200/70 shadow-sm p-5 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-sm font-bold text-ink-800">
              {goal === '减脂' ? '🔥 今日减脂目标' : goal === '增肌' ? '💪 今日增肌目标' : goal === '控糖' ? '🍬 今日控糖目标' : '⚖️ 今日均衡目标'}
            </div>
            <div className="mt-1 text-sm text-ink-500">
              {tdee ? (
                <>你的每日消耗约 <b className="text-ink-700">{tdee} kcal</b>
                  {calorieMode === 'auto'
                    ? <>，按「{goal}」{recommendedAdj > 0 ? `盈余 +${recommendedAdj}` : recommendedAdj < 0 ? `缺口 ${recommendedAdj}` : '维持平衡'} 推荐</>
                    : <>，按你设定的{adjustment > 0 ? `盈余 +${adjustment}` : adjustment < 0 ? `缺口 ${adjustment}` : '维持平衡'}</>}
                </>
              ) : '填写个人档案后可自动按你的身体情况推荐'}
            </div>
            {targetNote && <div className="mt-0.5 text-xs text-ink-400">{targetNote}</div>}
          </div>
          <div className="text-right">
            <div className={`text-2xl font-black ${(day.remaining || 0) > 0 ? 'text-brand-600' : 'text-orange-500'}`}>
              {(day.remaining || 0) > 0 ? `还可吃 ${day.remaining} kcal` : `已超出 ${-day.remaining} kcal`}
            </div>
            <div className="text-xs text-ink-400 mt-1">今日已摄入 {day.total_calories} / 目标 {day.target_calories} kcal</div>
          </div>
        </div>
      )}

      {/* 今日进度 */}
      <div className="rounded-3xl bg-white border border-ink-200/70 shadow-sm p-7 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-sm font-semibold text-brand-600">每日目标 · {goal}</div>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-4xl font-black text-ink-800">{day?.total_calories || 0}</span>
              <span className="text-ink-400">/ {day?.target_calories || target} kcal</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-black text-ink-800">{day?.percent || 0}%</div>
            <div className="text-xs text-ink-400 mt-1">目标完成度</div>
          </div>
        </div>
        <div className="mt-4 h-3.5 rounded-full bg-ink-100 overflow-hidden">
          <div className={`h-full rounded-full transition-all duration-700 ${pct > 100 ? 'bg-gradient-to-r from-orange-400 to-red-400' : 'bg-gradient-to-r from-brand-500 to-brand-400'}`} style={{ width: `${pct}%` }} />
        </div>
        {/* 宏量营养素进度 */}
        <div className="mt-5 grid sm:grid-cols-3 gap-3">
          {[
            { key: 'protein', label: '🥩 蛋白质', color: 'bg-red-400', text: 'text-red-500', goal: day?.macro_targets?.protein ?? proteinGoal ?? 0 },
            { key: 'carbs', label: '🍚 碳水', color: 'bg-amber-400', text: 'text-amber-600', goal: day?.macro_targets?.carbs ?? carbGoal ?? 0 },
            { key: 'fat', label: '🥑 脂肪', color: 'bg-orange-400', text: 'text-orange-500', goal: day?.macro_targets?.fat ?? fatGoal ?? 0 },
          ].map((m) => {
            const cur = day?.macros?.[m.key] || 0
            const gp = Math.min(cur / (m.goal || 1) * 100, 100)
            return (
              <div key={m.key} className="rounded-xl bg-ink-100/60 p-3">
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-semibold text-ink-600">{m.label}</span>
                  <span className={`font-black ${m.text}`}>{Math.round(cur)}<span className="text-ink-400 font-medium">/{Math.round(m.goal)}g</span></span>
                </div>
                <div className="h-2 rounded-full bg-white overflow-hidden">
                  <div className={`h-full ${m.color} transition-all duration-700`} style={{ width: `${gp}%` }} />
                </div>
                <div className="mt-1 text-[10px] text-ink-400">{cur >= m.goal ? '已达标' : `还差 ${Math.max(Math.round(m.goal - cur), 0)}g`}</div>
              </div>
            )
          })}
        </div>
        <p className="mt-2 text-[11px] text-ink-400">宏量目标默认按热量自动推算，AI 分析过的食物才会累计蛋白/碳水/脂肪</p>
        <div className="mt-6 border-t border-ink-100 pt-5 space-y-5">
          {/* 个人档案（来自个人中心） */}
          <div>
            <div className="text-sm font-bold text-ink-800 mb-2">👤 我的档案</div>
            {height && weight && age ? (
              <div className="rounded-xl bg-brand-50/60 border border-brand-100 p-4 flex flex-wrap items-center justify-between gap-3">
                <div className="text-sm text-ink-700">
                  {height}cm · {weight}kg · {age}岁 · {gender} · 活动量{activity}
                  {tdee && <span className="ml-2 text-brand-600">（每日消耗约 <b>{tdee} kcal</b>）</span>}
                </div>
                <Link to="/profile" className="text-xs font-semibold text-brand-600 hover:text-brand-700">✏️ 修改档案 →</Link>
              </div>
            ) : (
              <div className="rounded-xl bg-ink-100/60 border border-ink-200 p-4 flex flex-wrap items-center justify-between gap-3">
                <div className="text-sm text-ink-600">📝 尚未填写身体档案，当前使用默认目标</div>
                <Link to="/profile" className="text-xs font-semibold text-brand-600 hover:text-brand-700">去个人中心填写 →</Link>
              </div>
            )}
          </div>

          {/* 热量目标模式 */}
          <div>
            <div className="text-sm font-bold text-ink-800 mb-2">🎯 每日热量目标</div>
            <div className="flex flex-wrap gap-2 mb-3">
              <button type="button" onClick={() => setCalorieMode('auto')}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${calorieMode === 'auto' ? 'bg-brand-600 text-white shadow' : 'bg-ink-100 text-ink-600 hover:bg-ink-200'}`}>
                ✨ 智能推荐（按目标类型）
              </button>
              <button type="button" onClick={() => setCalorieMode('manual')}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${calorieMode === 'manual' ? 'bg-brand-600 text-white shadow' : 'bg-ink-100 text-ink-600 hover:bg-ink-200'}`}>
                🎛️ 手动设定缺口/盈余
              </button>
            </div>

            {calorieMode === 'auto' ? (
              <div className="rounded-xl bg-brand-50/60 border border-brand-100 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm text-ink-700">
                    目标类型
                    <select value={goal} onChange={(e) => setGoal(e.target.value)} className="ml-2 px-2.5 py-1.5 rounded-lg border border-ink-200 bg-white text-sm">
                      {GOALS.map((g) => <option key={g}>{g}</option>)}
                    </select>
                  </div>
                  <div className="text-sm font-semibold text-brand-700">
                    {goal === '减脂' && '推荐每日缺口 300~500 kcal（每周约减 0.5~1 kg）'}
                    {goal === '增肌' && '推荐每日盈余 300~500 kcal'}
                    {goal === '控糖' && '推荐维持热量平衡，碳水 45~60% 且选低 GI'}
                    {goal === '均衡饮食' && '推荐维持热量平衡，均衡三餐'}
                  </div>
                </div>
                {!tdee && <div className="mt-2 text-xs text-orange-500">⚠️ 未填身体数据时使用默认目标 {target} kcal，填写后可自动推荐</div>}
              </div>
            ) : (
              <div className="rounded-xl bg-ink-100/60 border border-ink-200 p-4">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="text-sm text-ink-700">每日热量调整</div>
                  <div className="flex items-center gap-2">
                    <button type="button" onClick={() => setAdjustment(Math.max(-1000, Number(adjustment) - 50))} className="w-8 h-8 rounded-lg bg-white border border-ink-200 hover:bg-ink-100">−</button>
                    <input type="number" value={adjustment} onChange={(e) => setAdjustment(Number(e.target.value) || 0)} className="w-24 px-2 py-1.5 text-center rounded-lg border border-ink-200 bg-white" />
                    <button type="button" onClick={() => setAdjustment(Math.min(1000, Number(adjustment) + 50))} className="w-8 h-8 rounded-lg bg-white border border-ink-200 hover:bg-ink-100">＋</button>
                  </div>
                  <span className="text-xs text-ink-500">
                    {Number(adjustment) > 0 ? `每日盈余 +${adjustment} kcal` : Number(adjustment) < 0 ? `每日缺口 ${adjustment} kcal` : '维持平衡（0）'}
                  </span>
                </div>
                <div className="mt-2 text-[11px] text-ink-400">正数 = 增肌盈余，负数 = 减脂缺口。系统会按安全下限（女 1200 / 男 1500 kcal）兜底。</div>
              </div>
            )}

            <div className="mt-3 flex flex-wrap items-end gap-3">
              <div>
                <label className="block text-xs text-ink-500 mb-1">每日热量目标 (kcal)</label>
                <input type="number" value={target} onChange={(e) => setTarget(e.target.value)} min={500} max={8000} className="w-32 px-3 py-2 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition" />
              </div>
              <button onClick={savePlan} className="px-5 py-2 rounded-xl font-semibold text-white bg-gradient-to-r from-brand-600 to-brand-500 hover:shadow-lg hover:shadow-brand-500/30 transition-all">保存目标</button>
              <label className="flex items-center gap-2 text-sm text-ink-600 cursor-pointer select-none">
                <input type="checkbox" checked={reminder} onChange={(e) => setReminder(e.target.checked)} className="w-4 h-4 accent-brand-600" />
                🔔 每日打卡提醒
              </label>
              {saved && <span className="text-sm text-brand-600">✅ 已保存</span>}
            </div>
          </div>

          {/* 宏量目标 */}
          <div>
            <div className="text-sm font-bold text-ink-800 mb-2">🥩 宏量营养素目标（可选，留空自动按热量推算）</div>
            <div className="flex flex-wrap items-end gap-3">
              <div>
                <label className="block text-xs text-ink-500 mb-1">蛋白质 (g)</label>
                <input type="number" value={proteinGoal ?? ''} onChange={(e) => setProteinGoal(e.target.value)} placeholder="自动" className="w-28 px-3 py-2 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition" />
              </div>
              <div>
                <label className="block text-xs text-ink-500 mb-1">碳水 (g)</label>
                <input type="number" value={carbGoal ?? ''} onChange={(e) => setCarbGoal(e.target.value)} placeholder="自动" className="w-28 px-3 py-2 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition" />
              </div>
              <div>
                <label className="block text-xs text-ink-500 mb-1">脂肪 (g)</label>
                <input type="number" value={fatGoal ?? ''} onChange={(e) => setFatGoal(e.target.value)} placeholder="自动" className="w-28 px-3 py-2 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition" />
              </div>
              <button type="button" onClick={() => {
                const t = Number(target) || 2000
                setProteinGoal(Math.round(t * 0.2 / 4)); setCarbGoal(Math.round(t * 0.5 / 4)); setFatGoal(Math.round(t * 0.3 / 9))
              }} className="px-3 py-2 rounded-xl text-xs font-semibold text-brand-600 bg-brand-50 hover:bg-brand-100 border border-brand-200 transition">✨ 按比例自动</button>
            </div>
          </div>
        </div>
      </div>

      {/* 当日餐次 */}
      <div className="rounded-3xl bg-white border border-ink-200/70 shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-ink-800">🍽️ {isToday ? '今天吃了什么' : `${date} 的记录`}</h2>
          <button onClick={() => { setShowAdd(!showAdd); setEditId(null) }} className="px-4 py-2 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-brand-600 to-brand-500 hover:shadow-lg transition-all">
            ＋ 手动添加
          </button>
        </div>

        {showAdd && (
          <div className="mb-4 rounded-2xl bg-ink-100/70 p-4 grid sm:grid-cols-[1fr_130px_140px_auto] gap-3 items-end">
            <div>
              <label className="block text-xs text-ink-500 mb-1">菜名 / 食物</label>
              <input className={inputCls} value={form.dish_name} onChange={(e) => setForm({ ...form, dish_name: e.target.value })} placeholder="如：鸡蛋三明治" />
            </div>
            <div>
              <label className="block text-xs text-ink-500 mb-1">热量 (kcal)</label>
              <input type="number" className={inputCls} value={form.calories} onChange={(e) => setForm({ ...form, calories: e.target.value })} />
            </div>
            <div>
              <label className="block text-xs text-ink-500 mb-1">餐次</label>
              <select className={inputCls} value={form.meal_type} onChange={(e) => setForm({ ...form, meal_type: e.target.value })}>
                {MEAL_TYPES.map((m) => <option key={m}>{m}</option>)}
              </select>
            </div>
            <button onClick={addMeal} className="px-4 py-2 rounded-xl font-semibold text-white bg-brand-600 hover:bg-brand-500 transition">添加</button>
          </div>
        )}

        {(!day?.meals || day.meals.length === 0) ? (
          <div className="text-center py-10">
            <div className="text-4xl mb-3">📭</div>
            <p className="text-ink-500">这一天还没有记录</p>
            <Link to="/analyze" className="inline-block mt-4 px-5 py-2.5 rounded-xl font-semibold text-white bg-gradient-to-r from-brand-600 to-brand-500 hover:shadow-lg transition-all">去分析并记入今日 →</Link>
          </div>
        ) : (
          <div className="space-y-3">
            {day.meals.map((m) => (
              <div key={m.id} className="flex items-center gap-4 rounded-2xl bg-ink-100/70 p-4 hover:bg-ink-100 transition">
                {editId === m.id ? (
                  <>
                    <input className={`${inputCls} flex-1`} value={form.dish_name} onChange={(e) => setForm({ ...form, dish_name: e.target.value })} />
                    <input type="number" className={`${inputCls} w-24`} value={form.calories} onChange={(e) => setForm({ ...form, calories: e.target.value })} />
                    <select className={`${inputCls} w-24`} value={form.meal_type} onChange={(e) => setForm({ ...form, meal_type: e.target.value })}>
                      {MEAL_TYPES.map((x) => <option key={x}>{x}</option>)}
                    </select>
                    <button onClick={() => saveEdit(m.id)} className="px-3 py-2 rounded-lg text-xs font-semibold text-white bg-brand-600 hover:bg-brand-500 transition">保存</button>
                    <button onClick={() => setEditId(null)} className="px-3 py-2 rounded-lg text-xs font-semibold text-ink-500 bg-ink-200 hover:bg-ink-300 transition">取消</button>
                  </>
                ) : (
                  <>
                    <div className="text-2xl">{MEAL_EMOJI[m.meal_type] || '🍽️'}</div>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-ink-800 truncate">{m.dish_name}</div>
                      <div className="text-xs text-ink-500 mt-0.5">{m.meal_type || '未分类'} · {m.time}</div>
                    </div>
                    <div className="font-bold text-ink-800">{m.calories} kcal</div>
                    <button onClick={() => startEdit(m)} className="text-ink-300 hover:text-brand-600 transition" title="修改">✏️</button>
                    <button onClick={() => removeMeal(m.id)} className="text-ink-300 hover:text-red-500 transition" title="删除">✕</button>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 摄入统计 */}
      <div className="rounded-3xl bg-white border border-ink-200/70 shadow-sm p-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-bold text-ink-800">📊 摄入统计</h2>
          <div className="flex gap-1">
            {[7, 30].map((n) => (
              <button key={n} onClick={() => setStatsDays(n)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${statsDays === n ? 'bg-brand-600 text-white' : 'bg-ink-100 text-ink-600 hover:bg-ink-200'}`}>
                近{n}天
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3 mb-5">
          <div className="rounded-xl bg-ink-100/70 p-3 text-center">
            <div className="text-xl font-black text-ink-800">{stats?.average ?? '-'}</div>
            <div className="text-xs text-ink-500 mt-0.5">日均摄入 (kcal)</div>
          </div>
          <div className="rounded-xl bg-ink-100/70 p-3 text-center">
            <div className="text-xl font-black text-brand-600">{stats?.target ?? '-'}</div>
            <div className="text-xs text-ink-500 mt-0.5">每日目标 (kcal)</div>
          </div>
          <div className="rounded-xl bg-ink-100/70 p-3 text-center">
            <div className="text-xl font-black text-ink-800">{stats?.within_target_days ?? '-'}/{stats?.days ?? '-'}</div>
            <div className="text-xs text-ink-500 mt-0.5">达标天数</div>
          </div>
        </div>
        <div className="grid sm:grid-cols-2 gap-3 mb-5">
          <div className="rounded-xl bg-ink-100/70 p-4 text-center">
            <div className="text-xs text-ink-500 mb-1">本周日均</div>
            <div className="text-xl font-black text-ink-800">{stats?.this_week_avg ?? '-'} kcal</div>
            <div className={`text-xs mt-1 ${(stats?.this_week_avg || 0) >= (stats?.last_week_avg || 0) ? 'text-red-500' : 'text-brand-600'}`}>
              {(stats?.this_week_avg || 0) >= (stats?.last_week_avg || 0) ? '↑ 较上周' : '↓ 较上周'} {Math.abs((stats?.this_week_avg || 0) - (stats?.last_week_avg || 0))} kcal
            </div>
          </div>
          <div className="rounded-xl bg-ink-100/70 p-4 text-center">
            <div className="text-xs text-ink-500 mb-1">上周日均</div>
            <div className="text-xl font-black text-ink-800">{stats?.last_week_avg ?? '-'} kcal</div>
            <div className="text-xs mt-1 text-ink-400">用于对比本周趋势</div>
          </div>
        </div>

        {(stats?.meal_distribution || []).filter((m) => m.calories > 0).length > 0 && (
          <div className="mb-5 rounded-2xl bg-ink-100/50 p-4">
            <div className="text-sm font-bold text-ink-700 mb-3">🍱 餐次热量占比（近{statsDays}天）</div>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={stats.meal_distribution} dataKey="calories" nameKey="meal_type" innerRadius={50} outerRadius={80} paddingAngle={2}>
                    {['#3d564b', '#50695b', '#c9633a', '#d97b4f', '#aaa298'].map((c, i) => <Cell key={i} fill={c} />)}
                  </Pie>
                  <Tooltip formatter={(v) => [`${v} kcal`, '热量']} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e9f0ec" />
              <XAxis dataKey="date" tickFormatter={(v) => v.slice(5)} tick={{ fontSize: 11, fill: '#64776c' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64776c' }} />
              <Tooltip formatter={(v) => [`${v} kcal`, '摄入']} labelFormatter={(l) => `日期 ${l}`} />
              <Legend />
              <Bar dataKey="total" name="摄入" radius={[6, 6, 0, 0]}>
                {chartData.map((d, i) => (
                  <Cell key={i} fill={d.total > d.target ? '#c9633a' : '#50695b'} />
                ))}
              </Bar>
              <Line type="monotone" dataKey="target" name="目标" stroke="#3d564b" strokeWidth={2} strokeDasharray="6 3" dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <p className="mt-3 text-xs text-ink-400">绿色柱 = 达标内，橙色柱 = 超出目标 · 虚线 = 每日目标线</p>
      </div>

      {/* 今日小知识 */}
      {dailyTip && (
        <div className="mt-6 rounded-2xl bg-brand-50/70 border border-brand-100 p-5">
          <div className="flex items-center gap-2 text-sm font-bold text-brand-700 mb-1.5">
            <span>🧠 今日小知识</span>
            <Link to="/tips" className="text-xs font-medium text-brand-500 hover:text-brand-700">更多健康科普 →</Link>
          </div>
          <div className="text-sm text-ink-600"><span className="font-semibold text-red-500">误区：</span>{dailyTip.myth}</div>
          <div className="mt-1.5 text-sm text-ink-600"><span className="font-semibold text-brand-600">真相：</span>{dailyTip.truth}</div>
        </div>
      )}
    </div>
  )
}
