import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, getToken } from '../api.js'

const QUICK_AMOUNTS = [100, 200, 250, 350, 500]
const WATER_TIMES = ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00']

function nowHM() {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function reminderIcon(title) {
  if (title.includes('水')) return '💧'
  if (title.includes('药')) return '💊'
  return '⏰'
}

export default function Water() {
  const nav = useNavigate()
  const token = getToken()
  const [today, setToday] = useState(null)
  const [customAmount, setCustomAmount] = useState('')
  const [loading, setLoading] = useState(false)
  const [encouragement, setEncouragement] = useState('')
  const [goalReached, setGoalReached] = useState(false)
  const [showEncouragement, setShowEncouragement] = useState(false)
  const [calendar, setCalendar] = useState(null)
  const [calYear, setCalYear] = useState(new Date().getFullYear())
  const [calMonth, setCalMonth] = useState(new Date().getMonth() + 1)
  const [reminders, setReminders] = useState([])
  const [reminderForm, setReminderForm] = useState({ title: '💧 喝水', time: '09:00' })
  const [dueNow, setDueNow] = useState(null)
  const [notifOn, setNotifOn] = useState('Notification' in window && Notification.permission === 'granted')
  const firedRef = useRef(new Set())

  useEffect(() => { if (!token) nav('/login') }, [token, nav])

  const fetchWater = useCallback(() => {
    api.getWaterToday()
      .then(setToday)
      .catch(() => setToday({ total: 0, goal: 2000, percent: 0, logs: [], streak_days: 0 }))
    api.getWaterCalendar(calYear, calMonth).then(setCalendar).catch(() => {})
  }, [calYear, calMonth])

  useEffect(() => {
    if (!token) return
    fetchWater()
    api.getReminders().then((list) => setReminders(list || [])).catch(() => setReminders([]))
  }, [token, fetchWater])

  // 页面打开期间按点提醒
  useEffect(() => {
    if (!token) return
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().then((p) => setNotifOn(p === 'granted')).catch(() => {})
    }
    const check = () => {
      const hm = nowHM()
      const key = `${new Date().toDateString()} ${hm}`
      const due = reminders.find((r) => r.enabled && r.time === hm)
      if (due && !firedRef.current.has(key)) {
        firedRef.current.add(key)
        setDueNow(due)
        setTimeout(() => setDueNow(null), 15000)
        if (notifOn) {
          try { new Notification('NutriVision 提醒', { body: `${due.title}（${due.time}）` }) } catch {}
        }
      }
    }
    check()
    const id = setInterval(check, 20000)
    return () => clearInterval(id)
  }, [token, reminders, notifOn])

  const logWater = async (amount) => {
    if (!amount || amount <= 0) return
    setLoading(true)
    try {
      const res = await api.logWater(amount, '')
      setToday((prev) => ({
        ...(prev || { goal: 2000 }),
        total: res.total_today,
        goal: res.goal,
        percent: res.percent,
        logs: [...(prev?.logs || []), { id: res.id, amount: res.amount, time: nowHM(), note: '' }],
        streak_days: res.streak_days,
      }))
      setEncouragement(res.encouragement)
      setGoalReached(res.goal_reached)
      setShowEncouragement(true)
      setTimeout(() => setShowEncouragement(false), 3000)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
      setCustomAmount('')
    }
  }

  const onCustomSubmit = () => {
    const amount = parseInt(customAmount, 10)
    if (amount > 0) logWater(amount)
  }

  const saveReminder = async (title, time) => {
    try {
      const r = await api.addReminder(title, time)
      setReminders((prev) => [...prev, r].sort((a, b) => a.time.localeCompare(b.time)))
      setReminderForm({ title: '💧 喝水', time: '09:00' })
    } catch (e) {
      console.error(e)
    }
  }

  const toggleReminder = async (r) => {
    const next = [...reminders]
    const i = next.findIndex((x) => x.id === r.id)
    if (i < 0) return
    next[i] = { ...next[i], enabled: !next[i].enabled }
    setReminders(next)
    try {
      const up = await api.updateReminder(r.id, { title: r.title, time: r.time, enabled: !r.enabled })
      next[i] = up
      setReminders(next)
    } catch (e) {
      next[i] = r
      setReminders(next)
      console.error(e)
    }
  }

  const deleteReminder = async (id) => {
    setReminders((prev) => prev.filter((x) => x.id !== id))
    try { await api.deleteReminder(id) } catch (e) { console.error(e) }
  }

  const renderCalendar = () => {
    if (!calendar) return null
    const firstDay = new Date(calYear, calMonth - 1, 1).getDay()
    const daysInMonth = new Date(calYear, calMonth, 0).getDate()
    const todayStr = new Date().toISOString().slice(0, 10)
    const cells = []
    for (let i = 0; i < firstDay; i++) {
      cells.push(<div key={`empty-${i}`} className="h-10" />)
    }
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${calYear}-${String(calMonth).padStart(2, '0')}-${String(d).padStart(2, '0')}`
      const dayData = calendar.calendar?.[dateStr]
      const isToday = dateStr === todayStr
      const reached = dayData?.reached
      const hasLog = dayData && dayData.total > 0
      cells.push(
        <div key={d} className={`h-10 flex flex-col items-center justify-center rounded-lg text-sm relative
          ${isToday ? 'ring-2 ring-brand-500' : ''}
          ${reached ? 'bg-brand-100 text-brand-700 font-bold' : hasLog ? 'bg-blue-50 text-blue-600' : 'text-ink-500'}`}>
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
      <div className="text-center mb-6">
        <h1 className="text-2xl sm:text-3xl font-black text-ink-800">⏰ 提醒</h1>
        <p className="mt-1 text-sm text-ink-500">按时喝水、按时吃药，照顾好自己</p>
      </div>

      {/* 到点提醒横幅 */}
      {dueNow && (
        <div className="mb-4 rounded-2xl bg-gradient-to-br from-accent-500 to-orange-400 text-white shadow-lg px-5 py-4 flex items-center gap-4 animate-bounce-in">
          <div className="text-3xl">{reminderIcon(dueNow.title)}</div>
          <div className="flex-1">
            <div className="font-bold">{dueNow.title}</div>
            <div className="text-xs opacity-90">现在 {dueNow.time}，该行动啦</div>
          </div>
        </div>
      )}

      {/* 自定义提醒 */}
      <div className="rounded-2xl bg-white border border-ink-200/70 shadow-sm p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-ink-700">🔔 我的提醒</h2>
          <span className={`text-[11px] px-2.5 py-1 rounded-full font-medium ${notifOn ? 'bg-green-50 text-green-600' : 'bg-amber-50 text-amber-600'}`}>
            {notifOn ? '通知已开启' : '通知未开启'}
          </span>
        </div>

        {reminders.length > 0 ? (
          <div className="space-y-2 mb-4">
            {reminders.map((r) => (
              <div key={r.id} className="flex items-center gap-3 py-2.5 px-3 rounded-xl bg-ink-50/60 border border-ink-100">
                <span className="text-xl">{reminderIcon(r.title)}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-ink-800 truncate">{r.title}</div>
                  <div className="text-xs text-ink-400">每天 {r.time}</div>
                </div>
                <button
                  onClick={() => deleteReminder(r.id)}
                  className="w-8 h-8 rounded-lg text-ink-400 hover:text-red-500 hover:bg-red-50 transition"
                  title="删除"
                >
                  ✕
                </button>
                <button
                  onClick={() => toggleReminder(r)}
                  className={`w-11 h-6 rounded-full relative transition-colors ${r.enabled ? 'bg-brand-500' : 'bg-ink-200'}`}
                  title={r.enabled ? '暂停' : '启用'}
                >
                  <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all ${r.enabled ? 'left-[22px]' : 'left-0.5'}`} />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="mb-4 py-4 text-center text-sm text-ink-400">还没有提醒，添加喝水或吃药提醒吧</div>
        )}

        <div className="flex flex-wrap gap-2 mb-3">
          {WATER_TIMES.slice(0, 6).map((t) => (
            <button key={t} onClick={() => saveReminder('💧 喝水', t)} className="px-3 py-1.5 rounded-full text-xs font-medium bg-blue-50 text-blue-600 border border-blue-100 hover:bg-blue-100 transition">
              💧 {t}
            </button>
          ))}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={reminderForm.title}
            onChange={(e) => setReminderForm({ ...reminderForm, title: e.target.value })}
            placeholder="提醒内容（如 💊 吃药）"
            className="flex-1 min-w-0 px-4 py-2.5 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition bg-white"
          />
          <input
            type="time"
            value={reminderForm.time}
            onChange={(e) => setReminderForm({ ...reminderForm, time: e.target.value })}
            className="px-3 py-2.5 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition bg-white"
          />
          <button
            onClick={() => saveReminder(reminderForm.title, reminderForm.time)}
            disabled={!reminderForm.title.trim() || !reminderForm.time}
            className="px-5 py-2.5 rounded-xl font-bold text-white bg-gradient-to-r from-brand-600 to-brand-500 hover:opacity-90 disabled:opacity-50 transition"
          >
            添加
          </button>
        </div>
      </div>

      {/* 今日饮水进度 */}
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
                <div className="text-xs text-orange-500 font-medium mt-1">🔥 连续 {today.streak_days} 天</div>
              )}
            </div>
          </div>

          <div className="h-4 bg-white/60 rounded-full overflow-hidden mb-4">
            <div
              className={`h-full rounded-full transition-all duration-500 ${today.percent >= 100 ? 'bg-gradient-to-r from-green-400 to-emerald-500' : 'bg-gradient-to-r from-blue-400 to-cyan-500'}`}
              style={{ width: `${Math.min(today.percent, 100)}%` }}
            />
          </div>

          <div className="flex flex-wrap gap-2 mb-4">
            {QUICK_AMOUNTS.map((amount) => (
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
          <div className={`px-8 py-6 rounded-2xl shadow-2xl text-center animate-bounce-in ${goalReached ? 'bg-gradient-to-br from-green-400 to-emerald-500 text-white' : 'bg-gradient-to-br from-blue-400 to-cyan-500 text-white'}`}>
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

        <div className="grid grid-cols-7 gap-1 mb-2">
          {['日', '一', '二', '三', '四', '五', '六'].map((d) => (
            <div key={d} className="text-center text-xs font-medium text-ink-400 py-1">{d}</div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-1">
          {renderCalendar()}
        </div>

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
