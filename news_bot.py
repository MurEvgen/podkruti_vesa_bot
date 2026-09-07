import feedparser
from groq import Groq
import requests
import os
import json

# ========== НАСТРОЙКИ ==========
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = "@podkruti_vesa"

RSS_FEEDS = [
    'https://openai.com/blog/rss.xml',
    'https://venturebeat.com/category/ai/feed/',
    'https://www.anthropic.com/rss.xml',
    'https://www.syncedreview.com/feed/',
    'https://deepmind.google/blog/rss.xml',
    'https://neurohive.io/ru/feed/',
    'https://habr.com/ru/hub/artificial_intelligence/rss/',
    'https://techcrunch.com/feed/',
    'https://arstechnica.com/feed/',
    'https://technode.com/feed/',
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
    return all_news

# ========== ПЕРЕВОД И СОДЕРЖАНИЕ ==========
def translate_title_with_qwen(original_title):
    try:
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",  # Ваша проверенная модель
            messages=[
                {"role": "system", "content": "Переведи заголовок на русский кратко. Отвечай ТОЛЬКО переводом."},
                {"role": "user", "content": f"Переведи:\n{original_title}"}
            ],
            temperature=0.3,
            max_tokens=100
        )
        return response.choices[0].message.content.strip().strip('"\'')
    except Exception as e:
        print(f"⚠️ Ошибка перевода: {e}")
        return original_title

def write_summary_with_qwen(news_item):
    try:
        prompt = f"""ИСТОЧНИК: {news_item['source']}
ЗАГОЛОВОК: {news_item['title']}
ТЕКСТ: {news_item['summary']}
Напиши КРАТКОЕ содержание в 2-4 предложениях. Живой язык, 1-2 эмодзи. Без заголовка."""
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",  # Ваша проверенная модель
            messages=[
                {"role": "system", "content": "Ты — редактор. Отвечай ТОЛЬКО текстом."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Ошибка генерации: {e}")
        return news_item['summary'][:200]

def create_post(news_item):
    translated_title = translate_title_with_qwen(news_item['title'])
    summary = write_summary_with_qwen(news_item)
    return f"<b>{translated_title}</b>\n\n{summary}\n\n🔗 <a href='{news_item['link']}'>Читать подробнее</a>\n\n#AI #технологии #новости"

# ========== ПОСТИНГ В TELEGRAM ==========
def post_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false"
    }
    
    response = requests.post(url, data=data, timeout=15)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('ok'):
            print("✅ Опубликовано!")
            return True
    
    print(f"⚠️ Ошибка Telegram: {response.text}")
    return False

# ========== ГЛАВНЫЙ ЦИКЛ ==========
def main():
    print("🚀 Запуск...\n")
    
    posted_links = load_posted_news()
    print(f"🧠 В памяти {len(posted_links)} уже опубликованных новостей.")
    
    raw_news = get_all_news()
    
    unique_news = [item for item in raw_news if item['link'] not in posted_links]
    print(f"📊 Найдено {len(raw_news)} новостей, из них {len(unique_news)} новых.\n")
    
    if not unique_news:
        print("🔄 Новых новостей нет. Ждем следующего запуска через 30 минут.")
        return
    
    # БЕРЕМ ТОЛЬКО 1 НОВОСТЬ за запуск для экономии лимитов GitHub
    news_item = unique_news[0]
    print(f"📝 Публикую: {news_item['title'][:40]}...")
    
    try:
        post = create_post(news_item)
        if post_to_telegram(post):
            posted_links.append(news_item['link'])
            save_posted_news(posted_links)
            print("🎉 Успешно! Скрипт завершает работу.")
        else:
            print("❌ Не удалось опубликовать")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
