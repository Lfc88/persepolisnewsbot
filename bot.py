import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
import threading
import time
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SENT_LINKS_FILE = "sent_links.txt"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
}

app = Flask(__name__)

@app.route('/')
def home():
    return "ربات اخبار پرسپولیس فعال است! 🚀"

def load_sent_links():
    if not os.path.exists(SENT_LINKS_FILE):
        return set()
    with open(SENT_LINKS_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_link(link):
    with open(SENT_LINKS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{link}\n")

def make_absolute_url(base_url, href):
    return urllib.parse.urljoin(base_url, href)

def simple_summary(title, text, max_len=300):
    combined = f"{title.strip()}\n\n{text.strip()}" if text else title.strip()
    if len(combined) > max_len:
        return combined[:max_len-3] + "..."
    return combined

def send_to_telegram(caption):
    if not caption:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": caption[:4096],
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        resp = requests.post(url, data=data, timeout=20)
        if resp.status_code == 200:
            print("ارسال موفق")
        else:
            print(f"خطا: {resp.status_code}")
    except Exception as e:
        print(f"خطای تلگرام: {e}")

def crawl_site(url, item_selector, title_selector, summary_selector, site_name):
    print(f"بررسی {site_name}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        sent_links = load_sent_links()
        items = soup.select(item_selector)
        for item in items:
            try:
                link_tag = item.select_one("a")
                if not link_tag or not link_tag.get("href"):
                    continue
                full_link = make_absolute_url(url, link_tag["href"])
                if full_link in sent_links:
                    continue
                title_tag = item.select_one(title_selector)
                title = title_tag.get_text(strip=True) if title_tag else "بدون عنوان"
                if "پرسپولیس" not in title:
                    continue
                summary_tag = item.select_one(summary_selector)
                summary_text = summary_tag.get_text(strip=True) if summary_tag else ""
                caption = simple_summary(title, summary_text, 300)
                final_caption = f"<b>🔴 {title}</b>\n\n{caption}\n\n🌐 منبع: <a href='{url}'>{site_name}</a>"
                send_to_telegram(final_caption)
                save_link(full_link)
                time.sleep(1.5)
            except Exception as e:
                print(f"خطا در آیتم: {e}")
    except Exception as e:
        print(f"خطای اتصال به {site_name}: {e}")

def crawl_all():
    crawl_site(
        url="https://www.varzesh3.com/news/tag/43/%D9%BE%D8%B1%D8%B3%D9%BE%D9%88%D9%84%DB%8C%D8%B3",
        item_selector=".news-main-list li",
        title_selector=".title",
        summary_selector=".lead, .summary",
        site_name="ورزش ۳"
    )
    crawl_site(
        url="https://football360.ir/tag/%D9%BE%D8%B1%D8%B3%D9%BE%D9%88%D9%84%DB%8C%D8%B3",
        item_selector=".item.news-list",
        title_selector="h2 a",
        summary_selector=".item-summary",
        site_name="فوتبال ۳۶۰"
    )
    crawl_site(
        url="https://www.fotballi.net/tag/%D9%BE%D8%B1%D8%B3%D9%BE%D9%88%D9%84%DB%8C%D8%B3",
        item_selector=".list-item",
        title_selector=".item-title a",
        summary_selector=".item-description",
        site_name="فوتبالی"
    )

def run_crawler_periodically():
    while True:
        crawl_all()
        print("خواب ۱۰ دقیقه‌ای...")
        time.sleep(600)

if __name__ == "__main__":
    threading.Thread(target=run_crawler_periodically, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
