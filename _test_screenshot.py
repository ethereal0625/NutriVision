import asyncio
from playwright.async_api import async_playwright

async def screenshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})
        
        # 登录
        await page.goto('http://localhost:5173/login')
        await page.wait_for_timeout(1000)
        await page.fill('input[placeholder="请输入用户名"]', 'user887840')
        await page.fill('input[placeholder="请输入密码"]', 'demo123456')
        await page.click('button[type=submit]')
        await page.wait_for_timeout(2000)
        
        pages = [
            ('home', '/'),
            ('analyze', '/analyze'),
            ('plan', '/plan'),
            ('water', '/water'),
            ('profile', '/profile'),
            ('history', '/history'),
            ('tips', '/tips'),
        ]
        
        for name, path in pages:
            await page.goto(f'http://localhost:5173{path}')
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f'D:/VLP/handoff/preview/test_{name}.png', full_page=True)
            print(f'[OK] {name}')
        
        await browser.close()
        print('All done!')

asyncio.run(screenshot())