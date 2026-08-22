import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, setSession } from '../api.js'

export default function Login() {
  const nav = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const res = await api.login(username.trim(), password)
      setSession(res.access_token, res.username)
      nav('/analyze')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-md px-6 py-20">
      <div className="rounded-3xl bg-white border border-ink-200/70 shadow-xl shadow-brand-900/5 p-8">
        <div className="text-center mb-8">
          <div className="text-4xl">🥗</div>
          <h1 className="mt-3 text-2xl font-black text-ink-800">欢迎回来</h1>
          <p className="mt-1 text-sm text-ink-500">登录 NutriVision，继续你的健康饮食之旅</p>
        </div>
        {error && <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 text-red-600 text-sm">{error}</div>}
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-ink-600 mb-1.5">用户名</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} required
              className="w-full px-4 py-3 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition"
              placeholder="请输入用户名" />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink-600 mb-1.5">密码</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
              className="w-full px-4 py-3 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition"
              placeholder="请输入密码" />
          </div>
          <button type="submit" disabled={loading}
            className="w-full py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-brand-600 to-brand-500 hover:shadow-lg hover:shadow-brand-500/30 disabled:opacity-60 transition-all">
            {loading ? '登录中...' : '登 录'}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-ink-500">
          还没有账号？
          <Link to="/register" className="font-semibold text-brand-600 hover:text-brand-700"> 免费注册</Link>
        </p>
      </div>
    </div>
  )
}
