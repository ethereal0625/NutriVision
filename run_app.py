"""
run_app.py - NutriVision「手机 App 模式」启动器

做什么：
1. 把 Streamlit 的 index.html 换成带 PWA 注入的自定义版本
   （manifest / service worker / 图标 / 全屏 meta），使网页可安装到
   手机主屏幕、以全屏 App 方式运行；
2. 以 0.0.0.0 启动服务，手机与电脑同一 WiFi 即可通过「网络 URL」访问。

用法：python run_app.py   （或双击 启动NutriVision.bat）
"""
import os
import shutil
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PWA_DIR = APP_DIR / "pwa"
CUSTOM_STATIC = APP_DIR / ".app_static"

_PWA_FILES = (
    "manifest.webmanifest",
    "sw.js",
    "icon-192.png",
    "icon-512.png",
    "maskable-icon-192.png",
    "maskable-icon-512.png",
    "apple-touch-icon.png",
)

_HEAD_INJECT = """<!-- nutrivision-pwa -->
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#2e8b57">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="AI 健康饮食改造师">
<link rel="apple-touch-icon" href="/icon-192.png">
<link rel="icon" type="image/png" href="/icon-192.png">
"""

_SW_INJECT = (
    '<script>'
    'if("serviceWorker" in navigator){'
    'window.addEventListener("load",function(){'
    'navigator.serviceWorker.register("/sw.js").catch(function(e){console.warn("SW register failed", e)});'
    '})}'
    '</script>'
)


def _build_custom_static() -> Path:
    import streamlit.file_util as _fu

    package_static = Path(_fu.get_static_dir())
    if not CUSTOM_STATIC.exists():
        shutil.copytree(
            package_static,
            CUSTOM_STATIC,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    index = CUSTOM_STATIC / "index.html"
    if not index.exists():
        shutil.copy2(package_static / "index.html", index)

    html = index.read_text(encoding="utf-8")
    if "nutrivision-pwa" not in html:
        # 视图缩放适配刘海屏
        html = html.replace(
            'content="width=device-width, initial-scale=1, shrink-to-fit=no"',
            'content="width=device-width, initial-scale=1, shrink-to-fit=no, viewport-fit=cover"',
        )
        html = html.replace("</head>", _HEAD_INJECT + "</head>")
        html = html.replace("</body>", _SW_INJECT + "</body>")
        index.write_text(html, encoding="utf-8")
        print("[PWA] 已向 index.html 注入 PWA 头部")
    else:
        print("[PWA] index.html 已包含 PWA 注入，跳过")

    # 复制 PWA 资源到自定义静态目录根
    for fname in _PWA_FILES:
        src = PWA_DIR / fname
        if src.exists():
            shutil.copy2(src, CUSTOM_STATIC / fname)

    # 苹果触摸图标：直接用 192 图标
    if not (CUSTOM_STATIC / "apple-touch-icon.png").exists() and (PWA_DIR / "icon-192.png").exists():
        shutil.copy2(PWA_DIR / "icon-192.png", CUSTOM_STATIC / "apple-touch-icon.png")

    return CUSTOM_STATIC


def main() -> None:
    import streamlit.config as _config
    import streamlit.file_util as _fu
    from streamlit.web import bootstrap

    custom_static = _build_custom_static()
    # 让 Streamlit 从自定义静态目录提供页面（含 PWA 注入）
    _fu.get_static_dir = lambda: str(custom_static)

    os.chdir(APP_DIR)
    main_script = str(APP_DIR / "app.py")
    _config._main_script_path = main_script

    flag_options = {
        "server.port": 8501,
        "server.headless": True,
        "server.runOnSave": True,
        "browser.gatherUsageStats": False,
    }
    bootstrap.load_config_options(flag_options=flag_options)
    bootstrap.run(main_script, False, [], flag_options)


if __name__ == "__main__":
    main()
