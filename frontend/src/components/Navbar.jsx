import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { getToken, clearSession, getUser } from '../api.js'

export default function Navbar() {
  const nav = useNavigate()
  const location = useLocation()
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

  // 底部 Tab 配置（仅移动端显示）
  const tabs = [
    { to: '/', icon: '🏠', label: '首页', end: true },
    { to: '/analyze', icon: '📸', label: '分析', end: false },
    { to: '/plan', icon: '📋', label: '计划', end: false },
    { to: '/history', icon: '📅', label: '记录', end: false },
    { to: '/water', icon: '💧', label: '饮水', end: false },
    { to: '/profile', icon: '👤', label: '我的', end: false },
  ]

  // 登录/注册页不显示底部 Tab
  const hideTabs = ['/login', '/register'].includes(location.pathname)

  return (
    <>
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-50 bg-[#faf8f4]/85 backdrop-blur-xl border-b border-ink-200/60">
        <nav className="mx-auto max-w-6xl px-4 sm:px-6 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-lg font-extrabold tracking-tight text-ink-900">
            <span className="w-8 h-8 rounded-lg bg-brand-600 text-white flex items-center justify-center text-base">🥗</span>
            <span className="hidden sm:inline">
              Nutri<span className="text-brand-600">Vision</span>
            </span>
          </Link>

          {/* 桌面端导航 */}
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

          {/* 桌面端用户信息 */}
          <div className="hidden md:flex items-center gap-1.5">
            {token && user ? (
              <div className="flex items-center gap-1.5">
                <span className="flex items-center gap-2 pl-1 pr-3 py-1.5 rounded-full text-sm font-medium text-ink-600">
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

          {/* 移动端：顶部简洁标题 */}
          <div className="flex md:hidden items-center gap-2">
            <span className="text-base font-bold text-ink-800">
              Nutri<span className="text-brand-600">Vision</span>
            </span>
          </div>
          <div className="flex md:hidden items-center">
            {token && user ? (
              <button onClick={logout}
                className="px-2.5 py-1.5 rounded-full text-xs font-medium text-ink-500 hover:text-red-600 transition">
                退出
              </button>
            ) : (
              <Link to="/login" className="px-3 py-1.5 rounded-full text-xs font-medium text-brand-600 border border-brand-200">
                登录
              </Link>
            )}
          </div>
        </nav>
      </header>

      {/* 底部 Tab 栏（移动端） */}
      {!hideTabs && (
        <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-xl border-t border-ink-200/60"
          style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}>
          <div className="flex items-center justify-around h-14">
            {tabs.map((tab) => (
              <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.end}
                className={({ isActive }) =>
                  `flex flex-col items-center justify-center gap-0.5 w-full h-full transition-colors ` +
                  (isActive ? 'text-brand-600' : 'text-ink-400')
                }
              >
                <span className="text-xl leading-none">{tab.icon}</span>
                <span className="text-[10px] font-medium leading-none">{tab.label}</span>
              </NavLink>
            ))}
          </div>
        </nav>
      )}
    </>
  )
}