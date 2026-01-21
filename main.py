import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- 設定區 (精選穩定來源: 14 個) ---
news_sources = [
    # === 美洲 ===
    { "name": "AP News (美聯社)", "url": "https://apnews.com/hub/world-news", "tag": "h3", "root": "https://apnews.com" },
    { "name": "CNN", "url": "https://edition.cnn.com/world", "tag": "span", "root": "https://edition.cnn.com" },
    { "name": "NPR (美國公共廣播)", "url": "https://www.npr.org/sections/news/", "tag": "h2", "root": "" },
    { "name": "The New York Times (紐約時報)", "url": "https://www.nytimes.com/section/world", "tag": "h3", "root": "https://www.nytimes.com" },
    
    # === 歐洲 ===
    { "name": "BBC News (英國)", "url": "https://www.bbc.com/news", "tag": "h2", "root": "https://www.bbc.com" },
    { "name": "The Guardian (衛報)", "url": "https://www.theguardian.com/international", "tag": "h3", "root": "" },
    { "name": "Deutsche Welle (德國之聲)", "url": "https://www.dw.com/en/top-stories/s-9097", "tag": "h3", "root": "https://www.dw.com" },
    { "name": "France 24 (法國)", "url": "https://www.france24.com/en/", "tag": "p", "root": "https://www.france24.com" }, # 新增替代來源
    { "name": "El País (西班牙)", "url": "https://english.elpais.com/", "tag": "h2", "root": "https://english.elpais.com" },

    # === 亞洲與中東 ===
    { "name": "Al Jazeera (半島電視台)", "url": "https://www.aljazeera.com/news/", "tag": "h3", "root": "https://www.aljazeera.com" },
    { "name": "The Japan Times (日本時報)", "url": "https://www.japantimes.co.jp/news/world/", "tag": "h3", "root": "" }, # 新增替代來源
    { "name": "SCMP (南華早報)", "url": "https://www.scmp.com/news/world", "tag": "h2", "root": "https://www.scmp.com" },
    { "name": "Xinhua (新華社)", "url": "https://english.news.cn/", "tag": "span", "root": "" },

    # === 科學 ===
    { "name": "Nature (科學期刊)", "url": "https://www.nature.com/news", "tag": "h3", "root": "" }
]

translator = GoogleTranslator(source='auto', target='zh-TW')

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

# 全域變數：用來累積所有要寄出的內容
full_content = ""

def log_and_save(text):
    """ 同時打印到螢幕、寫入檔案、並存入 Email 內容緩衝區 """
    global full_content
    print(text)
    full_content += text + "\n"
    with open("news_report.txt", "a", encoding="utf-8") as file:
        file.write(text + "\n")

# --- 寄信功能 ---
def send_email_report():
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')

    if not email_user or not email_password:
        print("⚠️ 找不到 Email 設定，跳過寄信步驟。")
        return

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_user  # 寄給自己
    msg['Subject'] = f"📰 每日新聞快報 ({datetime.now().strftime('%Y-%m-%d')})"

    # 將內容轉為 HTML 格式稍微美化一下
    html_content = f"""
    <html>
      <body>
        <h2>🌍 你的每日重點新聞</h2>
        <pre style="font-family: Arial; font-size: 14px;">{full_content}</pre>
        <hr>
        <p>Sent by Daily News Bot 🤖</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))

    try:
        # 連線到 Gmail 伺服器
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()
        print("\n📧 Email 寄送成功！請檢查收件匣。")
    except Exception as e:
        print(f"\n❌ Email 寄送失敗: {e}")

# --- 主程式 ---
# 清空舊檔
with open("news_report.txt", "w", encoding="utf-8") as file:
    file.write("")

log_and_save(f"=== 每日重點新聞彙整 ===\n時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

# 開始抓取
for source in news_sources:
    site_name = source["name"]
    url = source["url"]
    tag = source["tag"]
    root_url = source["root"]
    
    log_and_save(f"🚀 {site_name}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            items = []

            if site_name == "CNN":
                items = soup.find_all("span", class_="container__headline-text") or soup.find_all("span")
            elif site_name == "Xinhua (新華社)":
                items = soup.find_all("div", class_="tit") or soup.find_all("span")
            elif site_name == "Nikkei Asia (日經)":
                 items = soup.find_all("h4")
            else:
                items = soup.find_all(tag)
            
            count = 0
            seen = set()
            
            for item in items:
                if count >= 5: break
                
                link = item.find_parent("a") or item.find("a") if tag in ["h2","h3","h4","span","div"] else item
                
                txt = item.get_text(strip=True) or (link.get_text(strip=True) if link else "")
                
                if txt and len(txt) > 10 and txt not in seen:
                    seen.add(txt)
                    try:
                        zh_txt = translator.translate(txt)
                    except:
                        zh_txt = txt
                    
                    link_url = link.get("href") if link else ""
                    if link_url and not link_url.startswith("http"):
                        link_url = root_url + link_url
                    
                    log_and_save(f"   📰 {zh_txt}")
                    log_and_save(f"   🔗 {link_url}\n")
                    count += 1
            
            if count == 0: log_and_save("   ⚠️ 未抓到新聞")
        else:
            log_and_save(f"   ❌ 連線失敗: {response.status_code}")
            
    except Exception as e:
        log_and_save(f"   ❌ 錯誤: {e}")
    
    log_and_save("-" * 30)
    time.sleep(1)

# 最後寄出 Email
send_email_report()
print("💤 任務全部完成！")
