import feedparser
import requests
import time

FEEDS = [
    # =====================================================
    # === РАБОЧИЕ (26 источников, уже проверены) ==========
    # =====================================================
    ("✅ OpenAI Blog", 'https://openai.com/blog/rss.xml'),
    ("✅ DeepMind", 'https://deepmind.google/blog/rss.xml'),
    ("✅ Google AI", 'https://blog.google/technology/ai/rss/'),
    ("✅ HuggingFace", 'https://huggingface.co/blog/feed.xml'),
    ("✅ The Decoder", 'https://the-decoder.com/feed/'),
    ("✅ MIT TR AI", 'https://www.technologyreview.com/topic/artificial-intelligence/feed'),
    ("✅ arXiv cs.AI", 'https://rss.arxiv.org/rss/cs.AI'),
    ("✅ Synced Review", 'https://www.syncedreview.com/feed/'),
    ("✅ TechCrunch AI", 'https://techcrunch.com/category/artificial-intelligence/feed/'),
    ("✅ Verge AI", 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml'),
    ("✅ Neurohive RU", 'https://neurohive.io/ru/feed/'),
    ("✅ Pandaily CN", 'https://pandaily.com/feed/'),
    ("✅ TechCrunch", 'https://techcrunch.com/feed/'),
    ("✅ Ars Technica", 'https://arstechnica.com/feed/'),
    ("✅ Tech.eu", 'https://tech.eu/feed/'),
    ("✅ The Register", 'https://www.theregister.com/headlines.atom'),
    ("✅ Hackaday", 'https://hackaday.com/feed/'),
    ("✅ Robot Report", 'https://www.therobotreport.com/feed/'),
    ("✅ SemiEngineering", 'https://semiengineering.com/feed/'),
    ("✅ EE Times", 'https://www.eetimes.com/feed/'),
    ("✅ ExtremeTech", 'https://www.extremetech.com/feed'),
    ("✅ Tom's Hardware", 'https://www.tomshardware.com/feeds/all'),
    ("✅ Phys.org", 'https://phys.org/rss-feed/'),
    ("✅ 3DNews RU", 'https://3dnews.ru/news/rss/'),
    ("✅ iXBT RU", 'https://www.ixbt.com/export/news.rss'),
    ("✅ TechNode CN", 'https://technode.com/feed/'),
    
    # =====================================================
    # === АЛЬТЕРНАТИВНЫЕ URL для ранее мёртвых ============
    # =====================================================
    # Anthropic (был 404)
    ("🔸 Anthropic alt1", 'https://www.anthropic.com/news/rss.xml'),
    ("🔸 Anthropic alt2", 'https://www.anthropic.com/research/rss.xml'),
    ("🔸 Anthropic alt3", 'https://www.anthropic.com/blog/rss'),
    
    # Meta AI (был 404)
    ("🔸 Meta AI alt1", 'https://ai.meta.com/blog/rss'),
    ("🔸 Meta AI alt2", 'https://ai.meta.com/blog/index.xml'),
    ("🔸 Meta AI alt3", 'https://engineering.fb.com/category/ai/feed/'),
    
    # Habr AI (был 404)
    ("🔸 Habr AI alt1", 'https://habr.com/ru/rss/hub/artificial_intelligence/'),
    ("🔸 Habr AI alt2", 'https://habr.com/ru/rss/hub/artificial_intelligence/?fl=ru'),
    ("🔸 Habr AI alt3", 'https://habr.com/ru/rss/hub/MachineLearning/'),
    
    # IEEE Spectrum (был 404)
    ("🔸 IEEE Spectrum alt1", 'https://spectrum.ieee.org/feeds/feed.rss'),
    ("🔸 IEEE Spectrum alt2", 'https://spectrum.ieee.org/rss'),
    ("🔸 IEEE Spectrum alt3", 'https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss'),
    
    # VentureBeat AI (был 429 — rate limit)
    ("🔸 VentureBeat AI", 'https://venturebeat.com/category/ai/feed/'),
    ("🔸 VentureBeat alt", 'https://venturebeat.com/feed/'),
    
    # MarkTechPost (был 202)
    ("🔸 MarkTechPost alt1", 'https://www.marktechpost.com/feed'),
    ("🔸 MarkTechPost alt2", 'https://marktechpost.com/feed/'),
    ("🔸 MarkTechPost alt3", 'https://www.marktechpost.com/feed/rss/'),
    
    # ChinaTechNews (был 403)
    ("🔸 ChinaTechNews alt1", 'https://www.chinatechnews.com/feed'),
    ("🔸 ChinaTechNews alt2", 'https://www.chinatechnews.com/feed/rss'),
    ("🔸 ChinaTechNews alt3", 'https://www.chinatechnews.com/?feed=rss2'),
    
    # CGTN Tech (был 404)
    ("🔸 CGTN Tech alt1", 'https://www.cgtn.com/subscribe/rss/section/tech'),
    ("🔸 CGTN Tech alt2", 'https://www.cgtn.com/rss/technology'),
    ("🔸 CGTN Tech alt3", 'https://www.cgtn.com/subscribe/rss/section/sci-tech'),
    
    # SCMP Tech (был 404)
    ("🔸 SCMP alt1", 'https://www.scmp.com/rss/91/feed'),
    ("🔸 SCMP alt2", 'https://www.scmp.com/rss/36/feed'),
    ("🔸 SCMP alt3", 'https://www.scmp.com/rss/tech'),
    
    # Sina Tech (был 404)
    ("🔸 Sina Tech alt1", 'https://tech.sina.com.cn/rss/rollnews.xml'),
    ("🔸 Sina Tech alt2", 'https://rss.sina.com.cn/news/allnews/tech.xml'),
    
    # New Atlas (был 0 новостей)
    ("🔸 New Atlas alt1", 'https://newatlas.com/feed/'),
    ("🔸 New Atlas alt2", 'https://newatlas.com/rss-feed/'),
    ("🔸 New Atlas alt3", 'https://newatlas.com/technology/feed/'),
    
    # =====================================================
    # === 🇨🇳 НОВЫЕ КИТАЙСКИЕ КАНДИДАТЫ ===================
    # =====================================================
    # ИИ-компании Китая
    ("🇨🇳 DeepSeek Blog", 'https://www.deepseek.com/rss.xml'),
    ("🇨🇳 DeepSeek alt", 'https://api-docs.deepseek.com/blog/rss.xml'),
    ("🇨🇳 DeepSeek alt2", 'https://www.deepseek.com/blog/rss'),
    ("🇨🇳 Baidu Research", 'https://research.baidu.com/Blog/rss'),
    ("🇨🇳 Baidu AI alt", 'https://ai.baidu.com/ai-doc/FEED/rss'),
    ("🇨🇳 Tencent AI Lab", 'https://ai.tencent.com/ailab/rss'),
    ("🇨🇳 Tencent alt", 'https://cloud.tencent.com/developer/feed/rss'),
    ("🇨🇳 Alibaba DAMO", 'https://damo.alibaba.com/rss'),
    ("🇨🇳 Alibaba Cloud", 'https://www.alibabacloud.com/blog/rss'),
    
    # Китайские техно-СМИ
    ("🇨🇳 36Kr", 'https://www.36kr.com/feed'),
    ("🇨🇳 36Kr alt", 'https://36kr.com/feed'),
    ("🇨🇳 36Kr RSSHub", 'https://rsshub.app/36kr/news/latest'),
    ("🇨🇳 36Kr RSSHub2", 'https://rsshub.app/36kr/newsflashes'),
    ("🇨🇳 ITHome", 'https://www.ithome.com/rss/'),
    ("🇨🇳 ITHome alt", 'https://m.ithome.com/rss/'),
    ("🇨🇳 QbitAI", 'https://www.qbitai.com/feed'),
    ("🇨🇳 QbitAI RSSHub", 'https://rsshub.app/qbitai'),
    ("🇨🇳 QbitAI alt", 'https://www.qbitai.com/category/资讯/feed'),
    ("🇨🇳 Jiqizhixin", 'https://www.jiqizhixin.com/rss'),
    ("🇨🇳 Jiqizhixin alt", 'https://www.jiqizhixin.com/daily/feed'),
    ("🇨🇳 cnBeta", 'https://www.cnbeta.com.tw/backend.php'),
    ("🇨🇳 cnBeta alt1", 'https://rss.cnbeta.com/'),
    ("🇨🇳 cnBeta alt2", 'https://www.cnbeta.com.tw/rss'),
    ("🇨🇳 InfoQ CN", 'https://www.infoq.cn/public/v1/article/getList?token='),
    ("🇨🇳 InfoQ CN RSS", 'https://www.infoq.cn/feed'),
    ("🇨🇳 GeekPark", 'https://www.geekpark.net/rss'),
    ("🇨🇳 PingWest", 'https://www.pingwest.com/rss'),
    ("🇨🇳 Huxiu (Tiger)", 'https://www.huxiu.com/rss'),
    ("🇨🇳 Huxiu RSSHub", 'https://rsshub.app/huxiu/article'),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
}

print("=" * 80)
print("ПОЛНАЯ ПРОВЕРКА RSS-ИСТОЧНИКОВ")
print("=" * 80)

ok_count = 0
alt_ok_count = 0
results = []

for name, url in FEEDS:
    try:
        resp = requests.get(url, timeout=20, headers=HEADERS, allow_redirects=True)
        if resp.status_code != 200:
            line = f"❌ {name}: HTTP {resp.status_code} — {url}"
            print(line)
            results.append(line)
            continue
        feed = feedparser.parse(resp.content)
        n = len(feed.entries)
        if n == 0:
            line = f"⚠️ {name}: ответ 200, но 0 новостей — {url}"
            print(line)
            results.append(line)
        else:
            ok_count += 1
            if "alt" in name.lower() or "🔸" in name:
                alt_ok_count += 1
            latest = feed.entries[0].get('title', '?')[:55]
            line = f"✅ {name}: {n} новостей. Свежая: {latest}"
            print(line)
            results.append(line)
    except Exception as e:
        line = f"❌ {name}: ОШИБКА {type(e).__name__}: {str(e)[:60]} — {url}"
        print(line)
        results.append(line)
    
    # Небольшая пауза, чтобы не получить 429
    time.sleep(0.3)

print("=" * 80)
print(f"ИТОГО: рабочих {ok_count} из {len(FEEDS)}")
print(f"Из них АЛЬТЕРНАТИВНЫХ URL, которые ожили: {alt_ok_count}")
print("=" * 80)
