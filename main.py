import requests
from bs4 import BeautifulSoup
import os
import time

# دریافت متغیرها
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# فایل برای ذخیره لینک‌های ارسال شده تا تکراری فرستاده نشود
SENT_LINKS_FILE = "sent_links.txt"

def load_sent_links():
    if not os.path.exists(SENT_LINKS_FILE):
        return set()
    with open(SENT_LINKS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_link(link):
    with open(SENT_LINKS_FILE, "a") as f:
        f.write(f"{link}\n")

def send_to_telegram(photo_url, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    # اگر متن خیلی طولانی بود کوتاه شود
    if len(caption) > 1000:
        caption = caption[:1000] + "..."
    
    data = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption
    }
    try:
        resp = requests.post(url, data=data)
        print(f"Sent: {resp.status_code}")
    except Exception as e:
        print(f"Error sending: {e}")

def crawl_varzesh3():
    print("Checking Varzesh3...")
    url = "https://www.varzesh3.com/news/tag/43/%D9%BE%D8%B1%D8%B3%D9%BE%D9%88%D9%84%DB%8C%D8%B3" # لینک مستقیم اخبار پرسپولیس
    
    # هدر برای اینکه سایت ما را ربات تشخیص ندهد
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, "html.parser")
        sent_links = load_sent_links()

        # کلاس صحیح خبرهای ورزش 3 معمولا در بخش آرشیو متفاوت است، این یک نمونه است:
        # نکته: باید کلاس دقیق news-main-list li را چک کنید
        news_list = soup.select(".news-main-list li") 

        for item in news_list:
            try:
                # استخراج لینک و تیتر
                link_tag = item.select_one("a")
                if not link_tag: continue
                
                href = link_tag['href']
                full_link = href if href.startswith("http") else f"https://www.varzesh3.com{href}"
                
                # اگر قبلا فرستاده شده، رد کن
                if full_link in sent_links:
                    continue

                title_tag = item.select_one(".title")
                title = title_tag.text.strip() if title_tag else "خبر پرسپولیس"
                
                img_tag = item.select_one("img")
                photo = img_tag['src'] if img_tag else "https://www.varzesh3.com/assets/img/logo.png"

                # ارسال به تلگرام
                caption = f"🔴 {title}\n\n🔗 {full_link}"
                send_to_telegram(photo, caption)
                
                # ذخیره در فایل که دوباره فرستاده نشود
                save_link(full_link)
                
                # وقفه کوتاه برای جلوگیری از بلاک شدن
                time.sleep(2)

            except Exception as e:
                print(f"Error parsing item: {e}")

    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    # اگر از Cron Job رندر استفاده می‌کنید، نیازی به schedule و while true نیست
    # فقط تابع را صدا بزنید تا یک بار اجرا شود و تمام شود
    crawl_varzesh3()
    # crawl_football360() -> باید کلاس‌هایش اصلاح شود
    # crawl_fotballi() -> باید کلاس‌هایش اصلاح شود
