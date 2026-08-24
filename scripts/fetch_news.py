import json, re, time
from datetime import datetime, timezone
from pathlib import Path
import feedparser, requests

FEEDS = [
 ("Hacker News","https://hnrss.org/frontpage","Software"),
 ("Hacker News / Show","https://hnrss.org/show","Open Source"),
 ("GitHub Trending","https://cdn.jsdelivr.net/gh/Hyraze/trending-collection@main/api/daily/all.json","Open Source"),
 ("arXiv AI","https://export.arxiv.org/rss/cs.AI","Research"),
 ("arXiv ML","https://export.arxiv.org/rss/cs.LG","AI"),
 ("arXiv Robotics","https://export.arxiv.org/rss/cs.RO","Robotics"),
 ("Hugging Face","https://huggingface.co/blog/feed.xml","AI"),
 ("Tech Xplore","https://techxplore.com/rss-feed/","Research"),
 ("IEEE Spectrum","https://spectrum.ieee.org/feeds/feed.rss","Hardware"),
 ("Ars Technica","https://feeds.arstechnica.com/arstechnica/technology","Software"),
 ("TechCrunch","https://techcrunch.com/feed/","Industry"),
]

KEYWORDS = {
 "AI":["ai","artificial intelligence","llm","model","agent","machine learning","neural","inference","transformer","gpu"],
 "Hardware":["gpu","cpu","chip","semiconductor","processor","memory","nvidia","amd","intel","qualcomm","silicon","datacenter"],
 "Robotics":["robot","robotics","humanoid","embodied","autonomous","drone","manipulation"],
 "Software":["software","linux","database","developer","programming","compiler","browser","cloud","security","api"],
 "Open Source":["open source","github","opensource","repository","framework","library"],
 "Industry":["startup","funding","acquisition","ipo","microsoft","apple","google","meta","amazon","nvidia"],
 "Research":["research","paper","study","algorithm","benchmark","arxiv"],
}

def clean(s):
    s=re.sub("<[^>]+>"," ",s or "")
    return re.sub(r"\s+"," ",s).strip()

def parse_date(e):
    if getattr(e,"published_parsed",None):
        return datetime.fromtimestamp(time.mktime(e.published_parsed),timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()

def category(title, default):
    t=title.lower()
    hits=[(sum(1 for k in ks if k in t),cat) for cat,ks in KEYWORDS.items()]
    best=max(hits)
    return best[1] if best[0]>=1 else default

def score(title, source):
    t=title.lower(); s=45
    s+=min(30,sum(1 for words in KEYWORDS.values() for k in words if k in t)*3)
    if source in ("Hacker News","GitHub Trending","Hugging Face"): s+=10
    if any(x in t for x in ["launch","release","breakthrough","open source","new model","new gpu"]): s+=10
    return min(99,s)

items=[]
for source,url,default in FEEDS:
    try:
        if url.endswith(".json"):
            data=requests.get(url,timeout=20).json()
            for e in data.get("items",[])[:20]:
                title=e.get("title","").strip()
                items.append({"title":title,"url":e.get("url","https://github.com/trending"),"description":clean(e.get("description",""))[:280],
                    "source":source,"category":category(title,default),"kind":"repository","date":e.get("pubDate",datetime.now(timezone.utc).isoformat()),"score":score(title,source)})
        else:
            feed=feedparser.parse(url)
            for e in feed.entries[:20]:
                title=clean(e.get("title",""))
                items.append({"title":title,"url":e.get("link","#"),"description":clean(e.get("summary",e.get("description","")))[:280],
                    "source":source,"category":category(title,default),"kind":"article/paper","date":parse_date(e),"score":score(title,source)})
    except Exception as ex:
        print("Feed failed:",source,ex)

seen=set(); unique=[]
for i in sorted(items,key=lambda x:x["date"],reverse=True):
    key=re.sub(r"\W","",i["title"].lower())
    if key and key not in seen:
        seen.add(key); unique.append(i)

out={"generated_at":datetime.now(timezone.utc).isoformat(),"items":unique[:180]}
Path("data").mkdir(exist_ok=True)
Path("data/news.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("Saved",len(unique),"items")
