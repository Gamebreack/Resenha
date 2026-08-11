# Arquitetura

## Fluxo principal

1. `resenha.__main__` interpreta o modo de execução.
2. `pipeline.py` carrega configurações e monta o contexto.
3. Fontes de dados coletam carteira, preços, macroeconomia, agenda e RSS.
4. `assembler.py` consolida os dados em `BriefingContext`.
5. `summary.py` constrói o prompt e chama `GeminiClient`.
6. `delivery.py` publica o resultado no Discord.
7. Memória e reações são persistidas no SQLite.

## Diretórios

- `src/resenha/`: código da aplicação.
- `tests/`: testes automatizados.
- `docs/megaplan/`: visão, roadmap, backlog e decisões do projeto.
- `docs/research/`: pesquisas e fontes utilizadas para a curadoria RSS.
- `data/`: cache e registros locais; ignorado pelo Git.

## Modelo e geração

A integração em `src/resenha/gemini.py` usa o SDK `google-genai` e o modelo `gemini-flash-lite-latest`, com retry para respostas HTTP 429. A chave é lida de `GEMINI_API_KEY`.

## Princípios

- Integrações externas ficam isoladas em módulos próprios.
- Dados temporários e credenciais não entram no controle de versão.
- Mudanças devem ser acompanhadas por testes e documentação Megaplan.

## Pontos de entrada

```bash
python -m resenha --once pre-market
python -m resenha --once eod
python -m resenha --once long-form
```

Consulte `docs/operations.md` para diagnóstico e operação.