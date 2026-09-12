import os
import requests
import feedparser
import re
from datetime import datetime, timedelta, timezone

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

NEWS_RSS = "https://www.thairath.co.th/rss/news"

TECH_TH_RSS = "https://www.blognone.com/atom.xml"
TECH_GLOBAL_RSS = "https://feeds.arstechnica.com/arstechnica/index"

POLITICS_RSS = "http://rssfeeds.sanook.com/rss/feeds/sanook/news.politic.xml"
SPORTS_RSS = "https://www.thairath.co.th/rss/sport"
ECONOMIC_RSS = "http://rssfeeds.sanook.com/rss/feeds/sanook/news.economic.xml"


# =========================
# LOAD RSS FEEDS
# =========================

news_feed = feedparser.parse(NEWS_RSS)

tech_th_feed = feedparser.parse(TECH_TH_RSS)
tech_global_feed = feedparser.parse(TECH_GLOBAL_RSS)

politics_feed = feedparser.parse(POLITICS_RSS)
sports_feed = feedparser.parse(SPORTS_RSS)
economic_feed = feedparser.parse(ECONOMIC_RSS)


# =========================
# REMOVE DUPLICATE TITLES
# =========================

def normalize_title(title):
    title = title.lower()

    # ลบ URL
    title = re.sub(r"https?://\S+", "", title)

    # ลบคำที่มักทำให้พาดหัวต่างกัน
    remove_words = [
        "ด่วน",
        "ล่าสุด",
        "เผย",
        "เปิดเผย",
        "รายงาน",
        "ระบุ",
        "ชี้",
        "พบว่า",
        "เตือน",
        "ประกาศ",
        "แล้ว",
        "วันนี้",
        "เมื่อวันนี้",
        "ล่าสุดนี้",
    ]

    for word in remove_words:
        title = title.replace(word, " ")

    # ลบเครื่องหมายพิเศษ
    title = re.sub(r"[^\w\sก-๙]", " ", title)

    # ลดช่องว่าง
    title = re.sub(r"\s+", " ", title).strip()

    return title


def get_title_words(title):
    normalized = normalize_title(title)

    words = normalized.split()

    # ตัดคำสั้นมากออก
    words = [
        word for word in words
        if len(word) >= 2
    ]

    return set(words)


def titles_are_similar(title1, title2):
    words1 = get_title_words(title1)
    words2 = get_title_words(title2)

    if not words1 or not words2:
        return False

    common_words = words1.intersection(words2)

    # จำนวนคำที่เหมือนกัน
    common_count = len(common_words)

    # คำนวณสัดส่วนความคล้าย
    similarity = common_count / min(
        len(words1),
        len(words2)
    )

    # ถ้ามีคำสำคัญเหมือนกันหลายคำ
    if common_count >= 4 and similarity >= 0.55:
        return True

    return False


def remove_similar_news(items):
    unique_items = []

    for item in items:

        title = item.get(
            "title",
            ""
        ).strip()

        if not title:
            continue

        is_duplicate = False

        for existing in unique_items:

            existing_title = existing.get(
                "title",
                ""
            ).strip()

            if titles_are_similar(
                title,
                existing_title
            ):
                is_duplicate = True
                break

        if not is_duplicate:
            unique_items.append(item)

    return unique_items


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
# NEWS SCORING
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
    "Microsoft",
    "Google",
    "Apple",
    "Amazon",
    "Meta",
    "Nvidia",
    "OpenAI",
    "Tesla",
    "Gemini",
    "iPhone",
    "Android",
    "Cloud",
    "Cyber",
    "Cybersecurity",
    "Hack",
    "Hacking",
    "Data Breach",

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


def score_news(item):
    title = item.get("title", "").lower()

    score = 0

    # =====================================
    # ข่าวสำคัญทั่วไป
    # =====================================

    for keyword in IMPORTANT_KEYWORDS:
        if keyword.lower() in title:
            score += 2

    # =====================================
    # ข่าวด่วน / เหตุการณ์สำคัญ
    # =====================================

    HIGH_IMPACT_KEYWORDS = [
        "ด่วน",
        "ล่าสุด",
        "ประกาศ",
        "เตือนภัย",
        "วิกฤต",
        "ฉุกเฉิน",
        "กระทบ",
        "ครั้งแรก",
        "ครั้งใหญ่",
        "สำคัญ",
    ]

    for keyword in HIGH_IMPACT_KEYWORDS:
        if keyword.lower() in title:
            score += 4

    # =====================================
    # AI
    # =====================================

    AI_KEYWORDS = [
        "ai",
        "artificial intelligence",
        "ปัญญาประดิษฐ์",
        "generative ai",
        "agentic ai",
        "ai agent",
        "chatgpt",
        "openai",
        "claude",
        "gemini",
        "deepseek",
        "copilot",
    ]

    for keyword in AI_KEYWORDS:
        if keyword.lower() in title:
            score += 4

    # =====================================
    # Cybersecurity
    # =====================================

    CYBER_KEYWORDS = [
        "cybersecurity",
        "cyber security",
        "ไซเบอร์",
        "แฮก",
        "แฮ็ก",
        "hack",
        "hacking",
        "hacker",
        "malware",
        "ransomware",
        "data breach",
        "breach",
        "ข้อมูลรั่ว",
        "ถูกโจมตี",
        "โจมตีทางไซเบอร์",
        "ขโมยข้อมูล",
    ]

    for keyword in CYBER_KEYWORDS:
        if keyword.lower() in title:
            score += 5

    # =====================================
    # บริษัท Technology รายใหญ่
    # =====================================

    BIG_TECH = [
        "microsoft",
        "google",
        "apple",
        "amazon",
        "meta",
        "nvidia",
        "openai",
        "tesla",
        "samsung",
        "qualcomm",
        "intel",
        "amd",
        "oracle",
        "adobe",
        "shopify",
    ]

    for keyword in BIG_TECH:
        if keyword.lower() in title:
            score += 3

    # =====================================
    # Technology Trends
    # =====================================

    TECH_TREND_KEYWORDS = [
        "cloud",
        "5g",
        "6g",
        "semiconductor",
        "chip",
        "ชิป",
        "data center",
        "ดาต้าเซ็นเตอร์",
        "robot",
        "หุ่นยนต์",
        "quantum",
        "blockchain",
        "electric vehicle",
        "ev",
        "autonomous",
        "รถยนต์ไร้คนขับ",
    ]

    for keyword in TECH_TREND_KEYWORDS:
        if keyword.lower() in title:
            score += 2

    # =====================================
    # การเมือง
    # =====================================

    POLITICS_KEYWORDS = [
        "รัฐบาล",
        "นายกรัฐมนตรี",
        "รัฐมนตรี",
        "เลือกตั้ง",
        "นโยบาย",
        "กฎหมาย",
        "สภา",
        "รัฐสภา",
        "ฝ่ายค้าน",
        "พรรคร่วม",
    ]

    for keyword in POLITICS_KEYWORDS:
        if keyword.lower() in title:
            score += 4

    # =====================================
    # เศรษฐกิจ / การเงิน
    # =====================================

    ECONOMIC_KEYWORDS = [
        "ตลาดหุ้น",
        "หุ้น",
        "set",
        "ดัชนี",
        "เศรษฐกิจ",
        "การลงทุน",
        "นักลงทุน",
        "ดอกเบี้ย",
        "เงินบาท",
        "ค่าเงินบาท",
        "ธนาคาร",
        "ราคาทอง",
        "ทองคำ",
        "น้ำมัน",
        "เงินเฟ้อ",
        "จีดีพี",
        "gdp",
    ]

    for keyword in ECONOMIC_KEYWORDS:
        if keyword.lower() in title:
            score += 3

    # =====================================
    # กีฬา
    # =====================================

    SPORTS_KEYWORDS = [
        "ผลการแข่งขัน",
        "ชนะ",
        "แพ้",
        "เสมอ",
        "ทีมชาติไทย",
        "ทีมชาติ",
        "พรีเมียร์ลีก",
        "ยูฟ่า",
        "แชมเปียนส์ลีก",
        "champions league",
        "premier league",
        "ฟุตบอลโลก",
        "world cup",
    ]

    for keyword in SPORTS_KEYWORDS:
        if keyword.lower() in title:
            score += 3

    # =====================================
    # ข่าวบันเทิง / ข่าวเบา
    # =====================================

    LOW_PRIORITY_KEYWORDS = [
        "ดารา",
        "บันเทิง",
        "ละคร",
        "เพลง",
        "แฟชั่น",
        "ความรัก",
        "ดวง",
        "ไลฟ์สไตล์",
        "กินเที่ยว",
        "ท่องเที่ยว",
    ]

    for keyword in LOW_PRIORITY_KEYWORDS:
        if keyword.lower() in title:
            score -= 3

    # =====================================
    # มีตัวเลข = มักมีข้อมูลสำคัญ
    # =====================================

    if re.search(r"\d", title):
        score += 1

    return score


# =========================
# THAI TIME
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
# GET NEWS FROM LAST 24 HOURS
# =========================

def get_recent_news(feed_entries, limit=5):

    now = datetime.now(timezone.utc)

    cutoff = now - timedelta(hours=24)

    recent_news = []

    for item in feed_entries:

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
# GET BALANCED IT NEWS
# =========================

def get_it_news():

    # Get more candidates from both sources first
    thai_candidates = get_recent_news(
        tech_th_feed.entries,
        10
    )

    global_candidates = get_recent_news(
        tech_global_feed.entries,
        10
    )


    # Prefer a balanced mix:
    # 5 Thai + 5 Global maximum
    thai_items = thai_candidates[:5]
    global_items = global_candidates[:5]


    # Remove duplicates between Thai and Global sources
    selected = []
    seen_titles = set()


    for item in thai_items + global_items:

        title = item.get("title", "").strip()

        if not title:
            continue

        normalized = normalize_title(title)

        if normalized in seen_titles:
            continue

        seen_titles.add(normalized)

        selected.append(item)


    # Maximum 10 IT news
    selected = selected[:10]


    # Minimum target = 5 if enough news exists
    # If fewer than 5 after duplicate removal,
    # try to fill from remaining candidates.

    if len(selected) < 5:

        remaining = thai_candidates[5:] + global_candidates[5:]

        for item in remaining:

            title = item.get("title", "").strip()

            if not title:
                continue

            normalized = normalize_title(title)

            if normalized in seen_titles:
                continue

            seen_titles.add(normalized)

            selected.append(item)

            if len(selected) >= 5:
                break


    return selected


# =========================
# NORMAL NEWS
# =========================

news_items = get_recent_news(
    news_feed.entries,
    5
)


# =========================
# IT NEWS
# =========================

it_items = get_it_news()


# =========================
# OTHER CATEGORIES
# =========================

politics_items = get_recent_news(
    politics_feed.entries,
    5
)

sports_items = get_recent_news(
    sports_feed.entries,
    5
)

economic_items = get_recent_news(
    economic_feed.entries,
    5
)


# =========================
# DATE / TIME
# =========================

thai_timezone = timezone(timedelta(hours=7))

now_thai = datetime.now(thai_timezone)

thai_date = now_thai.strftime("%d/%m/%Y")

thai_time = now_thai.strftime("%H:%M")


# =========================
# BUILD TELEGRAM MESSAGE
# =========================

message = "☀️ GP MORNING BRIEF\n"

message += f"📅 {thai_date}  🕐 {thai_time} น.\n"

message += "📰 ข่าวสำคัญในรอบ 24 ชั่วโมง\n"

message += "━━━━━━━━━━━━━━━━━━\n\n"


# =========================
# NORMAL SECTION
# =========================

def add_section(title, items):

    global message

    message += f"{title}\n\n"


    if not items:

        message += "ไม่มีข่าวในช่วง 24 ชั่วโมงล่าสุด\n\n"

        message += "━━━━━━━━━━━━━━━━━━\n\n"

        return


    for index, item in enumerate(items, start=1):

        title_text = item.get(
            "title",
            "ไม่มีหัวข้อ"
        )

        link = item.get(
            "link",
            ""
        )

        news_time = get_thai_time(item)


        message += f"{index}️⃣ {title_text}\n"


        if news_time:

            message += f"   🕐 {news_time} น.\n"


        if link:

            message += f"   🔗 {link}\n"


        message += "\n"


    message += "━━━━━━━━━━━━━━━━━━\n\n"


# =========================
# IT SECTION
# =========================

def add_it_section(items):

    global message

    message += "💻 IT / TECHNOLOGY 🇹🇭 + 🌎\n\n"


    if not items:

        message += "ไม่มีข่าว IT ในช่วง 24 ชั่วโมงล่าสุด\n\n"

        message += "━━━━━━━━━━━━━━━━━━\n\n"

        return


    # Separate Thai and Global based on source URL

    thai_items = []

    global_items = []


    for item in items:

        link = item.get("link", "")

        if "blognone.com" in link:

            thai_items.append(item)

        else:

            global_items.append(item)


    # Thai IT

    if thai_items:

        message += "🇹🇭 ข่าว IT ไทย\n\n"

        for index, item in enumerate(
            thai_items,
            start=1
        ):

            title_text = item.get(
                "title",
                "ไม่มีหัวข้อ"
            )

            link = item.get(
                "link",
                ""
            )

            news_time = get_thai_time(item)


            message += f"{index}️⃣ {title_text}\n"


            if news_time:

                message += f"   🕐 {news_time} น.\n"


            if link:

                message += f"   🔗 {link}\n"


            message += "\n"


    # Global IT

    if global_items:

        message += "🌎 ข่าว IT ต่างประเทศ\n\n"

        start_number = len(thai_items) + 1


        for index, item in enumerate(
            global_items,
            start=start_number
        ):

            title_text = item.get(
                "title",
                "ไม่มีหัวข้อ"
            )

            link = item.get(
                "link",
                ""
            )

            news_time = get_thai_time(item)


            message += f"{index}️⃣ {title_text}\n"


            if news_time:

                message += f"   🕐 {news_time} น.\n"


            if link:

                message += f"   🔗 {link}\n"


            message += "\n"


    message += "━━━━━━━━━━━━━━━━━━\n\n"


# =========================
# ADD ALL SECTIONS
# =========================

add_section(
    "📰 ข่าวเด่น",
    news_items
)

add_it_section(
    it_items
)

add_section(
    "🏛️ การเมือง",
    politics_items
)

add_section(
    "⚽ SPORTS",
    sports_items
)

add_section(
    "📈 หุ้น / เศรษฐกิจ",
    economic_items
)


# =========================
# SEND TELEGRAM
# =========================

url = (
    f"https://api.telegram.org/"
    f"bot{TOKEN}/sendMessage"
)


response = requests.post(

    url,

    data={
        "chat_id": CHAT_ID,
        "text": message,
    },

    timeout=30,
)


response.raise_for_status()


print(
    f"Morning Brief sent successfully. "
    f"IT news: {len(it_items)}"
)
