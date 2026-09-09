import feedparser
from groq import Groq
import requests
import os
import json

# ========== НАСТРОЙКИ ==========
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = "@podkruti_vesa"

# ========== ИСТОЧНИКИ (только проверенные) ==========
AI_FEEDS = [
    # --- ИИ-компании и лаборатории ---
    'https://openai.com/blog/rss.xml',
    'https://deepmind.google/blog/rss.xml',
    'https://blog.google/technology/ai/rss/',          # Google AI Blog
    # --- ИИ-разработки и исследования ---
    'https://huggingface.co/blog/feed.xml',            # Hugging Face
    'https://the-decoder.com/feed/',                   # The Decoder
    'https://www.technologyreview.com/topic/artificial-intelligence/feed',  # MIT TR AI
    'https://rss.arxiv.org/rss/cs.AI',                 # arXiv (научные статьи)
    'https://techcrunch.com/category/artificial-intelligence/feed/',  # TechCrunch AI
    'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml',    # The Verge AI
    # --- Русские ИИ-источники ---
    'https://neurohive.io/ru/feed/',
    'https://habr.com/ru/rss/hub/artificial_intelligence/',  # Habr AI (альтернативный URL)
    # --- 🇨🇳 Китайские ИИ-источники ---
    'https://pandaily.com/feed/',                      # Pandaily (англ., про Китай)
    'https://www.qbitai.com/feed',                     # QbitAI (специализированный ИИ)
    'https://www.infoq.cn/feed',                       # InfoQ CN (техсообщество)
]

TECH_FEEDS = [
    # --- Западные техно-СМИ ---
    'https://techcrunch.com/feed/',
    'https://arstechnica.com/feed/',
    'https://tech.eu/feed/',
    'https://www.theregister.com/headlines.atom',
    # --- ⚙️ Инженерия × новые технологии ---
    'https://hackaday.com/feed/',                      # Инженерные проекты
    'https://www.therobotreport.com/feed/',            # Робототехника
    'https://semiengineering.com/feed/',               # Чипы и полупроводники
    'https://www.eetimes.com/feed/',                   # Электроника
    'https://www.extremetech.com/feed',                # ExtremeTech
    'https://www.tomshardware.com/feeds/all',          # Железо
    'https://phys.org/rss-feed/',                      # Наука + инженерия
    'https://spectrum.ieee.org/feeds/feed.rss',        # IEEE Spectrum (альтернативный URL)
    # --- Русские техно-источники ---
    'https://3dnews.ru/news/rss/',
    'https://www.ixbt.com/export/news.rss',
    # --- 🇨🇳 Китайские техно-источники ---
    'https://www.chinatechnews.com/feed',              # ChinaTechNews (альтернативный URL)
    'https://www.scmp.com/rss/36/feed',                # SCMP Tech (альтернативный URL)
    'http://rss.sina.com.cn/news/allnews/tech.xml',    # Sina Tech (альтернативный URL)
    'https://www.36kr.com/feed',                       # 36Kr (главное техно-СМИ Китая)
    'https://www.ithome.com/rss/',                     # ITHome (популярный техно-портал)
    'https://www.geekpark.net/rss',                    # GeekPark (инновации и стартапы)
]

MEMORY_FILE = "posted_news.json"
groq_client = Groq(api_key=GROQ_API_KEY)

# ========== ФУНКЦИИ ПАМЯТИ ==========
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
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
    
    all_news = []
    current_index = start_index
    for i in range(num_feeds):
        feed_idx = (current_index + i) % num_feeds
        news = get_news_from_rss(feeds[feed_idx], max_items=2)
        all_news.extend(news)
    
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
    
    if current_category == 'ai':
        feeds = AI_FEEDS
        start_index = ai_index
        print(f"🤖 Источники AI: {len(feeds)} каналов")
    else:
        feeds = TECH_FEEDS
        start_index = tech_index
        print(f"💻 Источники TECH: {len(feeds)} каналов")
    
    raw_news, next_index = get_news_from_feeds(feeds, start_index)
    
    unique_news = [item for item in raw_news if item['link'] not in posted_links]
    print(f"📊 Найдено {len(raw_news)} новостей, из них {len(unique_news)} новых.\n")
    
    if not unique_news:
        print("🔄 Новых новостей нет. Переключаем категорию.")
        next_category = 'tech' if current_category == 'ai' else 'ai'
        memory['category'] = next_category
        save_memory(memory)
        return
    
    news_item = unique_news[0]
    print(f"📝 Публикую: {news_item['title'][:40]}...")
    
    try:
        post = create_post(news_item)
        if post_to_telegram(post):
            posted_links.append(news_item['link'])
            
            next_category = 'tech' if current_category == 'ai' else 'ai'
            
            # Храним 500 ссылок (источников теперь больше)
            memory['posted_links'] = posted_links[-500:]
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
