# Configuração

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

- `DISCORD_BOT_TOKEN`: token do bot.
- `DISCORD_CHANNEL_ID`: canal de publicação.
- `GEMINI_API_KEY`: chave da Google AI Studio.
- `GOOGLE_SHEET_ID`: planilha da carteira.
- `GOOGLE_SHEET_TAB`: aba da carteira, normalmente `Consolidado`.
- `CACHE_DB_PATH`: caminho do SQLite local.
- `PREMARKET_HOUR`: hora local do pré-mercado.
- `GOOGLE_TOKEN_PATH`: caminho do arquivo de token OAuth do Google (opcional; possui um padrão local).

Nunca versione `.env` ou tokens OAuth.

## Google Workspace

As integrações de Sheets, Gmail e Calendar usam um arquivo de token OAuth do Google configurado via `GOOGLE_TOKEN_PATH`. O token deve possuir os escopos necessários para ler a planilha, a agenda e os emails definidos pelo código.

## Instalação

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

Para verificar a configuração, execute os testes:

```bash
python -m pytest tests/ -q
```

Erros de credencial normalmente indicam variável ausente, token OAuth expirado ou ID incorreto da planilha/canal.
