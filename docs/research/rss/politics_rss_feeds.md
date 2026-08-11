# Global English-language politics/current affairs RSS feeds

Feeds verified live on 2026-06-19. All return valid RSS/Atom XML and are free to access.

| Source | Feed URL | Update frequency | Paywall | Ideology |
|---|---|---|---|---|
| BBC News – World | https://feeds.bbci.co.uk/news/world/rss.xml | ~hourly / TTL 15 min | Free | Center / mainstream international |
| The Guardian – World | https://www.theguardian.com/world/rss | Continuous, several times daily | Free | Left / liberal |
| Al Jazeera English – All News | https://www.aljazeera.com/xml/rss/all.xml | Continuous, often hourly | Free | Center-left / progressive international |
| The American Conservative | https://www.theamericanconservative.com/feed/ | Hourly (`sy:updatePeriod` hourly) | Free | Right / conservative, foreign-policy realist |

## Notes
- BBC, Guardian and Al Jazeera are strong for global breaking news.
- The Guardian feed includes full article text where rights allow.
- The American Conservative is the right-leaning anchor; it currently runs a daily “Iran War” tracker and non-interventionist foreign-policy analysis.
- Reuters and AP no longer publish usable public RSS feeds; the Economist and National Review feeds are Cloudflare-protected and/or paywalled, so they were not selected.

## Verification
All four URLs were fetched with `curl` and returned HTTP 200 with `application/rss+xml` or `text/xml` payloads containing current items dated 2026-06-19.
