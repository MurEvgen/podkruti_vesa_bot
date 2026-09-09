import feedparser
import requests

FEEDS = [
    ("OpenAI Blog", 'https://openai.com/blog/rss.xml'),
    ("Anthropic", 'https://www.anthropic.com/rss.xml'),
    ("DeepMind", 'https://deepmind.google/blog/rss.xml'),
    ("Google AI", 'https://blog.google/technology/ai/rss/'),
    ("Meta AI", 'https://ai.meta.com/blog/rss/'),
    ("HuggingFace", 'https://huggingface.co/blog/feed.xml'),
    ("The Decoder", 'https://the-decoder.com/feed/'),
    ("MarkTechPost", 'https://www.marktechpost.com/feed/'),
    ("MIT TR AI", 'https://www.technologyreview.com/topic/artificial-intelligence/feed'),
    ("arXiv cs.AI", 'https://rss.arxiv.org/rss/cs.AI'),
    ("VentureBeat AI", 'https://venturebeat.com/category/ai/feed/'),
    ("Synced Review", 'https://www.syncedreview.com/feed/'),
    ("TechCrunch AI", 'https://techcrunch.com/category/artificial-intelligence/feed/'),
    ("Verge AI", 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml'),
    ("Neurohive RU", 'https://neurohive.io/ru/feed/'),
    ("Habr AI RU", 'https://habr.com/ru/hub/artificial_intelligence/rss/'),
    ("Pandaily CN", 'https://pandaily.com/feed/'),
    ("ChinaTechNews CN", 'https://www.chinatechnews.com/rss'),
    ("Sina Tech CN", 'http://rss.sina.com.cn/tech/index.xml'),
    ("CGTN Tech CN", 'https://www.cgtn.com/rss/tech'),
    ("TechCrunch", 'https://techcrunch.com/feed/'),
    ("Ars Technica", 'https://arstechnica.com/feed/'),
    ("Tech.eu", 'https://tech.eu/feed/'),
    ("The Register", 'https://www.theregister.com/headlines.atom'),
    ("IEEE Spectrum", 'https://spectrum.ieee.org/rss.xml'),
    ("Hackaday", 'https://hackaday.com/feed/'),
    ("Robot Report", 'https://www.therobotreport.com/feed/'),
    ("SemiEngineering", 'https://semiengineering.com/feed/'),
    ("EE Times", 'https://www.eetimes.com/feed/'),
    ("New Atlas", 'https://newatlas.com/rss'),
    ("ExtremeTech", 'https://www.extremetech.com/feed'),
    ("Tom's Hardware", 'https://www.tomshardware.com/feeds/all'),
    ("Phys.org", 'https://phys.org/rss-feed/'),
    ("3DNews RU", 'https://3dnews.ru/news/rss/'),
    ("iXBT RU", 'https://www.ixbt.com/export/news.rss'),
    ("TechNode CN", 'https://technode.com/feed/'),
    ("SCMP Tech CN", 'https://www.scmp.com/rss/369480/rss.xml'),
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; FeedChecker/1.0)'}

print("=" * 70)
print("ПРОВЕРКА RSS-ИСТОЧНИКОВ")
print("=" * 70)

ok_count = 0
for name, url in FEEDS:
    try:
        resp = requests.get(url, timeout=15, headers=HEADERS)
        if resp.status_code != 200:
            print(f"❌ {name}: HTTP {resp.status_code} — {url}")
            continue
        feed = feedparser.parse(resp.content)
        n = len(feed.entries)
        if n == 0:
            print(f"⚠️ {name}: ответ 200, но 0 новостей (возможно мёртв) — {url}")
        else:
            ok_count += 1
            latest = feed.entries[0].get('title', '?')[:50]
            print(f"✅ {name}: {n} новостей. Свежая: {latest}")
    except Exception as e:
        print(f"❌ {name}: ОШИБКА {type(e).__name__} — {url}")

print("=" * 70)
print(f"ИТОГО: рабочих {ok_count} из {len(FEEDS)}")
