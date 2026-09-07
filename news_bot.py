import feedparser
from groq import Groq
import requests
import os
import json
from datetime import datetime, timedelta, timezone

# ========== НАСТРОЙКИ ==========
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = "@podkruti_vesa"

# ========== ИСТОЧНИКИ НОВОСТЕЙ (12 штук) ==========
RSS_FEEDS = [
    # --- ИИ: США ---
    'https://openai.com/blog/rss.xml',
    'https://venturebeat.com/category/ai/feed/',
    'https://www.anthropic.com/rss.xml',
    # --- ИИ: Китай ---
    'https://www.syncedreview.com/feed/',
    # --- ИИ: Европа ---
    'https://deepmind.google/blog/rss.xml',
    # --- ИИ: Россия ---
    'https://neurohive.io/ru/feed/',
    'https://habr.com/ru/hub/artificial_intelligence/rss/',
    # --- Технологии: США ---
    'https://techcrunch.com/feed/',
    'https://arstechnica.com/feed/',
    # --- Технологии: Китай ---
    'https://technode.com/feed/',
    # --- Технологии: Европа ---
    'https://tech.eu/feed/',
    'https://www.theregister.com/headlines.atom'
]

MEMORY_FILE = "posted_news.json"
groq_client = Groq(api_key=GROQ_API_KEY)

# ========== ФУНКЦИИ ПАМЯТИ ==========
def load_posted_news():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_posted_news(posted_list):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(posted_list[-100:], f, ensure_ascii=False, indent=2)

# ========== ЧТЕНИЕ RSS ==========
def get_news_from_rss(feed_url, max_items=2):
    try:
        feed = feedparser.parse(feed_url)
        news_list = []
        for entry in feed.entries[:max_items]:
            raw_summary = entry.get('summary', 'Нет описания')
            short_summary = (raw_summary[:600] + "...") if len(raw_summary) > 600 else raw_summary
            news_item = {
                'title': entry.title,
                'summary': short_summary,
                'link': entry.link,
                'source': feed.feed.get('title', 'Неизвестный источник')
            }
            news_list.append(news_item)
        return news_list
    except Exception as e:
        print(f"Ошибка при чтении {feed_url}: {e}")
        return []

def get_all_news():
    all_news = []
    for feed_url in RSS_FEEDS:
        news = get_news_from_rss(feed_url, max_items=2)
        all_news.extend(news)
    return all_news[:5]

# ========== ПЕРЕВОД И СОДЕРЖАНИЕ ==========
def translate_title_with_qwen(original_title):
    response = groq_client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "system", "content": "Ты — переводчик. Переводи заголовки на русский кратко. Отвечай ТОЛЬКО переводом."},
            {"role": "user", "content": f"Переведи:\n{original_title}"}
        ],
        temperature=0.3,
        max_tokens=100
    )
    return response.choices[0].message.content.strip().strip('"\'')

def write_summary_with_qwen(news_item):
    prompt = f"""ИСТОЧНИК: {news_item['source']}
ЗАГОЛОВОК: {news_item['title']}
ТЕКСТ: {news_item['summary']}
Напиши КРАТКОЕ содержание в 2-4 предложениях (что, почему важно, факты). Живой язык, 1-2 эмодзи. Без заголовка."""
    response = groq_client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "system", "content": "Ты — редактор. Отвечай ТОЛЬКО текстом."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=400
    )
    return response.choices[0].message.content.strip()

def create_post(news_item):
    translated_title = translate_title_with_qwen(news_item['title'])
    summary = write_summary_with_qwen(news_item)
    return f"<b>{translated_title}</b>\n\n{summary}\n\n <a href='{news_item['link']}'>Читать подробнее</a>\n\n#AI #технологии #новости"

# ========== ПОСТИНГ ЧЕРЕЗ ПРЯМОЙ HTTP-ЗАПРОС (с поддержкой schedule_date!) ==========
def post_to_telegram(text, schedule_date=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    # Добавляем schedule_date если указано (Telegram сам опубликует в нужное время!)
    if schedule_date:
        payload["schedule_date"] = int(schedule_date.timestamp())
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        if schedule_date:
            print(f"✅ Запланировано на {schedule_date.strftime('%H:%M')} (UTC)")
        else:
            print("✅ Опубликовано!")
        return True
    else:
        print(f"⚠️ Ошибка Telegram: {response.text}")
        return False

# ========== ГЛАВНЫЙ ЦИКЛ ==========
def main():
    print(" Запуск...\n")
    
    posted_links = load_posted_news()
    print(f" В памяти {len(posted_links)} уже опубликованных новостей.")
    
    raw_news = get_all_news()
    
    unique_news = [item for item in raw_news if item['link'] not in posted_links]
    print(f"📊 Найдено {len(raw_news)} новостей, из них {len(unique_news)} новых.\n")
    
    if not unique_news:
        print("🔄 Новых новостей нет. Пропускаем генерацию.")
        return
    
    total_posts = len(unique_news)
    # Интервал 12 минут между постами (5 постов за 60 минут)
    interval_minutes = 12
    
    new_links = []
    for i, news_item in enumerate(unique_news):
        print(f"📝 Обрабатываю: {news_item['title'][:50]}...")
        try:
            post = create_post(news_item)
            
            # Первый пост через 2 минуты, остальные с интервалом 12 минут
            schedule_time = datetime.now(timezone.utc) + timedelta(minutes=2 + (i * interval_minutes))
            
            success = post_to_telegram(post, schedule_date=schedule_time)
            if success:
                new_links.append(news_item['link'])
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            
    save_posted_news(posted_links + new_links)
    print(f"\n🎉 Готово! Запомнил {len(new_links)} новых ссылок.")
    print(f"⏰ Посты будут выходить в течение часа (с интервалом 12 минут).")

if __name__ == "__main__":
    main()
