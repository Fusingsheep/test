import sys
import asyncio

# ==========================================
# 1. 强制 Windows 使用支持子进程的事件循环
# ==========================================
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 2. 正常的导入
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from playwright.async_api import async_playwright, Browser

# 全局变量
browser_instance: Browser = None
playwright_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global browser_instance, playwright_instance
    print(">>> 正在启动 Playwright 浏览器内核...")
    try:
        playwright_instance = await async_playwright().start()
        # 启动浏览器
        browser_instance = await playwright_instance.chromium.launch(headless=True)
        print(">>> 浏览器内核启动成功！")
    except Exception as e:
        print(f"!!! 浏览器启动失败: {e}")
        raise e
        
    yield
    
    print(">>> 正在关闭浏览器内核...")
    if browser_instance:
        await browser_instance.close()
    if playwright_instance:
        await playwright_instance.stop()

app = FastAPI(lifespan=lifespan, title="HTML to PDF API")

@app.post("/convert")
async def convert_html_to_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(('.html', '.htm')):
        raise HTTPException(status_code=400, detail="仅支持 .html 文件")

    context = None
    page = None
    try:
        content = await file.read()
        html_content = content.decode("utf-8")

        # 创建页面
        context = await browser_instance.new_context()
        page = await context.new_page()

        # 渲染
        await page.set_content(html_content, wait_until="networkidle")

        # 导出 PDF
        pdf_bytes = await page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"}
        )
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=output.pdf"}
        )

    except Exception as e:
        print(f"转换出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 确保资源释放，防止内存泄漏
        if page: await page.close()
        if context: await context.close()

if __name__ == "__main__":
    # ==========================================
    # 3. 关键修改：reload 必须设为 False
    # Windows 下 Playwright 不支持 Uvicorn 的热重载模式
    # ==========================================
    print("正在启动服务 (注意：Windows下必须关闭 reload 模式)...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)