import discord
from resenha.adaptive import inject_feedback
from resenha.gemini import GeminiClient
from resenha.prompts import build_briefing_prompt
from resenha.assembler import BriefingContext


def _detect_category(title: str) -> str:
    """Detect the category of a section based on header keywords."""
    title_upper = title.upper()

    macro_keywords = ("SELIC", "IPCA", "DÓLAR", "DOLAR", "CÂMBIO", "CAMBIO")
    portfolio_keywords = ("MACRO", "CARTEIRA", "PORTFOLIO", "IBOV", "IBOVESPA")

    for kw in macro_keywords:
        if kw in title_upper:
            return "macro"
    for kw in portfolio_keywords:
        if kw in title_upper:
            return "portfolio"
    return "news"


CATEGORY_COLORS = {
    "macro": 0x2ECC71,
    "portfolio": 0x3498DB,
    "news": 0xE67E22,
}


def generate_briefing(context: BriefingContext, gemini: GeminiClient, style: str = "pre-market", feedback_text: str = "", previous_briefing: str | None = None) -> str:
    prompt = build_briefing_prompt(context, style, previous_briefing=previous_briefing)
    prompt = inject_feedback(prompt, feedback_text)
    return gemini.generate(prompt, max_tokens=4000)


def generate_embeds(briefing_text: str) -> list[discord.Embed]:
    sections = _split_into_sections(briefing_text)
    embeds = []
    for title, body in sections[:10]:  # Discord limit: 10 embeds
        desc = body[:4096]  # Discord limit: 4096 chars per description
        category = _detect_category(title)
        color = CATEGORY_COLORS.get(category, 0x00AAFF)
        embed = discord.Embed(title=title, description=desc, color=color)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="Resenha · Seu briefing diário")
        embed.set_author(name="Resenha")
        embeds.append(embed)
    return embeds


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """Split briefing text into (title, body) sections by headers."""
    lines = text.splitlines()
    sections = []
    current_title = "Resenha"
    current_body: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if current_body:
                sections.append((current_title, "\n".join(current_body).strip()))
            current_title = stripped[3:].strip()
            current_body = []
        else:
            current_body.append(line)

    if current_body or not sections:
        sections.append((current_title, "\n".join(current_body).strip()))

    return sections
