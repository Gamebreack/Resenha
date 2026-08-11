# Operação

## Execução manual

No diretório raiz do projeto:

```bash
. .venv/bin/activate
python -m resenha --once pre-market
python -m resenha --once eod
python -m resenha --once long-form
```

## Agendamento

O scheduler externo executa os modos recorrentes e entrega o resultado ao Discord. O processo deve usar o diretório raiz do projeto para carregar `.env`.

## Diagnóstico

1. Confirme que `.env` existe e contém `GEMINI_API_KEY`.
2. Verifique conectividade com Google, fontes RSS e Discord.
3. Rode o modo desejado manualmente para obter o traceback completo.
4. Execute `python -m pytest tests/ -q` e `python -m mypy src/`.
5. Consulte os registros em `data/` sem versioná-los.

## Falhas Gemini

O cliente usa `gemini-flash-lite-latest` pela API oficial Google GenAI. HTTP 429 recebe retry com backoff. Erros de payload, autenticação ou modelo devem ser reproduzidos com uma chamada mínima antes de alterar o scheduler.

## Segurança

Não publique chaves, tokens, `.env`, bancos SQLite ou credenciais OAuth. O `.gitignore` exclui esses artefatos locais.

## Releases e mudanças

Toda mudança significativa deve atualizar a documentação correspondente e registrar o item no backlog/Megaplan antes do commit.

## Recuperação

O cache local pode ser recriado removendo o banco em `data/`, desde que isso seja feito conscientemente, pois registros de memória e feedback serão perdidos.

## Contato operacional

O canal de entrega é definido por `DISCORD_CHANNEL_ID`; não há URL remota Git configurada neste checkout neste momento.
