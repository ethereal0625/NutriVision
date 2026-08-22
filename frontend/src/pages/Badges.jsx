import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, getToken } from '../api.js'

export default function Badges() {
  const nav = useNavigate()
  const [token] = useState(getToken())
  const [badges, setBadges] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) { nav('/login'); return }
    api.getBadges()
      .then(setBadges)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [token])

  if (loading) return <div className="py-24 text-center text-ink-400">加载中...</div>

  const unlockedCount = badges.filter((b) => b.unlocked).length

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 py-8 pb-24 md:pb-10">
      {/* 标题 */}
      <div className="text-center mb-6">
        <h1 className="text-2xl sm:text-3xl font-black text-ink-800">🏆 成就徽章墙</h1>
        <p className="mt-1 text-sm text-ink-500">坚持记录，点亮属于你的每一枚徽章</p>
      </div>

      {error && (
        <div className="mb-6 px-4 py-3 rounded-xl bg-red-50 text-red-600 text-sm">{error}</div>
      )}

      {/* 已解锁统计 */}
      <div className="rounded-2xl bg-gradient-to-br from-[#2e8b57] to-emerald-800 text-white p-6 sm:p-7 mb-6 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="text-sm opacity-85">已解锁成就</div>
            <div className="mt-1 text-4xl sm:text-5xl font-black">
              {unlockedCount}
              <span className="text-xl sm:text-2xl font-bold opacity-80 ml-1">/ {badges.length}</span>
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl sm:text-4xl">
              {unlockedCount === badges.length ? '🌟' : unlockedCount > 0 ? '💪' : '🚀'}
            </div>
            <div className="text-xs opacity-85 mt-1">
              {unlockedCount === badges.length ? '全部达成' : unlockedCount > 0 ? '继续加油' : '开始记录'}
            </div>
          </div>
        </div>
        <div className="mt-5 h-2.5 bg-white/25 rounded-full overflow-hidden">
          <div
            className="h-full bg-white rounded-full transition-all duration-700"
            style={{ width: `${badges.length ? (unlockedCount / badges.length) * 100 : 0}%` }}
          />
        </div>
      </div>

      {/* 徽章网格 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {badges.map((badge) => (
          <div
            key={badge.id}
            className={`rounded-2xl p-5 border transition-all ${
              badge.unlocked
                ? 'bg-white border-[#2e8b57]/25 shadow-sm'
                : 'bg-white/70 border-ink-200/70'
            }`}
          >
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center text-3xl mb-4 ${
                badge.unlocked
                  ? 'bg-gradient-to-br from-[#2e8b57] to-emerald-600 shadow-md shadow-[#2e8b57]/20'
                  : 'bg-ink-100'
              }`}
            >
              <span className={badge.unlocked ? '' : 'opacity-45'}>{badge.icon}</span>
            </div>
            <h3 className={`font-bold ${badge.unlocked ? 'text-ink-800' : 'text-ink-400'}`}>
              {badge.name}
            </h3>
            <p className={`mt-1.5 text-sm leading-relaxed ${badge.unlocked ? 'text-ink-500' : 'text-ink-400'}`}>
              {badge.desc}
            </p>
            <div
              className={`mt-4 pt-3 border-t text-xs font-medium ${
                badge.unlocked
                  ? 'border-[#2e8b57]/15 text-[#2e8b57]'
                  : 'border-ink-100 text-ink-400'
              }`}
            >
              {badge.unlocked ? `🗓️ ${badge.unlocked_at || '已解锁'}` : '🔒 未解锁'}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
