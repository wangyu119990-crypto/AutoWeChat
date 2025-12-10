# -*- coding: utf-8 -*-
# 文件名: test_bot.py
# 这是一个纯测试脚本，运行它来验证自动化功能

import os
from wechat_rpa import WeChatBot

# ================= 配置区 =================
# 1. 这里填一段假的 HTML，或者去你的 output 文件夹里找一个生成的 news.html 用记事本打开复制进来
TEST_HTML = """
<p>大家好，这是自动化发布的测试。</p>
<p style="color:red;">如果你看到这行红字，说明排版保留成功了！</p>
"""

# 2. 这里必须填一个你电脑上真实存在的图片路径！
# 建议直接用你项目里 output 文件夹下的某张图
# 例如: r"C:\你的项目路径\output\cover.jpg" (Windows路径前加r)
# 或者直接写相对路径，如果你的 test_bot.py 和 output 文件夹在同一级
# 确保你的代码里是这一行：
TEST_COVER_PATH = os.path.join("output", "cover.jpg")

# =========================================

def run_test():
    # 检查图片是否存在，不然Playwright会报错
    if not os.path.exists(TEST_COVER_PATH):
        print(f"❌ 错误：找不到测试图片 -> {TEST_COVER_PATH}")
        print("💡 请先去你的网页版生成一张图，或者随便找张图改名为 cover.jpg 放到 output 文件夹里。")
        return

    print("🚀 开始测试自动化机器人...")
    print("----------------------------------")
    
    # 初始化机器人 (headless=False 表示你会看到浏览器弹出来)
    bot = WeChatBot(headless=False)
    
    # 运行发布逻辑
    bot.run_publish(
        title="【测试】这是自动化发布的标题",
        author="INP助手",
        content_html=TEST_HTML,
        cover_path=os.path.abspath(TEST_COVER_PATH) # 转换为绝对路径更稳
    )

if __name__ == "__main__":
    run_test()