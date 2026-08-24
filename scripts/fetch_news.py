import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests


FEEDS = [
    ("Hacker News", "https://hnrss.org/frontpage", "Software"),
    ("Hacker News / Show", "https://hnrss.org/show", "Open Source"),
    (
        "GitHub Trending",
        "https://cdn.jsdelivr.net/gh/Hyraze/trending-collection@main/api/daily/all.json",
        "Open Source",
    ),
    ("arXiv AI", "https://export.arxiv.org/rss/cs.AI", "Research"),
    ("arXiv ML", "https://export.arxiv.org/rss/cs.LG", "AI"),
    ("arXiv Robotics", "https://export.arxiv.org/rss/cs.RO", "Robotics"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml", "AI"),
    ("Tech Xplore", "https://techxplore.com/rss-feed/", "Research"),
    ("IEEE Spectrum", "https://spectrum.ieee.org/feeds/feed.rss", "Hardware"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/technology", "Software"),
    ("TechCrunch", "https://techcrunch.com/feed/", "Industry"),
]


KEYWORDS = {
    "AI": [
        "ai",
        "artificial intelligence",
        "llm",
        "model",
        "agent",
        "machine learning",
        "neural",
        "inference",
        "transformer",
        "gpu",
    ],
    "Hardware": [
        "gpu",
        "cpu",
        "chip",
        "semiconductor",
        "processor",
        "memory",
        "nvidia",
        "amd",
        "intel",
        "qualcomm",
        "silicon",
        "datacenter",
    ],
    "Robotics": [
        "robot",
        "robotics",
        "humanoid",
        "embodied",
        "autonomous",
        "drone",
        "manipulation",
    ],
    "Software": [
        "software",
        "linux",
        "database",
        "developer",
        "programming",
        "compiler",
        "browser",
        "cloud",
        "security",
        "api",
    ],
    "Open Source": [
        "open source",
        "github",
        "opensource",
        "repository",
        "framework",
        "library",
    ],
    "Industry": [
        "startup",
        "funding",
        "acquisition",
        "ipo",
        "microsoft",
        "apple",
        "google",
        "meta",
        "amazon",
        "nvidia",
    ],
    "Research": [
        "research",
        "paper",
        "study",
        "algorithm",
        "benchmark",
        "arxiv",
    ],
}


def clean(s):
    """Remove HTML/XML and normalize whitespace."""
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", s).strip()


def parse_date(e):
    if getattr(e, "published_parsed", None):
        return datetime.fromtimestamp(
            time.mktime(e.published_parsed),
            timezone.utc,
        ).isoformat()

    if getattr(e, "updated_parsed", None):
        return datetime.fromtimestamp(
            time.mktime(e.updated_parsed),
            timezone.utc,
        ).isoformat()

    return datetime.now(timezone.utc).isoformat()


def category(title, default):
    t = title.lower()

    hits = [
        (sum(1 for k in keywords if k in t), cat)
        for cat, keywords in KEYWORDS.items()
    ]

    best = max(hits)

    return best[1] if best[0] >= 1 else default


def score(title, source):
    t = title.lower()
    s = 45

    s += min(
        30,
        sum(
            1
            for words in KEYWORDS.values()
            for k in words
            if k in t
        ) * 3,
    )

    if source in ("Hacker News", "GitHub Trending", "Hugging Face"):
        s += 10

    if any(
        x in t
        for x in [
            "launch",
            "release",
            "breakthrough",
            "open source",
            "new model",
            "new gpu",
        ]
    ):
        s += 10

    return min(99, s)


def parse_arxiv_entry(e):
    """
    arXiv RSS entries have a different structure from normal news feeds.

    We use the actual entry title as the headline and the abstract
    as the description, while stripping arXiv's embedded metadata.
    """

    title = clean(e.get("title", ""))

    # arXiv occasionally exposes metadata in the title itself.
    title = re.sub(
        r"\s*arXiv:\s*\d+\.\d+v\d+\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()

    # Prefer the actual abstract/summary.
    description = clean(
        e.get("summary", "")
        or e.get("description", "")
    )

    # Remove common arXiv metadata prefixes.
    description = re.sub(
        r"^\s*arXiv:\s*\d+\.\d+v\d+\s*",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(
        r"^\s*Announce Type:\s*\w+\s*",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(
        r"^\s*Abstract:\s*",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = clean(description)

    # Some arXiv feeds can expose the title/metadata inside the summary.
    # If the description still begins with metadata, clean it again.
    description = re.sub(
        r"^arXiv:\d+\.\d+v\d+\s*",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(
        r"^Announce Type:\s*\w+\s*",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(
        r"^Abstract:\s*",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = clean(description)

    return title, description


items = []


for source, url, default in FEEDS:
    try:

        # ---------------------------------------------------------
        # GitHub Trending JSON
        # ---------------------------------------------------------
        if url.endswith(".json"):

            response = requests.get(url, timeout=20)
            response.raise_for_status()

            data = response.json()

            for e in data.get("items", [])[:20]:

                title = e.get("title", "").strip()

                items.append(
                    {
                        "title": title,
                        "url": e.get(
                            "url",
                            "https://github.com/trending",
                        ),
                        "description": clean(
                            e.get("description", "")
                        )[:280],
                        "source": source,
                        "category": category(
                            title,
                            default,
                        ),
                        "kind": "repository",
                        "date": e.get(
                            "pubDate",
                            datetime.now(
                                timezone.utc
                            ).isoformat(),
                        ),
                        "score": score(
                            title,
                            source,
                        ),
                    }
                )

        # ---------------------------------------------------------
        # RSS feeds
        # ---------------------------------------------------------
        else:

            feed = feedparser.parse(url)

            for e in feed.entries[:20]:

                # Special handling for arXiv
                if source.startswith("arXiv"):

                    title, description = parse_arxiv_entry(e)
                    kind = "research paper"

                else:

                    title = clean(
                        e.get("title", "")
                    )

                    description = clean(
                        e.get(
                            "summary",
                            e.get(
                                "description",
                                "",
                            ),
                        )
                    )

                    kind = "article"

                if not title:
                    continue

                items.append(
                    {
                        "title": title,
                        "url": e.get(
                            "link",
                            "#",
                        ),
                        "description": description[:280],
                        "source": source,
                        "category": category(
                            title,
                            default,
                        ),
                        "kind": kind,
                        "date": parse_date(e),
                        "score": score(
                            title,
                            source,
                        ),
                    }
                )

    except Exception as ex:

        print(
            "Feed failed:",
            source,
            ex,
        )


# -------------------------------------------------------------
# Deduplicate
# -------------------------------------------------------------

seen = set()
unique = []

for item in sorted(
    items,
    key=lambda x: x["date"],
    reverse=True,
):

    key = re.sub(
        r"\W",
        "",
        item["title"].lower(),
    )

    if key and key not in seen:

        seen.add(key)
        unique.append(item)


# -------------------------------------------------------------
# Write output
# -------------------------------------------------------------

out = {
    "generated_at": datetime.now(
        timezone.utc
    ).isoformat(),
    "items": unique[:180],
}


Path("data").mkdir(
    exist_ok=True
)

Path("data/news.json").write_text(
    json.dumps(
        out,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


print(
    "Saved",
    len(unique),
    "items",
)
