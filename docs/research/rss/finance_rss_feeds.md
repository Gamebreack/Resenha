# Global English-language Finance/Economics RSS Feeds

Verified non-paywalled RSS/Atom feeds suitable for a daily/weekly briefing.

| # | Source | Feed URL | Category | Typical Update Frequency | Paywall Status |
|---|--------|----------|----------|--------------------------|----------------|
| 1 | CNBC – Finance | https://www.cnbc.com/id/10000664/device/rss/rss.html | Finance / Markets | Multiple times per day (breaking) | Free – no login required for RSS |
| 2 | Investing.com – Stock Market News | https://www.investing.com/rss/news_25.rss | Stock markets / Global finance | Very frequent (15–30+ posts/day during market hours) | Free – ad-supported, no login for RSS |
| 3 | The Guardian – Business | https://www.theguardian.com/business/rss | Business / Economics / Markets | Several times per day | Free – RSS includes full article text; no subscription required |
| 4 | NPR – Economy | https://feeds.npr.org/1017/rss.xml | U.S. & world economy / Fed / policy | Daily | Free – public radio; no login required |
| 5 | Fortune | https://fortune.com/feed | General business / Finance / Leadership | Hourly (feed declares hourly updates) | Free RSS; individual articles may show registration prompts but feed itself is open |

## Verification Notes
- All five URLs were fetched with `curl` and returned valid RSS 2.0 XML containing recent `<item>` entries.
- Feeds tested rejected or unavailable during research (not recommended):
  - Reuters Business (`https://www.reuters.com/business/rss/`) → HTTP 401 DataDome protected.
  - Yahoo Finance RSS (`https://www.yahoo.com/news/rss/finance`) → HTTP 403 Forbidden.
  - Axios (`https://www.axios.com/feeds/feed.rss`) → Cloudflare challenge/blocked.
- These feeds are global in scope and publish in English.
