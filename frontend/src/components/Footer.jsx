import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="mt-24 border-t border-ink-200 bg-white/60">
      <div className="mx-auto max-w-6xl px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-ink-500">
        <div className="flex items-center gap-2">
          <span className="text-xl">🥗</span>
          <span className="font-semibold text-ink-700">NutriVision · AI 健康饮食改造师</span>
        </div>
        <div className="flex items-center gap-5">
          <Link to="/about" className="hover:text-brand-700 transition">关于</Link>
          <Link to="/tips" className="hover:text-brand-700 transition">健康科普</Link>
        </div>
        <p>© 2026 NutriVision · 拍一张照片，让 AI 帮你把菜"改健康"</p>
      </div>
    </footer>
  )
}
