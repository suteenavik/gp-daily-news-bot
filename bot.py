import os
import requests
import feedparser
import re
from datetime import datetime, timedelta, timezone


TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


# =========================
# RSS แหล่งข่าว
# =========================

NEWS_RSS = "https://www.thairath.co.th/rss/news"
TECH_RSS = "https://feeds.arstechnica.com/arstechnica/index"
POLITICS_RSS = "http://rssfeeds.sanook.com/rss/feeds/sanook/news.politic.xml"
SPORTS_RSS = "https://www.thairath.co.th/rss/sport"
ECONOMIC_RSS = "http://rssfeeds.sanook.com/rss/feeds/sanook/news.economic.xml"


# =========================
# อ่าน RSS
# =========================

news_feed = feedparser.parse(NEWS_RSS)
tech_feed = feedparser.parse(TECH_RSS)
politics_feed = feedparser.parse(POLITICS_RSS)
sports_feed = feedparser.parse(SPORTS_RSS)
economic_feed = feedparser.parse(ECONOMIC_RSS)


# =========================
# ทำหัวข้อให้เหมาะกับการ
# ตรวจข่าวซ้ำ
# =========================

def normalize_title(title):
    title = title.lower()

    title = re.sub(r"https?://\S+", "", title)

    title = re.sub(r"[^\w\sก-๙]", " ", title)

    title = re.sub(r"\s+", " ", title).strip()

    return title


# =========================
# ตรวจข่าวซ้ำ
# =========================

def remove_duplicates(items):
    unique_items = []
    seen_titles = set()

    for item in items:
        title = item.get("title", "").strip()

        if not title:
            continue

        normalized = normalize_title(title)

        if normalized in seen_titles:
            continue

        seen_titles.add(normalized)
        unique_items.append(item)

    return unique_items


# =========================
# คำสำคัญสำหรับให้คะแนนข่าว
# =========================

IMPORTANT_KEYWORDS = [
    "ด่วน",
    "สำคัญ",
    "ประกาศ",
    "กระทบ",
    "วิกฤต",
    "เตือนภัย",
    "ฉุกเฉิน",
    "รัฐบาล",
    "นายกรัฐมนตรี",
    "รัฐมนตรี",
    "เลือกตั้ง",
    "นโยบาย",
    "กฎหมาย",
    "สงคราม",
    "ความขัดแย้ง",
    "หุ้น",
    "ตลาดหุ้น",
    "เศรษฐกิจ",
    "การลงทุน",
    "นักลงทุน",
    "ราคาทอง",
    "น้ำมัน",
    "ดอกเบี้ย",
    "เงินบาท",
    "ธนาคาร",
    "บริษัท",
    "AI",
    "เทคโนโลยี",
    "Cybersecurity",
    "Microsoft",
    "Google",
    "Apple",
    "Amazon",
    "Meta",
    "Nvidia",
    "OpenAI",
    "Tesla",
    "ฟุตบอล",
    "ทีมชาติ",
    "พรีเมียร์ลีก",
    "ยูฟ่า",
    "แชมเปียนส์ลีก",
    "ผลการแข่งขัน",
    "ชนะ",
    "แพ้",
]


LOW_PRIORITY_KEYWORDS = [
    "ดารา",
    "บันเทิง",
    "ละคร",
    "เพลง",
    "แฟชั่น",
    "ความรัก",
    "ดวง",
    "ไลฟ์สไตล์",
]


# =========================
# ให้คะแนนข่าว
# =========================

def score_news(item):
    title = item.get("title", "").lower()

    score = 0

    for keyword in IMPORTANT_KEYWORDS:
        if keyword.lower() in title:
            score += 2

    for keyword in LOW_PRIORITY_KEYWORDS:
        if keyword.lower() in title:
            score -= 2

    if "ด่วน" in title:
        score += 5

    if re.search(r"\d", title):
        score += 1

    return score


# =========================
# แปลงเวลาเป็นเวลาไทย
# =========================

def get_thai_time(item):
    published_time = item.get("published_parsed")

    if not published_time:
        return ""

    try:
        published_dt = datetime(
            published_time.tm_year,
            published_time.tm_mon,
            published_time.tm_mday,
            published_time.tm_hour,
            published_time.tm_min,
            published_time.tm_sec,
            tzinfo=timezone.utc,
        )

        thai_time = published_dt.astimezone(
            timezone(timedelta(hours=7))
        )

        return thai_time.strftime("%H:%M")

    except Exception:
        return ""


# =========================
# กรองข่าว 24 ชั่วโมง
# + ตัดข่าวซ้ำ
# + จัดอันดับข่าว
# =========================

def get_recent_news(feed, limit=5):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    recent_news = []

    for item in feed.entries:
        published_time = item.get("published_parsed")

        if not published_time:
            continue

        try:
            published_dt = datetime(
                published_time.tm_year,
                published_time.tm_mon,
                published_time.tm_mday,
                published_time.tm_hour,
                published_time.tm_min,
                published_time.tm_sec,
                tzinfo=timezone.utc,
            )

            if published_dt >= cutoff:
                recent_news.append(item)

        except Exception:
            continue

    recent_news = remove_duplicates(recent_news)

    for item in recent_news:
        item["_news_score"] = score_news(item)

    recent_news.sort(
        key=lambda item: (
            item.get("_news_score", 0),
            item.get("published_parsed"),
        ),
        reverse=True,
    )

    return recent_news[:limit]


# =========================
# ดึงข่าวแต่ละหมวด
# =========================

news_items = get_recent_news(news_feed, 5)
tech_items = get_recent_news(tech_feed, 5)
politics_items = get_recent_news(politics_feed, 5)
sports_items = get_recent_news(sports_feed, 5)
economic_items = get_recent_news(economic_feed, 5)


# =========================
# วันที่และเวลาปัจจุบันของไทย
# =========================

thai_timezone = timezone(timedelta(hours=7))
now_thai = datetime.now(thai_timezone)

thai_date = now_thai.strftime("%d/%m/%Y")
thai_time = now_thai.strftime("%H:%M")


# =========================
# สร้างข้อความ
# =========================

message = "☀️ GP MORNING BRIEF\n"
message += f"📅 {thai_date}  🕐 {thai_time} น.\n"
message += "📰 ข่าวสำคัญในรอบ 24 ชั่วโมง\n"
message += "━━━━━━━━━━━━━━━━━━\n\n"


# =========================
# เพิ่มหมวดข่าว
# =========================

def add_section(title, items):
    global message

    message += f"{title}\n\n"

    if not items:
        message += "ไม่มีข่าวในช่วง 24 ชั่วโมงล่าสุด\n\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        return

    for index, item in enumerate(items, start=1):
        title_text = item.get("title", "ไม่มีหัวข้อ")
        link = item.get("link", "")
        news_time = get_thai_time(item)

        message += f"{index}️⃣ {title_text}\n"

        if news_time:
            message += f"   🕐 {news_time} น.\n"

        if link:
            message += f"   🔗 {link}\n"

        message += "\n"

    message += "━━━━━━━━━━━━━━━━━━\n\n"


# =========================
# เพิ่มข่าว 5 หมวด
# =========================

add_section("📰 ข่าวเด่น", news_items)

add_section("💻 IT / TECHNOLOGY", tech_items)

add_section("🏛️ การเมือง", politics_items)

add_section("⚽ SPORTS", sports_items)

add_section("📈 หุ้น / เศรษฐกิจ", economic_items)


# =========================
# ส่ง Telegram
# =========================

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": message,
    },
    timeout=30,
)

response.raise_for_status()

print("Morning Brief sent successfully.")
