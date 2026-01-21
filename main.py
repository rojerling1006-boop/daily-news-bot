import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import time 

# --- 設定區 (精選 16 個新聞來源) ---
news_sources = [
    # === 原本保留的 7 個 ===
    { "name": "AP News (美聯社)", "url": "https://apnews.com/hub/world-news", "tag": "h3", "root": "https://apnews.com" },
    { "name": "CNN", "url": "https://edition.cnn.com/world", "tag": "span", "root": "https://edition.cnn.com" },
    { "name": "BBC News", "url": "https://www.bbc.com/news", "tag": "h2", "root": "https://www.bbc.com" },
    { "name": "The Guardian (衛報)", "url": "https://www.theguardian.com/international", "tag": "h3", "root": "" },
    { "name": "NPR (美國公共廣播)", "url": "https://www.npr.org/sections/news/", "tag": "h2", "root": "" },
    { "name": "Al Jazeera (半島電視台)", "url": "https://www.aljazeera.com/news/", "tag": "h3", "root": "https://www.aljazeera.com" },
    { "name": "Nature (科學期刊)", "url": "https://www.nature.com/news", "tag": "h3", "root": "" },
    
    # === 新增的 (已移除高防禦網站) ===
    { "name": "The New York Times (紐約時報)", "url": "https://www.nytimes.com/section/world", "tag": "h3", "root": "https://www.nytimes.com" },
    { "name": "The Washington Post (華盛頓郵報)", "url": "https://www.washingtonpost.com/world", "tag": "h2", "root": "" },
    { "name": "Nikkei Asia (日經)", "url": "https://asia.nikkei.com/", "tag": "h4", "root": "https://asia.nikkei.com" }, 
    { "name": "Le Monde (世界報)", "url": "https://www.lemonde.fr/en/", "tag": "h3", "root": "" },
    { "name": "Der Spiegel (明鏡周刊)", "url": "https://www.spiegel.de/international/", "tag": "h3", "root": "" },
    { "name": "Deutsche Welle (德國之聲)", "url": "https://www.dw.com/en/top-stories/s-9097", "tag": "h3", "root": "https://www.dw.com" },
    { "name": "El País (國家報)", "url": "https://english.elpais.com/", "tag": "h2", "root": "https://english.elpais.com" },
    { "name": "Xinhua (新華社)", "url": "https://english.news.cn/", "tag": "span", "root": "" },
    { "name": "SCMP (南華早報)", "url": "https://www.scmp.com/news/world", "tag": "h2", "root": "https://www.scmp.com" }
]

# 初始化翻譯器
translator = GoogleTranslator(source='auto', target='zh-TW')

# --- 偽裝頭 ---
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

# --- 步驟 1: 清空舊檔 ---
print("🧹 正在清空舊的新聞檔案...")
with open("news_report.txt", "w", encoding="utf-8") as file:
    file.write("=== 每日重點新聞彙整 (16 Sources) ===\n\n")

# --- 核心功能函數 ---
def get_news(source_config):
    url = source_config["url"]
    tag = source_config["tag"]
    root_url = source_config["root"]
    site_name = source_config["name"]

    print(f"🚀 正在前往 {site_name}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            items = []

            # --- 網站專屬處理邏輯 ---
            if site_name == "CNN":
                items = soup.find_all("span", class_="container__headline-text")
                if not items: items = soup.find_all("span")
            
            elif site_name == "Xinhua (新華社)":
                items = soup.find_all("div", class_="tit") 
                if not items: items = soup.find_all("span")

            elif site_name == "Nikkei Asia (日經)":
                 items = soup.find_all("h4")
            
            else:
                items = soup.find_all(tag)
            # -----------------------

            if len(items) > 0:
                print(f"   ✅ 成功連線，找到 {len(items)} 個潛在標題")
            else:
                print(f"   ⚠️ 連線成功但找不到標題")

            count = 0
            seen_titles = set()

            for item in items:
                if count >= 5: break
                
                # 抓取連結
                if tag in ["h2", "h3", "h4", "span", "div"]:
                    link = item.find_parent("a")
                    if not link: link = item.find("a")
                else:
                    link = item 
                
                # 抓取標題文字
                headline_en = ""
                if item.get_text(strip=True):
                    headline_en = item.get_text(strip=True)
                elif link and link.get_text(strip=True):
                    headline_en = link.get_text(strip=True)

                if headline_en and len(headline_en) > 10 and headline_en not in seen_titles:
                    seen_titles.add(headline_en)
                    
                    try:
                        headline_zh = translator.translate(headline_en)
                        print(f"   📰 {headline_zh}")
                    except:
                        headline_zh = headline_en
                        print(f"   📰 {headline_zh} (翻譯略過)")
                    
                    if link:
                        link_url = link.get("href")
                        if link_url:
                            if not link_url.startswith("http"):
                                link_url = root_url + link_url
                            
                            with open("news_report.txt", "a", encoding="utf-8") as file:
                                file.write(f"【{site_name}】{headline_zh}\n{link_url}\n\n")
                            
                            count += 1
            
            if count == 0 and response.status_code == 200:
                print("   ⚠️ 沒抓到符合條件的新聞。")

        else:
            if response.status_code in [401, 403]:
                print(f"   🚫 被阻擋 (Error {response.status_code}): 該網站有嚴格防爬蟲機制")
            else:
                print(f"   ❌ 連線失敗: {response.status_code}")

    except Exception as e:
        print(f"   ❌ 發生錯誤: {e}")

    print("-" * 30)
    time.sleep(1)

# --- 主程式區 (不需要 while loop，也不需要 job 函數包裝) ---
print(f"⏰ 開始執行每日新聞抓取... 現在時間: {time.strftime('%H:%M:%S')}")

for source in news_sources:
    get_news(source)

print("💤 任務完成！")
