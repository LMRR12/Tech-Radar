# TECHRADAR

A static GitHub Pages dashboard that aggregates technical signals from RSS/JSON feeds.

## What it does

- AI
- Software
- Hardware
- Robotics
- Research
- Open Source
- Industry
- Search and category filters
- Signal scoring
- Automatic feed refresh every 3 hours through GitHub Actions

## Deploy

1. Create a new GitHub repository.
2. Upload all files in this folder.
3. Go to **Settings → Pages**.
4. Select **GitHub Actions** as the source.
5. Run **Actions → Update Tech Radar → Run workflow** once.
6. Your Pages site will then update automatically.

The dashboard is intentionally static. GitHub Actions performs the feed collection, so the browser does not need to bypass RSS CORS restrictions.

## Sources

Hacker News, GitHub Trending, arXiv, Hugging Face, Tech Xplore, IEEE Spectrum, Ars Technica and TechCrunch.

## Important

Some publishers change or retire RSS feeds. If a source stops updating, replace its URL in `scripts/fetch_news.py`.
