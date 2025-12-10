# -*- coding: utf-8 -*-
# 文件名: wechat_rpa.py (V24 强力同步修复版)
from playwright.sync_api import sync_playwright
import time
import re
import os
import sys

# ================= 配置区域 (同步版) =================
PROJECT_DIR = "/Users/wangyu/AutoWeChat" # 假设 PROJECT_DIR 在这里定义
NEWS_HTML_PATH = os.path.join(PROJECT_DIR, "output", "news.html")


class WeChatBot:
    def __init__(self, headless=False):
        pass

    def run_publish(self, title, author, content_html, cover_path):
        """主发布流程 (包含 V24 强力修复逻辑)"""
        html_path = NEWS_HTML_PATH # 使用全局配置的路径
        if not os.path.exists(html_path):
            print("❌ 错误: 找不到 news.html")
            return

        print(f"🤖 机器人启动 (V24 强力同步修复版) | 目标文件: {html_path}")
        
        with sync_playwright() as p:
            try:
                print("🔌 连接 Chrome (9222)...")
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                context = browser.contexts[0]
                
                # 1. 强制跳转编辑器 (同步版)
                wechat_page = None
                for page in context.pages:
                    if "mp.weixin.qq.com" in page.url:
                        wechat_page = page
                        break
                if not wechat_page:
                    wechat_page = context.new_page()
                    wechat_page.goto("https://mp.weixin.qq.com/")

                page = wechat_page
                if "media/appmsg_edit_v2" not in page.url:
                    if "token=" not in page.url:
                        page.goto("https://mp.weixin.qq.com/")
                        page.wait_for_url(lambda u: "token=" in u, timeout=10000)
                    token = re.search(r'token=(\d+)', page.url).group(1)
                    page.goto(f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=0&token={token}&lang=zh_CN")

                print("⏳ 等待编辑器加载...")
                page.wait_for_selector("#title", state="visible", timeout=30000)
                time.sleep(2)

                # 2. 复制内容
                print("📑 复制完整正文...")
                file_url = f"file://{html_path}"
                source_page = context.new_page()
                source_page.goto(file_url)
                time.sleep(1)
                source_page.keyboard.press("Meta+A")
                time.sleep(0.5)
                source_page.keyboard.press("Meta+C")
                time.sleep(1)
                source_page.close()
                page.bring_to_front()

                # 3. 移除遮罩，填写标题作者
                print("🛡️ 移除遮罩...")
                # 移除遮罩，防弹窗干扰
                page.evaluate("document.querySelectorAll('.media_list_box_mask, .weui-desktop-mask').forEach(e => e.remove());")
                page.locator("#title").fill(title)
                page.locator("#author").fill(author)
                
                # 4. 清空摘要 - 💥 强力清空修复
                print("🧹 清空摘要 (JS Focus + 键盘)...")
                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(0.5)
                    sel = "#digest" 
                    page.evaluate(f"document.querySelector('{sel}').focus()") # JS 强制聚焦
                    time.sleep(0.2)
                    page.locator(sel).click()
                    page.keyboard.press("Meta+A")
                    time.sleep(0.2)
                    page.keyboard.press("Backspace")
                    page.keyboard.press("Backspace") 
                    print("✅ 摘要已物理清空")
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(1)
                except Exception as e:
                    print(f"⚠️ 摘要清空失败: {e}")
                    page.evaluate("window.scrollTo(0, 0)")

                # 5. 粘贴正文
                print("🖱️ 粘贴正文...")
                page.locator("#author").click()
                page.keyboard.press("Tab")
                time.sleep(0.5)
                page.keyboard.type("x") 
                time.sleep(0.2)
                page.keyboard.press("Meta+A")
                page.keyboard.press("Meta+V")
                print("✅ 粘贴完成")
                time.sleep(3)


                # 6. 插入 '快讯模板' (或名片) - 💥 强力点击修复
                print("📋 插入 '快讯模板' (强力点击)...")
                try:
                    page.evaluate("document.querySelectorAll('.media_list_box_mask').forEach(e => e.remove())")
                    
                    # 尝试点击 '模板' 按钮
                    template_btn = page.get_by_text("模板", exact=True).first
                    template_btn.click()
                    
                    dialog = page.locator(".weui-desktop-dialog__wrp")
                    dialog.wait_for(state="visible", timeout=10000)
                    time.sleep(2.5) 

                    # 寻找包含 '快讯' 的列表项
                    target_item = dialog.locator("li").filter(has_text="快讯").first
                    
                    if target_item.count() > 0:
                        # 强制点击元素中心
                        target_item.click(force=True, position={"x": 50, "y": 50}) 
                        print("✅ 已点击快讯模版")
                        
                        try:
                            dialog.wait_for(state="hidden", timeout=5000)
                        except:
                            page.keyboard.press("Escape")
                            print("⚠️ 弹窗未自动关闭，按 ESC 关闭")
                    else:
                        print("❌ 未找到包含'快讯'的模版")

                except Exception as e:
                    print(f"❌ 模版操作异常: {e}")
                
                
                # 7. 设置封面 - 💥 鼠标轨迹修复
                print("🖼️ 设置封面 (鼠标轨迹模拟)...")
                try:
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(1)
                    
                    cover_area = page.locator(".js_cover_btn_area").first
                    
                    # 模拟真实鼠标移动
                    box = cover_area.bounding_box()
                    if box:
                        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                        time.sleep(0.5) 
                        page.mouse.move(box["x"] + box["width"] / 2 + 5, box["y"] + box["height"] / 2 + 5)
                        time.sleep(0.5)
                    else:
                        cover_area.hover()
                        time.sleep(1)

                    # 寻找并点击 "从正文选择"
                    target_btn = page.get_by_text("从正文选择").first
                    
                    if target_btn.is_visible():
                        print("   -> 发现'从正文选择'按钮，点击中...")
                        target_btn.click(force=True)
                    else:
                        print("❌ 找不到'从正文选择'按钮")
                        raise Exception("按钮不可见")

                    # 处理图片选择弹窗
                    page.wait_for_selector(".weui-desktop-dialog", timeout=3000)
                    
                    imgs = page.locator(".weui-desktop-img-picker__list .weui-desktop-img-picker__item")
                    count = imgs.count()
                    
                    if count > 0:
                        imgs.nth(count - 1).click() # 点击最后一张
                        time.sleep(0.5)
                        
                        if page.locator("button:has-text('下一步')").is_visible():
                            page.locator("button:has-text('下一步')").click()
                            time.sleep(0.5)
                            
                        page.locator("button:has-text('完成')").click()
                        print("✅ 封面已选定最后一张图")
                    else:
                        print("⚠️ 弹窗内无图片")
                except Exception as e:
                    print(f"❌ 封面设置异常: {e}")


                # 8. 底部配置 (合集等，保持旧逻辑但移除名片/模版/摘要/封面逻辑)
                print("⚙️ 底部配置...")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)

                # ... (这里放您原 wechat_rpa.py 中 step 8 的逻辑)
                # 例如：原创、留言、合集等逻辑，从您的旧 wechat_rpa.py 中移植过来
                
                print("\n✅✅✅ V24 流程结束！")

            except Exception as e:
                print(f"❌ 错误: {e}")
                import traceback
                traceback.print_exc()

# 示例：如果您需要一个入口来调用它
if __name__ == "__main__":
    bot = WeChatBot()
    # 假设这是您调用 run_publish 的地方，需要提供参数
    # bot.run_publish(title="测试标题", author="INP Family", content_html="", cover_path="")
    print("请通过您的主程序或 server.py 调用 WeChatBot.run_publish")