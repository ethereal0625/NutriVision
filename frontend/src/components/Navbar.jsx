import { Link, NavLink, useNavigate } from 'react-router-dom'
import { getToken, clearSession, getUser } from '../api.js'

export default function Navbar() {
  const nav = useNavigate()
  const token = getToken()
  const user = getUser()

  const linkCls = ({ isActive }) =>
    `px-3.5 py-2 rounded-full text-sm font-medium transition-all duration-200 ` +
    (isActive
      ? 'bg-brand-600 text-white shadow-sm'
      : 'text-ink-600 hover:text-brand-700')

  const logout = () => {
    clearSession()
    nav('/')
  }

  return (
    <header className="sticky top-0 z-50 bg-[#faf8f4]/85 backdrop-blur-xl border-b border-ink-200/60">
      <nav className="mx-auto max-w-6xl px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-lg font-extrabold tracking-tight text-ink-900">
          <span className="w-8 h-8 rounded-lg bg-brand-600 text-white flex items-center justify-center text-base">🥗</span>
          <span>
            Nutri<span className="text-brand-600">Vision</span>
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-1">
          <NavLink to="/" end className={linkCls}>首页</NavLink>
          <NavLink to="/analyze" className={linkCls}>食物分析</NavLink>
          <NavLink to="/plan" className={linkCls}>每日计划</NavLink>
          <NavLink to="/history" className={linkCls}>历史记录</NavLink>
          <NavLink to="/tips" className={linkCls}>健康科普</NavLink>
          <NavLink to="/profile"
            className={({ isActive }) =>
              `px-3.5 py-2 rounded-full text-sm font-semibold transition-all duration-200 ` +
              (isActive
                ? 'bg-accent-500 text-white shadow-sm'
                : 'text-accent-600 bg-accent-50 hover:bg-accent-100')}>
            👤 个人中心
          </NavLink>
        </div>

        <div className="flex items-center gap-1.5">
          {token && user ? (
            <div className="flex items-center gap-1.5">
              <span className="hidden sm:flex items-center gap-2 pl-1 pr-3 py-1.5 rounded-full text-sm font-medium text-ink-600">
                <span className="w-7 h-7 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-xs font-bold">
                  {user.username.slice(0, 1).toUpperCase()}
                </span>
                {user.username}
              </span>
              <button onClick={logout}
                className="px-3 py-2 rounded-full text-sm font-medium text-ink-500 hover:text-red-600 transition">
                退出
              </button>
            </div>
          ) : (
            <>
              <Link to="/login" className="px-3.5 py-2 rounded-full text-sm font-medium text-ink-600 hover:text-brand-700 transition">
                登录
              </Link>
              <Link to="/register"
                className="px-4 py-2 rounded-full text-sm font-semibold text-white bg-brand-600 hover:bg-brand-500 transition-all">
                免费注册
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}
