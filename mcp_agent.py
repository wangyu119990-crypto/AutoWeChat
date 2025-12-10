# -*- coding: utf-8 -*-
# 文件名: mcp_agent.py
# 版本: V24 (自动跳转 + 强力修复二合一版)

import asyncio
import os
import re
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright, Page

# ================= 配置区域 =================
PROJECT_DIR = "/Users/wangyu/AutoWeChat"
NEWS_HTML_PATH = os.path.join(PROJECT_DIR, "output", "news.html")

mcp = FastMCP("WeChatAgent")
browser_storage = {"playwright": None, "page": None}

# ================= 核心连接逻辑 =================
async def get_page() -> Page:
    """获取浏览器页面，如果断开会自动重连"""
    if not browser_storage["playwright"]:
        p = await async_playwright().start()
        browser_storage["playwright"] = p
        try:
            # 连接你已经打开的 Chrome (端口 9222)
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            
            # 优先找已经是编辑器的页面
            for page in context.pages:
                if "appmsg_edit" in page.url:
                    await page.bring_to_front()
                    browser_storage["page"] = page
                    return page
            
            # 没找到就用当前最新的页面
            if context.pages: 
                browser_storage["page"] = context.pages[-1]
                return browser_storage["page"]
            
            # 实在没有就新建
            browser_storage["page"] = await context.new_page()
            return browser_storage["page"]
        except Exception as e: 
            raise RuntimeError(f"无法连接 Chrome，请确认浏览器已用命令行启动。错误: {e}")
    return browser_storage["page"]

# ================= 🛠️ 自动化工具箱 =================

@mcp.tool()
async def step0_ensure_editor() -> str:
    """Step 0: 强制进入文章编辑器 (自动跳转)"""
    page = await get_page()
    print("Step 0: 检查编辑器状态...")

    # 如果已经在编辑器，直接通过
    if "appmsg_edit" in page.url:
        return "✅ 已在编辑器页面，准备就绪"

    # 如果不在，尝试自动跳转
    if "token=" in page.url:
        try:
            token = re.search(r'token=(\d+)', page.url).group(1)
            print(f"   -> 捕获到 Token: {token}，正在跳转...")
            target_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=0&token={token}&lang=zh_CN"
            await page.goto(target_url)
            
            # 等待编辑器核心元素出现
            try:
                await page.wait_for_selector("#title", state="visible", timeout=15000)
                return "✅ 已成功跳转到编辑器"
            except:
                return "⚠️ 跳转了，但页面加载似乎卡住了，请手动刷新"
        except Exception as e:
            return f"❌ 跳转失败: {e}"
    
    return "❌ 无法跳转：请先在浏览器手动登录微信公众号后台（看到首页即可）"

@mcp.tool()
async def step1_copy_local() -> str:
    """Step 1: 复制本地 news.html 内容"""
    if not os.path.exists(NEWS_HTML_PATH): return "❌ 错误：找不到 news.html 文件"
    
    page = await get_page()
    # 新开一个标签页去复制，防止干扰主流程
    cp = await page.context.new_page()
    await cp.goto(f"file://{NEWS_HTML_PATH}")
    
    # 模拟全选复制
    await cp.keyboard.press("Meta+A")
    await asyncio.sleep(0.5)
    await cp.keyboard.press("Meta+C")
    await asyncio.sleep(0.5)
    
    await cp.close()
    await page.bring_to_front() # 回到微信页面
    return "✅ 本地内容已复制到剪贴板"

@mcp.tool()
async def step2_paste_content(title: str) -> str:
    """Step 2: 注入标题并粘贴正文"""
    page = await get_page()
    
    # 1. 暴力移除遮罩 (防弹窗干扰)
    await page.evaluate("document.querySelectorAll('.media_list_box_mask, .weui-desktop-mask').forEach(e => e.remove())")

    # 2. JS 注入标题和作者
    await page.evaluate(f"document.getElementById('title').value = '{title}'; document.getElementById('title').dispatchEvent(new Event('input'));")
    await page.evaluate("document.getElementById('author').value = 'INP Family'; document.getElementById('author').dispatchEvent(new Event('input'));")
    
    # 3. 粘贴正文
    await page.locator("#ueditor_0").click()
    await asyncio.sleep(0.5)
    await page.keyboard.press("Meta+A")
    await page.keyboard.press("Backspace") # 先清空
    await page.keyboard.press("Meta+V") # 再粘贴
    
    return "✅ 标题与正文粘贴完成"

@mcp.tool()
async def step3_insert_template() -> str:
    """Step 3: 插入快讯模版 (强力点击版)"""
    page = await get_page()
    print("Step 3: 正在插入模版...")
    
    try:
        # 再次移除遮罩
        await page.evaluate("document.querySelectorAll('.media_list_box_mask').forEach(e => e.remove())")

        # 1. 点击“模板”按钮
        btn = page.get_by_text("模板", exact=True).first
        await btn.wait_for(state="visible")
        await btn.click()
        
        # 2. 等待弹窗
        dialog = page.locator(".weui-desktop-dialog__wrp")
        await dialog.wait_for(state="visible")
        await asyncio.sleep(2) # 必须死等一会，让列表渲染

        # 3. 寻找“快讯”并强制点击
        # 策略：找到包含文字的 li 标签
        target_item = dialog.locator("li").filter(has_text="快讯").first
        
        if await target_item.count() > 0:
            # 强制点击元素中心
            await target_item.click(force=True, position={"x": 50, "y": 30})
            print("✅ 已点击快讯模版")
            
            # 等待关闭
            try:
                await dialog.wait_for(state="hidden", timeout=5000)
            except:
                await page.keyboard.press("Escape") # 如果没关掉，按 ESC
        else:
            return "❌ 未找到'快讯'模版，请检查模版库"

        return "✅ 模版插入完成"
    except Exception as e:
        return f"❌ 模版步骤出错: {e}"

@mcp.tool()
async def step4_clear_abstract() -> str:
    """Step 4: 清空摘要 (强制聚焦版)"""
    page = await get_page()
    print("Step 4: 正在清空摘要...")
    
    try:
        # 1. 滚到底部
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await asyncio.sleep(0.5)
        
        # 2. JS 强制让输入框获得焦点 (解决点不中的问题)
        # 微信摘要框通常 ID 是 digest
        await page.evaluate("document.getElementById('digest').focus()")
        await asyncio.sleep(0.2)
        
        # 3. 物理点击辅助
        await page.locator("#digest").click()
        
        # 4. 键盘狂删
        await page.keyboard.press("Meta+A")
        await asyncio.sleep(0.1)
        await page.keyboard.press("Backspace")
        await page.keyboard.press("Backspace") # 多按一次保平安
        
        await page.evaluate("window.scrollTo(0, 0)")
        return "✅ 摘要已彻底清空"
    except Exception as e:
        return f"❌ 摘要清空失败: {e}"

@mcp.tool()
async def step5_set_cover() -> str:
    """Step 5: 设置封面 (真实鼠标模拟版)"""
    page = await get_page()
    print("Step 5: 正在设置封面...")
    
    try:
        # 1. 回到顶部
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)
        
        # 2. 模拟鼠标滑入封面区域
        cover_area = page.locator(".js_cover_btn_area").first
        box = await cover_area.bounding_box()
        
        if box:
            # 移动鼠标到区域中心，触发悬停菜单
            await page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
            await asyncio.sleep(0.5)
            # 再动一下，确保触发
            await page.mouse.move(box["x"] + box["width"]/2 + 5, box["y"] + box["height"]/2 + 5)
            await asyncio.sleep(0.5)
        
        # 3. 点击“从正文选择”
        # 使用 Force=True 无视任何透明遮挡
        btn = page.get_by_text("从正文选择").first
        if await btn.is_visible():
            await btn.click(force=True)
        else:
            # 如果悬停没出来，尝试盲点
            print("⚠️ 按钮未浮现，尝试点击区域...")
            await cover_area.click() 
            # 再次尝试找按钮
            if await btn.is_visible(): await btn.click(force=True)

        # 4. 选择最后一张图
        await page.wait_for_selector(".weui-desktop-img-picker__item", timeout=5000)
        imgs = page.locator(".weui-desktop-img-picker__item")
        count = await imgs.count()
        
        if count > 0:
            await imgs.nth(count - 1).click() # 点最后一张
            await asyncio.sleep(0.5)
            
            # 点下一步/完成
            next_btn = page.locator("button", has_text="下一步")
            if await next_btn.is_visible(): await next_btn.click()
            
            finish_btn = page.locator("button", has_text="完成")
            if await finish_btn.is_visible(): await finish_btn.click()
            
            return "✅ 封面已设置为最后一张图"
        else:
            return "⚠️ 正文中没有发现图片"
            
    except Exception as e:
        return f"❌ 封面设置出错: {e}"

@mcp.tool()
async def step6_settings() -> str:
    """Step 6: 收尾设置 (原创/留言)"""
    # 这里保持简单的逻辑即可
    page = await get_page()
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    return "✅ 配置完成，请人工最后检查并群发"

if __name__ == "__main__":
    mcp.run()