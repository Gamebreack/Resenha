# Glossary

## Domain Terms

| Term | Definition |
|------|------------|
| **Ativo** | A financial instrument tracked in the portfolio. In Resenha, always a B3-listed ticker (e.g., `ITUB4`, `TAEE11`). |
| **B3** | Brasil Bolsa Balcão — the Brazilian stock exchange. All tickers are B3-listed. |
| **FII** | Fundo de Investimento Imobiliário — Brazilian real estate investment fund. Tracked as tickers ending in `11` (e.g., `BRCO11`, `KNCR11`). |
| **Fiagro** | Fundo de Investimento do Agronegócio — agricultural investment fund. `RURA11` is the sole Fiagro in the portfolio. |
| **Consolidado** | The primary tab in the Google Sheet containing the live portfolio snapshot: ticker, sector, target weight, quantity, average price, current price, invested total, current value, P&L, and status. |
| **Ledger** | The transaction history tab in the Google Sheet. Not used for briefing generation. |
| **Pre-market** | The ~7am BRT briefing before the B3 market opens (10am BRT). Focus: overnight/global news + portfolio positions. |
| **EOD** | End-of-day wrap at ~7pm BRT after market close. Focus: daily price action, macro moves, news highlights. |
| **Saturday long-form** | Weekly recap delivered Saturday. Covers the week's performance per asset, macro highlights, and portfolio-level summary. |
| **Bias annotation** | Per-source ideological leaning flagged by the LLM (e.g., "InfoMoney — center-right business bias"). Displayed alongside each news item. |
| **Column neutrality** | A score or flag indicating whether a specific article is editorially neutral vs. opinion-driven. |
| **Raw data assembler** | The component that merges price data, macro indicators, and news snippets into a structured context object fed to the LLM prompt. |
| **Prompt builder** | The component that assembles the final LLM prompt from the raw data context, voice instructions, and formatting rules. |
| **Briefing memory** | The text of the most recently generated briefing for a given style, persisted so the next briefing can avoid repeating the same information. |
| **Agenda da Semana** | A briefing section summarizing the user's upcoming calendar events for the next 7 days and recent unread emails. |
| **Relevant emails** | Unread Gmail messages received in the last 24 hours, limited to the 5 most recent for inclusion in the agenda. |
| **Week events** | Calendar events from the current time through the next 7 days. |
