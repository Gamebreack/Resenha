# Global English-Language Tech News RSS Feeds Research

For: Resenha news bot project  
Date: 2026-06-19  
Criteria: non-paywalled, English, global tech focus, RSS/Atom accessible without login/subscription

## Recommended Feeds (verified working)

| # | Source | Feed URL | Format | Update Frequency | Paywall Status | Brazil Relevance |
|---|--------|----------|--------|------------------|----------------|------------------|
| 1 | **The Verge – Tech** | https://www.theverge.com/rss/tech/index.xml | Atom | Hourly/daily | Soft paywall on some articles; **RSS feed is free and requires no login** | Occasional; US-centric but covers global product/policy news |
| 2 | **Ars Technica – Biz & IT** | https://arstechnica.com/information-technology/feed/ | RSS 2.0 | Hourly | Public RSS is free; full-text subscriber feed exists behind login | Low direct Brazil coverage; strong on security/enterprise/tech policy |
| 3 | **TechCrunch** | https://techcrunch.com/feed/ | RSS 2.0 | Hourly | Free; no login required for RSS | Moderate; has dedicated [Brazil tag/section](https://techcrunch.com/tag/brazil) with startup/VC coverage |
| 4 | **Engadget** | https://www.engadget.com/feed/ | RSS 2.0 | Hourly | Free; ad-supported | Low; global consumer tech, US-heavy |
| 5 | **Rest of World** | https://restofworld.org/feed/latest/ | RSS 2.0 | Daily (2×/day) | Free; no paywall | **High**; explicitly covers Global South tech, with many Brazil stories (Pix, TikTok data center, Meituan launch, etc.) |

## Verification

All five URLs were fetched with `curl` and parsed as valid RSS/Atom using Python's `xml.etree.ElementTree`. HTTP 200 responses with XML content-types were confirmed.

```
✓ The Verge Tech: Atom, 30985 bytes, HTTP 200
✓ Ars Technica Biz & IT: RSS 2.0, 74252 bytes, HTTP 200
✓ TechCrunch: RSS 2.0, 18288 bytes, HTTP 200
✓ Engadget: RSS 2.0, 34813 bytes, HTTP 200
✓ Rest of World: RSS 2.0, 14492 bytes, HTTP 200
```

## Notes

- **The Verge**: The site recently introduced a soft paywall for some articles, but the RSS feed itself remains open and does not require authentication. Feed is Atom and tech-section-specific.
- **Ars Technica**: The canonical section feed is `/information-technology/feed/` (not `/technology-lab`, which redirects). Public feed contains excerpts/full text depending on article.
- **TechCrunch**: Broad startup/tech coverage; good for funding news and product launches.
- **Engadget**: Consumer electronics and reviews focus; lighter news tone.
- **Rest of World**: Best choice for non-Western/global tech perspective and Brazil relevance.

## Feeds tested but not recommended

| Source | URL | Reason |
|--------|-----|--------|
| Reuters Technology | `https://www.reutersagency.com/feed/?best-topics=tech&post_type=best` | Returns HTML page, not RSS |
| Financial Times Technology | `https://www.ft.com/technology?format=rss` | Hard paywall on articles |
| Wired (main feed) | `https://www.wired.com/feed/rss` | Valid RSS but very broad; includes coupons, deals, shopping, culture — not tech-specific |

## Suggested briefings mix

For a daily/weekly tech briefing:
- **Primary news**: The Verge Tech + TechCrunch
- **Deep analysis/security**: Ars Technica Biz & IT
- **Consumer/gadgets**: Engadget
- **Global/Brazil angle**: Rest of World
