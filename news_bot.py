import feedparser
from groq import Groq
import requests
import os
import json

# ========== НАСТРОЙКИ ==========
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = "@podkruti_vesa"

# Разделяем источники на категории
AI_FEEDS = [
    'https://openai.com/blog/rss.xml',
    'https://venturebeat.com/category/ai/feed/',
    'https://www.anthropic.com/rss.xml',
    'https://www.syncedreview.com/feed/',
    'https://deepmind.google/blog/rss.xml',
    'https://neurohive.io/ru/feed/',
    'https://habr.com/ru/hub/artificial_intelligence/rss/'
]

TECH_FEEDS = [
    'https://techcrunch.com/feed/',
    'https://arstechnica.com/feed/',
    'https://technode.com/feed/',
    'https://tech.eu/feed/',
    'https://www.theregister.com/headlines.atom'
]

MEMORY_FILE = "posted_news.json"
groq_client = Groq(api_key=GROQ_API_KEY)

# ========== ФУНКЦИИ ПАМЯТИ ==========
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Если старый формат (просто список), конвертируем
            if isinstance(data, list):
                return {'posted_links': data, 'ai_index': 0, 'tech_index': 0, 'category': 'ai'}
            return data
    return {'posted_links': [], 'ai_index': 0, 'tech_index': 0, 'category': 'ai'}

def save_memory(memory):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

# ========== ЧТЕНИЕ RSS ==========
def get_news_from_rss(feed_url, max_items=3):
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

def get_news_from_feeds(feeds, start_index):
    """Берём новости начиная с определённого индекса (round-robin)"""
    num_feeds = len(feeds)
    if num_feeds == 0:
        return [], start_index
    
    # Начинаем с start_index и идём по кругу
    all_news = []
    current_index = start_index
    for i in range(num_feeds):
        feed_idx = (current_index + i) % num_feeds
        news = get_news_from_rss(feeds[feed_idx], max_items=2)
        all_news.extend(news)
    
    # Следующий индекс — сдвигаем на 1
    next_index = (start_index + 1) % num_feeds
    return all_news, next_index

# ========== ПЕРЕВОД И СОДЕРЖАНИЕ ==========
def translate_title_with_qwen(original_title):
    try:
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
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
            model="qwen/qwen3.8-27b",
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
    
    memory = load_memory()
    posted_links = memory['posted_links']
    ai_index = memory.get('ai_index', 0)
    tech_index = memory.get('tech_index', 0)
    current_category = memory.get('category', 'ai')
    
    print(f"🧠 В памяти {len(posted_links)} опубликованных новостей.")
    print(f"📂 Текущая категория: {current_category.upper()}")
    
    # Выбираем источники в зависимости от категории
    if current_category == 'ai':
        feeds = AI_FEEDS
        start_index = ai_index
        print(f"🤖 Источники AI: {len(feeds)} каналов")
    else:
        feeds = TECH_FEEDS
        start_index = tech_index
        print(f"💻 Источники TECH: {len(feeds)} каналов")
    
    # Получаем новости с round-robin
    raw_news, next_index = get_news_from_feeds(feeds, start_index)
    
    # Фильтруем уже опубликованные
    unique_news = [item for item in raw_news if item['link'] not in posted_links]
    print(f"📊 Найдено {len(raw_news)} новостей, из них {len(unique_news)} новых.\n")
    
    if not unique_news:
        print("🔄 Новых новостей нет. Переключаем категорию.")
        # Переключаем категорию для следующего запуска
        next_category = 'tech' if current_category == 'ai' else 'ai'
        memory['category'] = next_category
        save_memory(memory)
        return
    
    # Берём только 1 новость
    news_item = unique_news[0]
    print(f" Публикую: {news_item['title'][:40]}...")
    
    try:
        post = create_post(news_item)
        if post_to_telegram(post):
            posted_links.append(news_item['link'])
            
            # Переключаем категорию для следующего запуска
            next_category = 'tech' if current_category == 'ai' else 'ai'
            
            # Сохраняем обновлённую память
            memory['posted_links'] = posted_links[-100:]  # Храним последние 100
            memory['ai_index'] = ai_index if current_category == 'ai' else next_index
            memory['tech_index'] = next_index if current_category == 'tech' else tech_index
            memory['category'] = next_category
            
            save_memory(memory)
            print(f"🎉 Успешно! Следующая категория: {next_category.upper()}")
        else:
            print("❌ Не удалось опубликовать")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
