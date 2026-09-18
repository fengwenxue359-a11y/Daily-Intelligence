import feedparser
from openai import OpenAI
import json
import os
import datetime

# ================= 你的情报源矩阵 =================
RSS_FEEDS = [
    # 【财经/股市/商业】
    {"name": "华尔街日报-市场", "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "category": "财经"},
    {"name": "CNBC-财经", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", "category": "财经"},
    
    # 【AI/科技】
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "category": "AI科技"},

    # 【书籍/文化】
    {"name": "纽约时报书评", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Books.xml", "category": "书籍"},

    # 【个人成长/学习视频】
    {"name": "Huberman Lab (YouTube)", "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC2D2CMWXMOVWx7giW1n3LIg", "category": "成长视频"},
]

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def process_content(text, title, category):
    prompt = f"""
    你是一位极其专业的内容主编。请对以下内容进行处理。
    分类：{category}
    标题：{title}
    内容：{text[:2000]}...

    请严格输出JSON格式（不要有多余文字）：
    {{
        "title_cn": "精准的中文标题",
        "title_en": "英文原标题（如果是中文源则写中文）",
        "summary_cn": "150字的中文摘要（有洞察力，说明为什么值得看）",
        "summary_en": "英文摘要（如果是中文源，则将中文摘要翻译成英文）"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = response.choices[0].message.content
        if content.startswith("```json"): content = content[7:-3]
        return json.loads(content)
    except Exception as e:
        print(f"AI处理失败: {e}")
        return None

def generate_daily_intelligence():
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    items = []
    
    for feed_info in RSS_FEEDS:
        print(f"正在抓取: {feed_info['name']}")
        feed = feedparser.parse(feed_info['url'])
        for entry in feed.entries[:2]:
            summary = entry.get('summary', '')
            if 'content' in entry: summary = entry.content[0].value
            
            processed = process_content(summary, entry.title, feed_info['category'])
            if processed:
                items.append({
                    "category": feed_info['category'],
                    "source": feed_info['name'],
                    "original_link": entry.link,
                    **processed
                })

    data = {"date": today_str, "items": items}
    os.makedirs("briefs/archive", exist_ok=True)
    with open("briefs/latest.json", "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
    with open(f"briefs/archive/{today_str}.json", "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

    history = sorted([f.replace('.json', '') for f in os.listdir("briefs/archive") if f.endswith('.json')], reverse=True)
    with open("briefs/history.json", "w", encoding="utf-8") as f: json.dump(history, f, ensure_ascii=False)
    print(f"成功生成 {len(items)} 条情报。")

if __name__ == "__main__":
    generate_daily_intelligence()
