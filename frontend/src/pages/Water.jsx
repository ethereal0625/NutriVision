import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, getToken } from '../api.js'

const QUICK_AMOUNTS = [100, 200, 250, 350, 500]

export default function Water() {
  const nav = useNavigate()
  const [token, setToken] = useState(getToken())
  const [today, setToday] = useState(null)
  const [customAmount, setCustomAmount] = useState('')
  const [loading, setLoading] = useState(false)
  const [showEncouragement, setShowEncouragement] = useState(false)
  const [encouragement, setEncouragement] = useState('')
  const [goalReached, setGoalReached] = useState(false)
  const [calendar, setCalendar] = useState(null)
  const [calYear, setCalYear] = useState(new Date().getFullYear())
  const [calMonth, setCalMonth] = useState(new Date().getMonth() + 1)

  useEffect(() => { if (!token) nav('/login') }, [token])

  const fetchData = () => {
    api.getWaterToday().then(setToday).catch(() => {})
    api.getWaterCalendar(calYear, calMonth).then(setCalendar).catch(() => {})
  }

  useEffect(() => {
    if (!token) return
    fetchData()
  }, [token, calYear, calMonth])

  const logWater = async (amount) => {
    if (!amount || amount <= 0) return
    setLoading(true)
    try {
      const res = await api.logWater(amount, '')
      setToday(prev => ({
        ...prev,
        total: res.total_today,
        percent: res.percent,
        logs: [...(prev?.logs || []), { id: res.id, amount: res.amount, time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }), note: '' }],
        streak_days: res.streak_days,
      }))
      // 显示鼓励话语
      setEncouragement(res.encouragement)
      setGoalReached(res.goal_reached)
      setShowEncouragement(true)
      setTimeout(() => setShowEncouragement(false), 3000)
      // 刷新日历
      api.getWaterCalendar(calYear, calMonth).then(setCalendar).catch(() => {})
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
      setCustomAmount('')
    }
  }

  const onCustomSubmit = () => {
    const amount = parseInt(customAmount)
    if (amount > 0) logWater(amount)
  }

  // 日历渲染
  const renderCalendar = () => {
    if (!calendar) return null
    const firstDay = new Date(calYear, calMonth - 1, 1).getDay()
    const daysInMonth = new Date(calYear, calMonth, 0).getDate()
    const todayStr = new Date().toISOString().slice(0, 10)
    
    const cells = []
    // 空白填充
    for (let i = 0; i < firstDay; i++) {
      cells.push(<div key={`empty-${i}`} className="h-10" />)
    }
    // 日期
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${calYear}-${String(calMonth).padStart(2, '0')}-${String(d).padStart(2, '0')}`
      const dayData = calendar.calendar?.[dateStr]
      const isToday = dateStr === todayStr
      const reached = dayData?.reached
      const hasLog = dayData && dayData.total > 0
      
      cells.push(
        <div key={d} className={`h-10 flex flex-col items-center justify-center rounded-lg text-sm relative
          ${isToday ? 'ring-2 ring-brand-500' : ''}
          ${reached ? 'bg-brand-100 text-brand-700 font-bold' : hasLog ? 'bg-blue-50 text-blue-600' : 'text-ink-500'}
        `}>
          <span>{d}</span>
          {reached && <span className="text-[8px]">✓</span>}
        </div>
      )
    }
    return cells
  }

  const prevMonth = () => {
    if (calMonth === 1) { setCalYear(calYear - 1); setCalMonth(12) }
    else setCalMonth(calMonth - 1)
  }
  const nextMonth = () => {
    if (calMonth === 12) { setCalYear(calYear + 1); setCalMonth(1) }
    else setCalMonth(calMonth + 1)
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 pb-20 md:pb-6">
      {/* 标题 */}
      <div className="text-center mb-6">
        <h1 className="text-2xl sm:text-3xl font-black text-ink-800">💧 饮水打卡</h1>
        <p className="mt-1 text-sm text-ink-500">每天喝够水，健康每一天</p>
      </div>

      {/* 今日进度卡片 */}
      {today && (
        <div className="rounded-2xl bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-200/70 shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm text-ink-500">今日饮水</div>
              <div className="text-3xl font-black text-blue-600">{today.total}
                <span className="text-base font-normal text-ink-400 ml-1">/ {today.goal} ml</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-4xl font-black text-cyan-500">{today.percent}%</div>
              {today.streak_days > 0 && (
                <div className="text-xs text-orange-500 font-medium mt-1">
                  🔥 连续 {today.streak_days} 天
                </div>
              )}
            </div>
          </div>
          
          {/* 进度条 */}
          <div className="h-4 bg-white/60 rounded-full overflow-hidden mb-4">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                today.percent >= 100 ? 'bg-gradient-to-r from-green-400 to-emerald-500' : 'bg-gradient-to-r from-blue-400 to-cyan-500'
              }`}
              style={{ width: `${Math.min(today.percent, 100)}%` }}
            />
          </div>

          {/* 快捷打卡按钮 */}
          <div className="flex flex-wrap gap-2 mb-4">
            {QUICK_AMOUNTS.map(amount => (
              <button
                key={amount}
                onClick={() => logWater(amount)}
                disabled={loading}
                className="flex-1 min-w-[70px] py-3 rounded-xl font-bold text-white bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 disabled:opacity-50 transition-all shadow-sm hover:shadow-md active:scale-95"
              >
                +{amount}ml
              </button>
            ))}
          </div>

          {/* 自定义输入 */}
          <div className="flex gap-2">
            <input
              type="number"
              value={customAmount}
              onChange={(e) => setCustomAmount(e.target.value)}
              placeholder="自定义 (ml)"
              className="flex-1 px-4 py-3 rounded-xl border border-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:border-blue-400 transition bg-white"
            />
            <button
              onClick={onCustomSubmit}
              disabled={loading || !customAmount}
              className="px-6 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 disabled:opacity-50 transition-all"
            >
              打卡
            </button>
          </div>
        </div>
      )}

      {/* 鼓励话语弹窗 */}
      {showEncouragement && (
        <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
          <div className={`px-8 py-6 rounded-2xl shadow-2xl text-center animate-bounce-in
            ${goalReached ? 'bg-gradient-to-br from-green-400 to-emerald-500 text-white' : 'bg-gradient-to-br from-blue-400 to-cyan-500 text-white'}
          `}>
            <div className="text-4xl mb-2">{goalReached ? '🎉' : '💧'}</div>
            <div className="text-lg font-bold">{encouragement}</div>
          </div>
        </div>
      )}

      {/* 今日记录列表 */}
      {today && today.logs && today.logs.length > 0 && (
        <div className="rounded-2xl bg-white border border-ink-200/70 shadow-sm p-4 mb-6">
          <h3 className="text-sm font-bold text-ink-700 mb-3">📋 今日记录</h3>
          <div className="space-y-2">
            {today.logs.map((log, i) => (
              <div key={log.id || i} className="flex items-center justify-between py-2 border-b border-ink-100 last:border-0">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">💧</span>
                  <div>
                    <div className="font-bold text-ink-700">{log.amount} ml</div>
                    <div className="text-xs text-ink-400">{log.time}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 日历 */}
      <div className="rounded-2xl bg-white border border-ink-200/70 shadow-sm p-4">
        <div className="flex items-center justify-between mb-4">
          <button onClick={prevMonth} className="p-2 rounded-lg hover:bg-ink-100 transition">←</button>
          <h3 className="text-lg font-bold text-ink-700">{calYear}年{calMonth}月</h3>
          <button onClick={nextMonth} className="p-2 rounded-lg hover:bg-ink-100 transition">→</button>
        </div>
        
        {/* 星期标题 */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {['日', '一', '二', '三', '四', '五', '六'].map(d => (
            <div key={d} className="text-center text-xs font-medium text-ink-400 py-1">{d}</div>
          ))}
        </div>
        
        {/* 日期网格 */}
        <div className="grid grid-cols-7 gap-1">
          {renderCalendar()}
        </div>

        {/* 统计 */}
        {calendar && (
          <div className="mt-4 pt-4 border-t border-ink-100 flex justify-around text-center">
            <div>
              <div className="text-2xl font-black text-brand-600">{calendar.streak_days}</div>
              <div className="text-xs text-ink-500">连续打卡</div>
            </div>
            <div>
              <div className="text-2xl font-black text-blue-600">{calendar.days_logged}</div>
              <div className="text-xs text-ink-500">本月打卡</div>
            </div>
            <div>
              <div className="text-2xl font-black text-green-600">{calendar.days_reached}</div>
              <div className="text-xs text-ink-500">达标天数</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}