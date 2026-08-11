# Resenha

Bot diário de briefings de notícias financeiras para Discord, alimentado por LLM.

O Resenha lê a carteira de investimentos a partir de uma planilha Google, coleta preços, dados macroeconômicos e notícias RSS, gera uma análise em português brasileiro via Gemini Flash e entrega o briefing em embeds do Discord.

## Funcionalidades

- Briefings pré-mercado, fim de dia e long-form semanal.
- Cotações e dados macroeconômicos com cache local SQLite.
- Agregação de notícias RSS por categorias.
- Resumos agrupados por ativo e tema.
- Anotação de viés das fontes.
- Memória do briefing anterior e adaptação baseada em reações.
- Agenda diária integrada a Google Sheets, Gmail e Calendar.

## Requisitos

- Python 3.11+
- Token de bot do Discord e ID do canal.
- Chave da Google AI Studio/Gemini.
- Credenciais Google para Sheets, Gmail e Calendar.

## Configuração

1. Crie um ambiente virtual e instale o projeto:

   ```bash
   python -m venv .venv
   . .venv/bin/activate
   pip install -e '.[dev]'
   ```

2. Copie `.env.example` para `.env` e preencha os segredos e IDs necessários.

3. Para integrações Google, configure o OAuth conforme `docs/configuration.md`.

## Execução

```bash
python -m resenha --once pre-market
python -m resenha --once eod
python -m resenha --once long-form
```

A execução recorrente é feita externamente pelo scheduler/cron.

## Desenvolvimento

```bash
python -m pytest tests/ -q
python -m mypy src/
```

Ambos devem passar antes de um commit.

## Documentação

- [Arquitetura](docs/architecture.md)
- [Configuração](docs/configuration.md)
- [Operação](docs/operations.md)
- [Governança e roadmap](docs/megaplan/megaplan.md)
- [Backlog](docs/megaplan/backlog.md)

## Governança

O projeto segue o ciclo Megaplan: documentar (pré) → red → green → blue → documentar (pós) → concluir. Consulte `AGENTS.md` para as regras de contribuição do ambiente.

## Licença

Ainda não definida.
