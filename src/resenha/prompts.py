from datetime import date, datetime

from resenha.assembler import BriefingContext


def _format_event_time(value: datetime | date) -> str:
    """Format a calendar event start time for the prompt."""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    return value.strftime("%d/%m/%Y")


def build_briefing_prompt(context: BriefingContext, style: str = "pre-market", previous_briefing: str | None = None) -> str:
    lines = [
        f"Você é um assistente financeiro brasileiro com tom relaxado e informal.",
        f"Estilo do briefing: {style}",
    ]
    if previous_briefing:
        previous_briefing = previous_briefing[:2000]
        lines.append("")
        lines.append("## Resumo Anterior")
        lines.append(previous_briefing)
        lines.append("")
        lines.append("Instrução: Evite repetir informações já presentes no resumo anterior; destaque apenas o que é novo ou mudou.")
    lines.append("")
    lines.append("## Portfólio")
    for pos in context.portfolio:
        lines.append(f"- {pos.asset.ticker} ({pos.asset.sector}): preço R$ {pos.price.get('price', 'N/A') if pos.price else 'N/A'}")
    lines.append("")
    lines.append("## Agenda da Semana")
    if context.agenda and (context.agenda.events or context.agenda.emails):
        for event in context.agenda.events:
            location = f" ({event.location})" if event.location else ""
            lines.append(f"- [{_format_event_time(event.start)}] {event.summary}{location}")
        for email in context.agenda.emails:
            sender = email.sender or "Desconhecido"
            subject = email.subject or "(Sem assunto)"
            lines.append(f"- [{sender}] {subject}")
    else:
        lines.append("Nada relevante por enquanto.")
    lines.append("")
    lines.append("## Macro")
    if context.macro:
        lines.append(f"- SELIC: {context.macro.selic}%")
        lines.append(f"- IPCA: {context.macro.ipca}%")
        lines.append(f"- Dólar: R$ {context.macro.dolar}")
    lines.append("")
    lines.append("## Notícias por Ativo")
    for ticker, items in context.news_by_asset.items():
        lines.append(f"### {ticker}")
        for item in items[:3]:
            lines.append(f"- [{item.source}] {item.title}")
    lines.append("")
    lines.append("## Notícias Gerais")
    for item in context.general_news[:70]:
        lines.append(f"- [{item.source}] {item.title}")
    lines.append("")
    lines.append("Instruções:")
    lines.append("1. Resuma as notícias mais relevantes por ativo e inclua uma seção final com notícias gerais (Brasil, mundo, tecnologia).")
    lines.append("2. Anote o viés ideológico de cada fonte entre parênteses.")
    lines.append("3. Mantenha o tom relaxado, como se estivesse conversando com um amigo.")
    lines.append("4. Use português brasileiro informal.")
    return "\n".join(lines)
