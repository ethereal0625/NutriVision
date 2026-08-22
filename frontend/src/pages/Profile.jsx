import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, getToken } from '../api.js'

const ACTIVITIES = [
  { id: '久坐', label: '久坐', desc: '办公/学习为主，很少运动' },
  { id: '轻度', label: '轻度', desc: '每周运动 1-3 次' },
  { id: '中度', label: '中度', desc: '每周运动 3-5 次' },
  { id: '高强度', label: '高强度', desc: '每周运动 6-7 次或体力劳动' },
]
const BMI_META = {
  偏瘦: { color: 'text-blue-500 bg-blue-50', tip: '体重偏轻，注意营养摄入，适当增重更健康' },
  正常: { color: 'text-brand-600 bg-brand-50', tip: '体重正常，继续保持均衡饮食和规律运动' },
  偏胖: { color: 'text-amber-600 bg-amber-50', tip: '轻微超重，建议适度控制热量并增加运动' },
  肥胖: { color: 'text-red-500 bg-red-50', tip: '达到肥胖范围，建议系统规划减脂计划' },
}

export default function Profile() {
  const nav = useNavigate()
  const [token] = useState(getToken())
  const [data, setData] = useState(null)
  const [form, setForm] = useState({ height_cm: '', weight_kg: '', age: '', gender: '男', activity: '轻度', water_goal: '2000' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) { nav('/login'); return }
    api.getProfile()
      .then((p) => {
        setData(p)
        setForm({
          height_cm: p.height_cm ?? '', weight_kg: p.weight_kg ?? '',
          age: p.age ?? '', gender: p.gender || '男', activity: p.activity || '轻度',
          water_goal: p.water_goal ?? '2000',
        })
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [token])

  const save = async () => {
    setSaving(true); setError(''); setSaved(false)
    try {
      const p = await api.updateProfile({
        height_cm: Number(form.height_cm) || null,
        weight_kg: Number(form.weight_kg) || null,
        age: Number(form.age) || null,
        gender: form.gender,
        activity: form.activity,
        water_goal: Number(form.water_goal) || 2000,
      })
      setData(p)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (e) { setError(e.message) } finally { setSaving(false) }
  }

  const inputCls = 'w-full px-4 py-2.5 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition bg-white'

  if (loading) return <div className="py-24 text-center text-ink-400">加载中...</div>
  const meta = BMI_META[data?.bmi_category] || BMI_META['正常']

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <div className="text-center mb-8">
        <h1 className="text-3xl sm:text-4xl font-black text-ink-800">👤 个人中心</h1>
        <p className="mt-2 text-ink-500">完善身体数据，让分析结果和每日目标更贴合你</p>
      </div>

      {/* 健康概览卡 */}
      <div className="rounded-3xl bg-gradient-to-br from-brand-600 to-brand-500 text-white p-7 mb-6 shadow-lg shadow-brand-500/20">
        <div className="grid sm:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-xs opacity-80 mb-1">BMI 指数</div>
            <div className="text-4xl font-black">{data?.bmi ?? '--'}</div>
            {data?.bmi_category && (
              <span className={`mt-2 inline-block px-3 py-1 rounded-full text-xs font-bold ${meta.color}`}>{data.bmi_category}</span>
            )}
          </div>
          <div className="text-center">
            <div className="text-xs opacity-80 mb-1">每日消耗 TDEE</div>
            <div className="text-4xl font-black">{data?.tdee ?? '--'}</div>
            <div className="text-xs opacity-80 mt-1">kcal / 天</div>
          </div>
          <div className="text-center">
            <div className="text-xs opacity-80 mb-1">档案状态</div>
            <div className="text-2xl font-black mt-1">{data?.has_profile ? '✅ 已完善' : '📝 未完善'}</div>
            <div className="text-xs opacity-80 mt-2">{data?.has_profile ? '分析已自动使用' : '完善后可个性化'}</div>
          </div>
        </div>
      </div>

      {data?.bmi_category && (
        <div className={`mb-6 px-5 py-3.5 rounded-2xl text-sm ${meta.color}`}>💡 {meta.tip}</div>
      )}

      {/* 编辑表单 */}
      <div className="rounded-3xl bg-white border border-ink-200/70 shadow-sm p-7">
        <h2 className="font-bold text-ink-800 mb-1">✏️ 编辑身体数据</h2>
        <p className="text-xs text-ink-400 mb-5">减肥期间体重每天都会变，随时回来更新即可；食物分析和每日目标会自动使用最新数据</p>
        {error && <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 text-red-600 text-sm">{error}</div>}

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs text-ink-500 mb-1.5">身高 (cm)</label>
            <input type="number" className={inputCls} value={form.height_cm} onChange={(e) => setForm({ ...form, height_cm: e.target.value })} placeholder="170" />
          </div>
          <div>
            <label className="block text-xs text-ink-500 mb-1.5">体重 (kg)</label>
            <input type="number" className={inputCls} value={form.weight_kg} onChange={(e) => setForm({ ...form, weight_kg: e.target.value })} placeholder="65" />
          </div>
          <div>
            <label className="block text-xs text-ink-500 mb-1.5">年龄</label>
            <input type="number" className={inputCls} value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} placeholder="22" />
          </div>
          <div>
            <label className="block text-xs text-ink-500 mb-1.5">性别</label>
            <select className={inputCls} value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}>
              <option>男</option><option>女</option>
            </select>
          </div>
        </div>

        <div className="mt-4">
          <label className="block text-xs text-ink-500 mb-1.5">活动水平</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {ACTIVITIES.map((a) => (
              <button key={a.id} type="button" onClick={() => setForm({ ...form, activity: a.id })}
                className={`px-3 py-3 rounded-xl border text-left transition ${form.activity === a.id ? 'border-brand-500 bg-brand-50' : 'border-ink-200 hover:border-ink-300'}`}>
                <div className="text-sm font-semibold text-ink-800">{a.label}</div>
                <div className="text-[11px] text-ink-400 mt-0.5">{a.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-4">
          <label className="block text-xs text-ink-500 mb-1.5">💧 每日饮水目标 (ml)</label>
          <input type="number" className={inputCls} value={form.water_goal} onChange={(e) => setForm({ ...form, water_goal: e.target.value })} placeholder="2000" />
          <div className="mt-1 text-[11px] text-ink-400">建议每天喝 1500-2500ml 水，约 8 杯</div>
        </div>

        <div className="mt-6 flex items-center gap-3">
          <button onClick={save} disabled={saving}
            className="px-8 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-brand-600 to-brand-500 hover:shadow-lg hover:shadow-brand-500/30 disabled:opacity-60 transition-all">
            {saving ? '保存中...' : '💾 保存资料'}
          </button>
          {saved && <span className="text-sm text-brand-600">✅ 已保存，分析会自动使用最新数据</span>}
        </div>
      </div>

      {/* 说明 */}
      <div className="mt-6 rounded-2xl bg-blue-50 border border-blue-100 p-5 text-sm text-blue-800 space-y-1.5">
        <div className="font-bold">📌 你的身体数据会被用在哪些地方？</div>
        <div>· 食物分析：改造方案会结合你的 BMI / 每日消耗给出个性化建议</div>
        <div>· 每日计划：自动计算 TDEE，按目标类型推荐热量缺口 / 盈余</div>
        <div>· 数据仅用于你的账号内计算，不会对外公开</div>
      </div>
    </div>
  )
}
