import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, getToken } from '../api.js'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from 'recharts'

const MODELS = [
  { id: 'qwen-vl-plus', label: '通义千问 Qwen-VL-Plus' },
  { id: 'qwen-vl-max', label: '通义千问 Qwen-VL-Max' },
  { id: 'glm-4v', label: '智谱 GLM-4V' },
  { id: 'doubao-seed-2.0', label: '豆包 Seed' },
]
const GOALS = ['减脂', '控糖', '增肌', '均衡饮食']

export default function Analyze() {
  const nav = useNavigate()
  const [token, setToken] = useState(getToken())
  const fileRef = useRef(null)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [models, setModels] = useState(['qwen-vl-plus'])
  const [goal, setGoal] = useState('减脂')
  const [profileInfo, setProfileInfo] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [activeTab, setActiveTab] = useState(0)
  const [mealType, setMealType] = useState('午餐')
  const [weightEdits, setWeightEdits] = useState({})
  const [edited, setEdited] = useState(false)
  const [compensate, setCompensate] = useState(null)
  const [shareOpen, setShareOpen] = useState(false)
  const [shareImage, setShareImage] = useState('')

  useEffect(() => { if (!token) nav('/login') }, [token])
  useEffect(() => {
    if (!token) return
    api.getProfile().then(setProfileInfo).catch(() => {})
  }, [token])

  const onFileChange = (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    setResult(null)
    setSaved(false)
    setPreview(URL.createObjectURL(f))
  }

  const run = async () => {
    if (!file) return
    setLoading(true); setError(''); setSaved(false); setResult(null)
    const fd = new FormData()
    fd.append('file', file)
    fd.append('models', models.join(','))
    fd.append('goal', goal)
    fd.append('profile', '{}')
    try {
      const res = await api.analyze(fd)
      setResult(res)
      // 获取当日补偿建议
      api.getCompensate().then(setCompensate).catch(() => {})
      setWeightEdits({}); setEdited(false)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const saveHistory = async () => {
    if (!result) return
    const primary = result.results?.[result.primary_model] || {}
    const adj = edited ? buildAdjusted() : result
    try {
      await api.saveHistory({
        dish_name: primary.dish_name || '',
        calories: edited ? (adj.calories || 0) : (result.calories || 0),
        models: result.models.join(','),
        goal,
        result_json: JSON.stringify(adj),
      })
      setSaved(true)
    } catch (e) { setError(e.message) }
  }

  const logToday = async () => {
    if (!result) return
    const primary = result.results?.[result.primary_model] || {}
    const today = new Date().toISOString().slice(0, 10)
    const adj = edited ? buildAdjusted() : result
    try {
      await api.saveHistory({
        dish_name: primary.dish_name || '未知食物',
        calories: edited ? (adj.calories || 0) : (result.calories || 0),
        models: result.models.join(','),
        goal,
        result_json: JSON.stringify(adj),
        date: today,
        meal_type: mealType,
      })
      setSaved(true)
    } catch (e) { setError(e.message) }
  }

  const modelList = result?.models || []
  const primary = result?.results?.[result.primary_model] || {}
  const plan = result?.plan || {}

  const drawRoundRect = (ctx, x, y, w, h, r) => {
    ctx.beginPath()
    ctx.moveTo(x + r, y)
    ctx.arcTo(x + w, y, x + w, y + h, r)
    ctx.arcTo(x + w, y + h, x, y + h, r)
    ctx.arcTo(x, y + h, x, y, r)
    ctx.arcTo(x, y, x + w, y, r)
    ctx.closePath()
  }

  const generateShareCard = () => {
    try {
      const canvas = document.createElement('canvas')
      canvas.width = 640
      canvas.height = 960
      const ctx = canvas.getContext('2d')
      const score = result.nutrition_score || {}
      const before = plan.before_after?.before || {}
      const after = plan.before_after?.after || {}
      const dishName = primary.dish_name || '未知食物'
      const cal = result.calories || 0
      const savedCal = before.calories && after.calories ? before.calories - after.calories : 0

      // 背景渐变
      const grad = ctx.createLinearGradient(0, 0, 0, 960)
      grad.addColorStop(0, '#2e8b57')
      grad.addColorStop(1, '#14532d')
      ctx.fillStyle = grad
      ctx.fillRect(0, 0, 640, 960)

      // 顶部标题
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 34px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText('AI 健康饮食改造师', 320, 70)
      ctx.font = '18px sans-serif'
      ctx.fillStyle = 'rgba(255,255,255,0.85)'
      ctx.fillText('NutriVision', 320, 102)

      // 白色主体
      ctx.fillStyle = '#ffffff'
      drawRoundRect(ctx, 32, 140, 576, 768, 26)
      ctx.fill()

      // 菜品名
      ctx.fillStyle = '#1f2937'
      ctx.font = 'bold 30px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(dishName, 320, 210)

      // 热量
      ctx.fillStyle = '#2e8b57'
      ctx.font = 'bold 62px sans-serif'
      ctx.fillText(cal + ' kcal', 320, 300)

      // 营养评分
      ctx.fillStyle = '#6b7280'
      ctx.font = '16px sans-serif'
      ctx.fillText('营养评分', 320, 350)
      const gradeColor = score.color === 'green' ? '#16a34a' : score.color === 'blue' ? '#2563eb' : score.color === 'orange' ? '#f59e0b' : '#dc2626'
      ctx.fillStyle = gradeColor
      ctx.font = 'bold 46px sans-serif'
      ctx.fillText((score.grade || '?') + ' · ' + (score.label || ''), 320, 410)

      // 分割线
      ctx.strokeStyle = '#e5e7eb'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(80, 460)
      ctx.lineTo(560, 460)
      ctx.stroke()

      // 改造前后
      if (before.name || after.name) {
        ctx.font = 'bold 22px sans-serif'
        ctx.fillStyle = '#1f2937'
        ctx.fillText('健康改造', 320, 510)
        ctx.font = '18px sans-serif'
        ctx.fillStyle = '#dc2626'
        ctx.fillText('改造前：' + (before.name || '原菜品') + '  ' + (before.calories || '?') + ' kcal', 320, 560)
        ctx.fillStyle = '#16a34a'
        ctx.fillText('改造后：' + (after.name || plan.healthy_dish_name || '健康版') + '  ' + (after.calories || '?') + ' kcal', 320, 605)
        if (savedCal > 0) {
          ctx.fillStyle = '#2e8b57'
          ctx.font = 'bold 22px sans-serif'
          ctx.fillText('每餐减少 ' + savedCal + ' kcal', 320, 660)
        }
      }

      // 底部品牌
      ctx.fillStyle = '#9ca3af'
      ctx.font = '15px sans-serif'
      ctx.fillText('AI 识别 · 营养数据库核算 · 个性化改造', 320, 860)

      setShareImage(canvas.toDataURL('image/png'))
      setShareOpen(true)
    } catch (e) {
      console.error(e)
    }
  }

  const maxCal = Math.max(1, ...(result ? Object.values(result.calories_by_model || {}) : [1]))

  // ===== 克重编辑：用户可修改 AI 估算的食材克重，热量与营养结构即时重算 =====
  const effWeight = (m, i) => {
    const v = weightEdits[`${m}:${i}`]
    if (v !== undefined) return Number(v) || 0
    return result?.breakdown_by_model?.[m]?.[i]?.weight_g ?? 0
  }
  const effCalories = (m) => {
    const bd = result?.breakdown_by_model?.[m] || []
    return bd.reduce((sum, b, i) => sum + effWeight(m, i) * (b.kcal_per_100g || 0) / 100, 0)
  }
  const effMacros = (m) => {
    const bd = result?.breakdown_by_model?.[m] || []
    let p = 0, c = 0, f = 0
    bd.forEach((b, i) => {
      const w = effWeight(m, i)
      p += w * (b.protein_per_100g || 0) / 100
      c += w * (b.carbs_per_100g || 0) / 100
      f += w * (b.fat_per_100g || 0) / 100
    })
    return { protein: Math.round(p), carbs: Math.round(c), fat: Math.round(f) }
  }
  const primaryCal = Math.round(effCalories(result?.primary_model))
  const primaryMacros = effMacros(result?.primary_model)
  const primaryKcal = primaryCal * 4.184
  // 保存历史前把修正后的数据写回 result（周报/历史读到的也是修正值）
  const buildAdjusted = () => {
    const adj = JSON.parse(JSON.stringify(result))
    adj.calories = primaryCal
    adj.calories_by_model = {}
    for (const m of modelList) adj.calories_by_model[m] = Math.round(effCalories(m))
    const pm = effMacros(result?.primary_model)
    const totalK = (pm.protein * 4 + pm.carbs * 4 + pm.fat * 9) || 1
    adj.macros = {
      protein: pm.protein, carbs: pm.carbs, fat: pm.fat,
      protein_pct: Math.round(pm.protein * 4 / totalK * 1000) / 10,
      carbs_pct: Math.round(pm.carbs * 4 / totalK * 1000) / 10,
      fat_pct: Math.round(pm.fat * 9 / totalK * 1000) / 10,
    }
    adj.breakdown_by_model = {}
    for (const m of modelList) {
      adj.breakdown_by_model[m] = (result?.breakdown_by_model?.[m] || []).map((b, i) => ({
        ...b,
        weight_g: effWeight(m, i),
        calories: Math.round(effWeight(m, i) * (b.kcal_per_100g || 0) / 100),
      }))
    }
    return adj
  }


  const inputCls = 'w-full px-4 py-2.5 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition bg-white'

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="text-center mb-10">
        <h1 className="text-3xl sm:text-4xl font-black text-ink-800">🍽️ 食物分析</h1>
        <p className="mt-2 text-ink-500">上传食物照片 → 多模型识别 → 营养核算 → 健康改造方案</p>
      </div>

      {/* 上传 + 设置 */}
      <div className="grid lg:grid-cols-[1fr_340px] gap-6">
        {/* 左侧：上传 */}
        <div className="rounded-3xl bg-white border border-ink-200/70 shadow-sm p-6">
          <div
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) { setFile(f); setResult(null); setSaved(false); setPreview(URL.createObjectURL(f)) } }}
            className="cursor-pointer rounded-2xl border-2 border-dashed border-brand-300 bg-brand-50/50 hover:bg-brand-50 hover:border-brand-400 transition-all p-10 text-center">
            {preview ? (
              <img src={preview} alt="preview" className="mx-auto max-h-72 rounded-xl shadow-md" />
            ) : (
              <div className="py-8">
                <div className="text-5xl mb-3">📸</div>
                <p className="font-semibold text-ink-700">点击或拖拽上传食物图片</p>
                <p className="mt-1 text-sm text-ink-400">支持 JPG / PNG，单张不超过 20MB</p>
              </div>
            )}
          </div>
          <input ref={fileRef} type="file" accept="image/jpeg,image/png" hidden onChange={onFileChange} />
          <button onClick={run} disabled={!file || loading}
            className="mt-5 w-full py-3.5 rounded-xl font-bold text-white bg-gradient-to-r from-brand-600 to-brand-500 hover:shadow-lg hover:shadow-brand-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all">
            {loading ? '🔍 分析中，请稍候...' : '🚀 开始分析'}
          </button>
          {error && <div className="mt-4 px-4 py-3 rounded-xl bg-red-50 text-red-600 text-sm">{error}</div>}
        </div>

        {/* 右侧：设置 */}
        <div className="rounded-3xl bg-white border border-ink-200/70 shadow-sm p-6 space-y-5">
          <div>
            <label className="block text-sm font-semibold text-ink-700 mb-2">🧠 视觉模型（可多选）</label>
            <div className="space-y-2">
              {MODELS.map((m) => (
                <label key={m.id} className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl border cursor-pointer transition ${models.includes(m.id) ? 'border-brand-500 bg-brand-50' : 'border-ink-200 hover:border-ink-300'}`}>
                  <input type="checkbox" checked={models.includes(m.id)} onChange={() => setModels(models.includes(m.id) ? models.filter(x => x !== m.id) : [...models, m.id])} className="w-4 h-4 accent-brand-600" />
                  <span className="text-sm text-ink-700">{m.label}</span>
                </label>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-semibold text-ink-700 mb-2">🎯 健康目标</label>
            <div className="grid grid-cols-4 gap-2">
              {GOALS.map((g) => (
                <button key={g} onClick={() => setGoal(g)}
                  className={`py-2 rounded-xl text-sm font-medium transition ${goal === g ? 'bg-brand-600 text-white shadow' : 'bg-ink-100 text-ink-600 hover:bg-ink-200'}`}>
                  {g}
                </button>
              ))}
            </div>
          </div>
          <div>
            <div className="text-sm font-semibold text-ink-700 mb-2">👤 我的档案</div>
            {profileInfo?.has_profile ? (
              <div className="rounded-xl bg-brand-50 border border-brand-100 p-3.5 text-sm">
                <div className="text-brand-700 font-semibold">✅ 已自动使用个人档案</div>
                <div className="mt-1.5 text-xs text-ink-600 leading-relaxed">
                  {profileInfo.height_cm}cm · {profileInfo.weight_kg}kg · {profileInfo.age}岁 · {profileInfo.gender}
                  <br />BMI <b>{profileInfo.bmi}</b>（{profileInfo.bmi_category}）· 每日消耗约 <b>{profileInfo.tdee} kcal</b>
                </div>
                <Link to="/profile" className="mt-2 inline-block text-xs font-semibold text-brand-600 hover:text-brand-700">修改档案 →</Link>
              </div>
            ) : (
              <div className="rounded-xl bg-ink-100/70 border border-ink-200 p-3.5 text-sm">
                <div className="text-ink-600 font-semibold">📝 未填写个人档案</div>
                <div className="mt-1 text-xs text-ink-400">当前按基础方式分析。填写后改造方案会结合你的 BMI 和每日消耗，更个性化</div>
                <Link to="/profile" className="mt-2 inline-block text-xs font-semibold text-brand-600 hover:text-brand-700">去完善档案 →</Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ===== 分析结果 ===== */}
      {result && result.is_food && (
        <div className="mt-10 space-y-6 fade-up">
          {/* 原图 + 概览 */}
          <div className="grid md:grid-cols-[280px_1fr] gap-6">
            <div className="rounded-2xl overflow-hidden border border-ink-200/70 shadow-sm">
              {preview && <img src={preview} alt="原图" className="w-full object-cover" />}
              <div className="p-3 text-center text-xs text-ink-500 bg-white">原图 · {primary.dish_name || '未识别菜名'}</div>
            </div>
            <div className="rounded-2xl bg-white border border-ink-200/70 shadow-sm p-6">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-black text-brand-600">{primaryCal}</div>
                  <div className="text-xs text-ink-500 mt-1">营养库核算 (kcal) · 约 {Math.round(primaryKcal)} kJ</div>
                  {edited && <div className="mt-1 text-[11px] font-semibold text-orange-500">✏️ 已按修正克重</div>}
                </div>
                <div><div className="text-2xl font-black text-ink-800">{primary.model_calories ?? '-'}</div><div className="text-xs text-ink-500 mt-1">模型估算 (kcal)</div></div>
                <div><div className="text-2xl font-black text-ink-800">{result.models.length}</div><div className="text-xs text-ink-500 mt-1">使用模型</div></div>
              </div>
              {result.matched_products?.length > 0 && (
                <div className="mt-4 px-4 py-3 rounded-xl bg-orange-50 border border-orange-100">
                  <div className="text-xs font-semibold text-orange-600 mb-1">🏷️ 品牌商品热量参考</div>
                  {result.matched_products.map((mp, i) => (
                    <div key={i} className="text-sm text-ink-700">
                      {mp.brand} · {mp.name}（{mp.serving}）<span className="font-bold text-orange-600">{mp.kcal} kcal</span>
                      {mp.note ? <span className="text-xs text-ink-400"> · {mp.note}</span> : null}
                    </div>
                  ))}
                </div>
              )}
              <div className="mt-3 px-3 py-2 rounded-xl bg-blue-50 border border-blue-100 text-xs text-blue-700">
                💡 小知识：1 大卡(kcal) ≈ 4.18 千焦(kJ)。食品包装上的 kJ 除以 4 左右才是大卡，别搞混啦。
              </div>
              <div className="mt-3">
                <div className="text-xs font-semibold text-ink-500 mb-1.5">各模型热量对比</div>
                <div className="space-y-2">
                  {modelList.map((m) => (
                    <div key={m}>
                      <div className="flex justify-between text-xs text-ink-600 mb-0.5">
                        <span>{MODELS.find(x => x.id === m)?.label || m}</span>
                        <span className="font-semibold">{Math.round(effCalories(m))} kcal</span>
                      </div>
                      <div className="h-2 rounded-full bg-ink-100 overflow-hidden">
                        <div className="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-400 transition-all"
                          style={{ width: `${(Math.round(effCalories(m)) / maxCal) * 100}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              {result.macros && (
                <div className="mt-5 border-t border-ink-100 pt-4">
                  <div className="text-xs font-semibold text-ink-500 mb-2">🥩 营养结构（蛋白质 / 碳水 / 脂肪）</div>
                  <div className="grid grid-cols-3 gap-2 mb-3 text-center">
                    <div className="rounded-xl bg-red-50 p-2.5">
                      <div className="text-lg font-black text-red-500">{primaryMacros.protein}g</div>
                      <div className="text-xs text-ink-500">蛋白质 · {Math.round(primaryMacros.protein * 4 / ((primaryMacros.protein * 4 + primaryMacros.carbs * 4 + primaryMacros.fat * 9) || 1) * 100 * 10) / 10}%</div>
                    </div>
                    <div className="rounded-xl bg-amber-50 p-2.5">
                      <div className="text-lg font-black text-amber-600">{primaryMacros.carbs}g</div>
                      <div className="text-xs text-ink-500">碳水 · {Math.round(primaryMacros.carbs * 4 / ((primaryMacros.protein * 4 + primaryMacros.carbs * 4 + primaryMacros.fat * 9) || 1) * 100 * 10) / 10}%</div>
                    </div>
                    <div className="rounded-xl bg-orange-50 p-2.5">
                      <div className="text-lg font-black text-orange-500">{primaryMacros.fat}g</div>
                      <div className="text-xs text-ink-500">脂肪 · {Math.round(primaryMacros.fat * 9 / ((primaryMacros.protein * 4 + primaryMacros.carbs * 4 + primaryMacros.fat * 9) || 1) * 100 * 10) / 10}%</div>
                    </div>
                  </div>
                  <div className="h-2.5 rounded-full bg-ink-100 overflow-hidden flex">
                    <div className="h-full bg-red-400" style={{ width: `${Math.round(primaryMacros.protein * 4 / ((primaryMacros.protein * 4 + primaryMacros.carbs * 4 + primaryMacros.fat * 9) || 1) * 100)}%` }} />
                    <div className="h-full bg-amber-400" style={{ width: `${Math.round(primaryMacros.carbs * 4 / ((primaryMacros.protein * 4 + primaryMacros.carbs * 4 + primaryMacros.fat * 9) || 1) * 100)}%` }} />
                    <div className="h-full bg-orange-400" style={{ width: `${Math.round(primaryMacros.fat * 9 / ((primaryMacros.protein * 4 + primaryMacros.carbs * 4 + primaryMacros.fat * 9) || 1) * 100)}%` }} />
                  </div>
                  <div className="mt-1.5 text-xs text-ink-400">按供能占比：蛋白质 {Math.round(primaryMacros.protein * 4 / ((primaryMacros.protein * 4 + primaryMacros.carbs * 4 + primaryMacros.fat * 9) || 1) * 100 * 10) / 10}% · 碳水 {Math.round(primaryMacros.carbs * 4 / ((primaryMacros.protein * 4 + primaryMacros.carbs * 4 + primaryMacros.fat * 9) || 1) * 100 * 10) / 10}% · 脂肪 {Math.round(primaryMacros.fat * 9 / ((primaryMacros.protein * 4 + primaryMacros.carbs * 4 + primaryMacros.fat * 9) || 1) * 100 * 10) / 10}%</div>
                </div>
              )}
            </div>
          </div>

          {/* 每个模型的分析 Tab */}
          <div className="rounded-2xl bg-white border border-ink-200/70 shadow-sm overflow-hidden">
            <div className="flex border-b border-ink-200 overflow-x-auto">
              {modelList.map((m, i) => (
                <button key={m} onClick={() => setActiveTab(i)}
                  className={`px-5 py-3 text-sm font-semibold whitespace-nowrap transition ${activeTab === i ? 'text-brand-700 border-b-2 border-brand-600' : 'text-ink-500 hover:text-ink-700'}`}>
                  {MODELS.find(x => x.id === m)?.label || m}
                </button>
              ))}
            </div>
            <div className="p-6">
              {(() => {
                const m = modelList[activeTab]
                const a = result.results?.[m] || {}
                const bd = result.breakdown_by_model?.[m] || []
                return (
                  <div className="grid lg:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-bold text-ink-800">菜名：{a.dish_name || '-'}</h3>
                      <p className="text-sm text-ink-500 mt-1">烹饪方式：{a.cooking_method || '-'}</p>
                      <div className="mt-4">
                        <div className="text-xs font-semibold text-ink-500 mb-1.5">风险标签</div>
                        <div className="flex flex-wrap gap-2">
                          {(a.health_risk_tags || []).map((t) => (
                            <span key={t} className="px-2.5 py-1 rounded-full bg-orange-50 text-orange-600 text-xs font-medium">{t}</span>
                          ))}
                          {!(a.health_risk_tags || []).length && <span className="px-2.5 py-1 rounded-full bg-brand-50 text-brand-600 text-xs font-medium">无明显风险</span>}
                        </div>
                      </div>
                      <div className="mt-4">
                        <div className="text-xs font-semibold text-ink-500 mb-1.5">视觉描述（英文）</div>
                        <p className="text-sm text-ink-600 leading-relaxed">{a.visual_description || '-'}</p>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="text-xs font-semibold text-ink-500">热量明细（成分表法）</div>
                        <div className="text-[11px] text-ink-400">✏️ 克重可修改，热量与营养即时重算</div>
                      </div>
                      <div className="overflow-x-auto rounded-xl border border-ink-200">
                        <table className="w-full text-sm">
                          <thead className="bg-brand-50 text-brand-700">
                            <tr><th className="px-3 py-2 text-left">食材</th><th className="px-3 py-2 text-right">克重(g)</th><th className="px-3 py-2 text-right">每100g</th><th className="px-3 py-2 text-right">小计</th></tr>
                          </thead>
                          <tbody>
                            {(bd || []).map((b, i) => {
                              const w = effWeight(m, i)
                              const sub = Math.round(w * (b.kcal_per_100g || 0) / 100)
                              return (
                                <tr key={i} className="border-t border-ink-200">
                                  <td className="px-3 py-2">{b.name}</td>
                                  <td className="px-3 py-2 text-right">
                                    <input
                                      type="number"
                                      min={0}
                                      value={w}
                                      onChange={(e) => {
                                        setWeightEdits((prev) => ({ ...prev, [`${m}:${i}`]: e.target.value }))
                                        setEdited(true)
                                      }}
                                      className="w-20 px-1.5 py-1 text-right rounded-lg border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition"
                                    />
                                  </td>
                                  <td className="px-3 py-2 text-right">{b.kcal_per_100g}</td>
                                  <td className="px-3 py-2 text-right font-semibold">{sub}</td>
                                </tr>
                              )
                            })}
                          </tbody>
                          <tfoot>
                            <tr className="border-t-2 border-brand-200 bg-brand-50/60">
                              <td className="px-3 py-2 font-bold text-brand-700" colSpan={3}>合计</td>
                              <td className="px-3 py-2 text-right font-black text-brand-700">{Math.round(effCalories(m))} kcal</td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </div>
                  </div>
                )
              })()}
            </div>
          </div>



          {/* 营养评分卡片 */}
          {result.nutrition_score && (
            <div className="rounded-2xl bg-white border border-ink-200/70 shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-ink-800">📊 营养评分</h3>
                <div className={`px-4 py-1.5 rounded-full text-sm font-black text-white ${
                  result.nutrition_score.color === 'green' ? 'bg-green-500' :
                  result.nutrition_score.color === 'blue' ? 'bg-blue-500' :
                  result.nutrition_score.color === 'orange' ? 'bg-orange-500' : 'bg-red-500'
                }`}>
                  {result.nutrition_score.grade} · {result.nutrition_score.label} ({result.nutrition_score.score}分)
                </div>
              </div>

              {/* 宏量营养素雷达图 */}
              {result.macros && (
                <div className="mb-4">
                  <div className="text-xs text-ink-500 mb-1">🍎 宏量营养素均衡度</div>
                  <ResponsiveContainer width="100%" height={200}>
                    <RadarChart
                      data={[
                        { name: '蛋白质', actual: result.macros.protein_pct || 0, target: 27 },
                        { name: '碳水', actual: result.macros.carbs_pct || 0, target: 55 },
                        { name: '脂肪', actual: result.macros.fat_pct || 0, target: 27 },
                      ]}
                      outerRadius="70%"
                    >
                      <PolarGrid />
                      <PolarAngleAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} />
                      <Radar name="实际" dataKey="actual" stroke="#2e8b57" fill="#2e8b57" fillOpacity={0.35} />
                      <Radar name="目标" dataKey="target" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.12} strokeDasharray="4 4" />
                    </RadarChart>
                  </ResponsiveContainer>
                  <div className="flex justify-center gap-4 text-xs text-ink-500">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-brand-600 inline-block" />实际</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />理想</span>
                  </div>
                </div>
              )}

              {/* 三项评分条 */}
              <div className="space-y-3">
                {[
                  { label: '热量控制', score: result.nutrition_score.details.calorie_score, color: 'bg-brand-500' },
                  { label: '营养均衡', score: result.nutrition_score.details.macro_score, color: 'bg-blue-500' },
                  { label: '烹饪方式', score: result.nutrition_score.details.cooking_score, color: 'bg-amber-500' },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="flex justify-between text-xs text-ink-500 mb-1">
                      <span>{item.label}</span>
                      <span className="font-bold">{item.score}分</span>
                    </div>
                    <div className="h-2 bg-ink-100 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${item.color}`} style={{ width: `${item.score}%` }} />
                    </div>
                  </div>
                ))}
              </div>

              {/* 改善建议 */}
              {result.nutrition_score.advice && result.nutrition_score.advice.length > 0 && (
                <div className="mt-4 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200">
                  <div className="text-xs font-semibold text-amber-700 mb-1">💡 改善建议</div>
                  <ul className="space-y-1">
                    {result.nutrition_score.advice.map((a, i) => (
                      <li key={i} className="text-sm text-amber-800">· {a}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}


          {/* 改造前后对比卡片 */}
          {plan && plan.before_after && (
            <div className="rounded-2xl bg-gradient-to-br from-orange-50 to-brand-50 border border-brand-200/70 shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-ink-800">🔄 改造前后对比</h3>
                {plan.difficulty && (
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    plan.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                    plan.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {plan.difficulty === 'easy' ? '🟢 简单' :
                     plan.difficulty === 'medium' ? '🟡 中等' : '🔴 困难'}
                  </span>
                )}
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                {/* 改造前 */}
                <div className="rounded-xl bg-white/80 border-2 border-red-200 p-4">
                  <div className="text-xs font-semibold text-red-600 mb-2">❌ 改造前</div>
                  <div className="text-lg font-bold text-ink-800 mb-2">{plan.before_after.before?.name || '原菜品'}</div>
                  <div className="text-2xl font-black text-red-600 mb-3">{plan.before_after.before?.calories || '?'} kcal</div>
                  {plan.before_after.before?.tags && plan.before_after.before.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {plan.before_after.before.tags.map((tag, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-red-50 text-red-600 rounded-full">🔴 {tag}</span>
                      ))}
                    </div>
                  )}
                </div>

                {/* 改造后 */}
                <div className="rounded-xl bg-white/80 border-2 border-green-200 p-4">
                  <div className="text-xs font-semibold text-green-600 mb-2">✅ 改造后</div>
                  <div className="text-lg font-bold text-ink-800 mb-2">{plan.before_after.after?.name || plan.healthy_dish_name || '健康版'}</div>
                  <div className="text-2xl font-black text-green-600 mb-3">{plan.before_after.after?.calories || '?'} kcal</div>
                  {plan.before_after.after?.tags && plan.before_after.after.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {plan.before_after.after.tags.map((tag, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-green-50 text-green-600 rounded-full">✅ {tag}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* 热量差值 */}
              {plan.before_after.before?.calories && plan.before_after.after?.calories && (
                <div className="mt-4 text-center">
                  <div className="inline-block px-6 py-3 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-500 text-white font-bold shadow-lg">
                    🔥 每餐减少 {plan.before_after.before.calories - plan.before_after.after.calories} kcal
                    {plan.expected_effects && <span className="ml-2 text-sm opacity-90">· {plan.expected_effects}</span>}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 改造方案 */}
          {plan && (
            <div className="rounded-2xl bg-white border border-ink-200/70 shadow-sm p-6">
              <h3 className="text-lg font-bold text-ink-800">
                💡 「{goal}」改造方案 → <span className="text-brand-600">{plan.healthy_dish_name || ''}</span>
              </h3>
              <div className="mt-4 grid md:grid-cols-2 gap-6">
                <div>
                  <div className="text-xs font-semibold text-red-500 mb-1.5">不健康点</div>
                  <ul className="space-y-1.5">
                    {(plan.risk_points || []).map((p, i) => <li key={i} className="text-sm text-ink-600">🔴 {p}</li>)}
                  </ul>
                </div>
                <div>
                  <div className="text-xs font-semibold text-brand-600 mb-1.5">改造步骤</div>
                  <ol className="space-y-1.5">
                    {(plan.modification_plan || []).map((s, i) => <li key={i} className="text-sm text-ink-600">{i + 1}. ✅ {s}</li>)}
                  </ol>
                </div>
              </div>
              {plan.expected_effects && (
                <div className="mt-4 px-4 py-3 rounded-xl bg-brand-50 text-brand-700 text-sm font-medium">{plan.expected_effects}</div>
              )}
            </div>
          )}

          {/* 替换建议 */}
          {result.swap_suggestions?.length > 0 && (
            <div className="rounded-2xl bg-white border border-ink-200/70 shadow-sm p-6">
              <h3 className="text-lg font-bold text-ink-800">🔄 食材替换建议</h3>
              <div className="mt-4 grid sm:grid-cols-2 gap-3">
                {result.swap_suggestions.map((s, i) => (
                  <div key={i} className="rounded-xl bg-ink-100 p-4">
                    <div className="text-sm font-semibold text-ink-700">
                      {s.original} <span className="text-brand-600">→</span> {s.swap}
                    </div>
                    <div className="mt-1 text-xs text-ink-500">{s.reason}</div>
                  </div>
                ))}
              </div>
            </div>
          )}


          {/* 膳食动态补偿卡片 */}
          {compensate && compensate.today_summary && (
            <div className="rounded-2xl bg-gradient-to-br from-brand-50 to-emerald-50 border border-brand-200/70 shadow-sm p-6">
              <h3 className="text-lg font-bold text-ink-800 flex items-center gap-2">
                ⚖️ 今日膳食平衡
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  compensate.status === 'over' ? 'bg-red-100 text-red-700' :
                  compensate.status === 'slightly_over' ? 'bg-orange-100 text-orange-700' :
                  compensate.status === 'under' ? 'bg-blue-100 text-blue-700' :
                  'bg-brand-100 text-brand-700'
                }`}>
                  {compensate.status === 'over' ? '已超标' :
                   compensate.status === 'slightly_over' ? '略超' :
                   compensate.status === 'under' ? '摄入不足' : '进行中'}
                </span>
              </h3>

              {/* 进度条 */}
              <div className="mt-4">
                <div className="flex justify-between text-sm text-ink-600 mb-1">
                  <span>已摄入 <b>{compensate.today_summary.total_calories}</b> kcal</span>
                  <span>目标 <b>{compensate.today_summary.target_calories}</b> kcal</span>
                </div>
                <div className="h-3 bg-ink-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      compensate.ratio_percent > 100 ? 'bg-red-500' :
                      compensate.ratio_percent > 80 ? 'bg-orange-400' :
                      'bg-brand-500'
                    }`}
                    style={{ width: `${Math.min(compensate.ratio_percent, 100)}%` }}
                  />
                </div>
                <div className="mt-1 text-xs text-ink-500 text-right">
                  剩余 <b className="text-brand-700">{compensate.remaining_budget?.calories || 0}</b> kcal
                </div>
              </div>

              {/* 宏量营养素剩余 */}
              {compensate.remaining_budget && (
                <div className="mt-4 grid grid-cols-3 gap-2">
                  <div className="text-center p-2 bg-white/60 rounded-lg">
                    <div className="text-xs text-ink-500">蛋白质</div>
                    <div className="text-sm font-bold text-blue-600">{compensate.remaining_budget.protein || 0}g</div>
                  </div>
                  <div className="text-center p-2 bg-white/60 rounded-lg">
                    <div className="text-xs text-ink-500">碳水</div>
                    <div className="text-sm font-bold text-amber-600">{compensate.remaining_budget.carbs || 0}g</div>
                  </div>
                  <div className="text-center p-2 bg-white/60 rounded-lg">
                    <div className="text-xs text-ink-500">脂肪</div>
                    <div className="text-sm font-bold text-rose-600">{compensate.remaining_budget.fat || 0}g</div>
                  </div>
                </div>
              )}

              {/* 下一餐建议 */}
              {compensate.next_meal_advice && compensate.next_meal_advice.direction && (
                <div className="mt-4 p-4 bg-white rounded-xl border border-brand-100">
                  <div className="text-sm font-semibold text-brand-700 mb-2">
                    🍽️ 下一餐建议：{compensate.next_meal_advice.direction}
                  </div>
                  <div className="text-xs text-ink-600 mb-2">{compensate.next_meal_advice.reason}</div>
                  {compensate.next_meal_advice.suggested_dishes?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {compensate.next_meal_advice.suggested_dishes.map((d, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-brand-50 text-brand-700 rounded-full">✅ {d}</span>
                      ))}
                    </div>
                  )}
                  {compensate.next_meal_advice.avoid?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {compensate.next_meal_advice.avoid.map((a, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-red-50 text-red-600 rounded-full">❌ {a}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* 今日展望 */}
              {compensate.today_outlook && (
                <div className="mt-3 text-sm text-ink-700 bg-white/60 rounded-lg p-3">
                  <span className="font-medium">📊 今日展望：</span>
                  {compensate.today_outlook.note}
                </div>
              )}

              {/* 明天建议 */}
              {compensate.tomorrow_advice?.needed && (
                <div className="mt-3 text-sm text-ink-700 bg-amber-50 rounded-lg p-3 border border-amber-200">
                  <span className="font-medium">📅 明天调整：</span>
                  {compensate.tomorrow_advice.note}
                </div>
              )}

              {/* 本周趋势 */}
              {compensate.weekly_insight && (
                <div className="mt-3 text-sm text-ink-700 bg-white/60 rounded-lg p-3">
                  <span className="font-medium">📈 本周趋势：</span>
                  {compensate.weekly_insight.note}
                </div>
              )}
            </div>
          )}

          {/* 分享卡片 */}
          {result && result.is_food && (
            <div className="rounded-2xl bg-white border border-ink-200/70 shadow-sm p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-bold text-ink-800">📤 分享分析结果</h3>
                  <p className="mt-1 text-xs text-ink-400">生成一张精美的健康卡片，分享给朋友</p>
                </div>
                <button onClick={generateShareCard}
                  className="px-6 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-brand-600 to-emerald-500 hover:shadow-lg hover:shadow-brand-500/30 transition-all">
                  🖼️ 生成分享卡
                </button>
              </div>
            </div>
          )}

          {/* 分享卡预览弹窗 */}
          {shareOpen && shareImage && (
            <div className="fixed inset-0 z-[60] bg-black/60 flex items-center justify-center p-4" onClick={() => setShareOpen(false)}>
              <div className="bg-white rounded-2xl p-4 max-w-sm w-full" onClick={(e) => e.stopPropagation()}>
                <img src={shareImage} alt="分享卡片" className="w-full rounded-xl" />
                <div className="mt-4 flex gap-2">
                  <a href={shareImage} download="nutrivision-share.png"
                    className="flex-1 text-center px-4 py-3 rounded-xl font-bold text-white bg-brand-600 hover:bg-brand-500 transition">
                    💾 保存图片
                  </a>
                  <button onClick={() => setShareOpen(false)}
                    className="px-4 py-3 rounded-xl font-semibold text-ink-600 bg-ink-100 hover:bg-ink-200 transition">
                    关闭
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 保存历史 */}
          <div className="rounded-2xl bg-white border border-ink-200/70 shadow-sm p-6">
            <h3 className="text-lg font-bold text-ink-800">📅 记入每日计划</h3>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <select value={mealType} onChange={(e) => setMealType(e.target.value)}
                className="px-4 py-2.5 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition bg-white text-sm font-medium">
                {['早餐', '午餐', '晚餐', '加餐', '饮品'].map((m) => <option key={m}>{m}</option>)}
              </select>
              <button onClick={logToday}
                className="px-6 py-2.5 rounded-xl font-semibold text-white bg-gradient-to-r from-brand-600 to-brand-500 hover:shadow-lg hover:shadow-brand-500/30 transition-all">
                ➕ 记入今天（{primaryCal} kcal）
              </button>
              {saved && <span className="text-sm font-medium text-brand-600">✅ 已记入今日</span>}
              <Link to="/plan" className="px-6 py-2.5 rounded-xl font-semibold text-brand-700 bg-brand-50 hover:bg-brand-100 transition">
                查看每日计划 →
              </Link>
              <Link to="/history" className="px-6 py-2.5 rounded-xl font-semibold text-ink-600 bg-ink-100 hover:bg-ink-200 transition">
                全部历史
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* 未检测到食物 */}
      {result && !result.is_food && (
        <div className="mt-10 rounded-2xl bg-orange-50 border border-orange-200 p-6 text-center text-orange-700">
          {result.message || '未检测到食物，请换一张图片试试'}
        </div>
      )}
    </div>
  )
}
