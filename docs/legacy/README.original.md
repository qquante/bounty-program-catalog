> Historical project notes. Paths, operational status, badges and test claims below are retained as archival reference and have not all been revalidated. Use the root README and docs/REVIEW.md for this review snapshot.

# HackenProof scraper

Coleta todos os programas de bounty do HackenProof via API JSON interna
(autenticada por cookie de sessao) e gera CSV/JSON consolidado.

## Passo a passo

1. **Instalar dependencias**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Pegar o cookie** (validade de algumas horas)
   - Logue no dashboard.hackenproof.com no Chrome
   - F12 -> aba **Network** -> abra `/user/programs`
   - Clique numa requisicao `opportunities` -> **Request Headers**
   - Copie o valor inteiro do header `cookie` e cole em `cookies.txt`
   - (Confira que o `user-agent` da requisicao bate com o de `user_agent.txt`)

3. **Rodar**
   ```powershell
   python scrape_hackenproof.py
   ```

## Saidas (pasta `data/`)
| arquivo | conteudo |
|---|---|
| `programs/<slug>.json` | detalhe bruto de cada programa |
| `programs_summary.csv`  | planilha consolidada (abre no Excel) |
| `programs_summary.json` | tudo num JSON |
| `listing_raw.json`      | snapshot da listagem |

## Flags
- `python scrape_hackenproof.py --refresh`      -> rebaixa todos os detalhes (ignora cache)
- `python scrape_hackenproof.py --consolidate`  -> so remonta o CSV a partir do que ja baixou

## Notas
- Se der **401/403**: cookie expirou ou Cloudflare bloqueou. Recole o cookie e garanta
  o mesmo User-Agent. `curl_cffi` (recomendado) imita o TLS do Chrome e evita bloqueio.
- Rode da **mesma maquina/IP** onde pegou o `cf_clearance`.
- O script **retoma** de onde parou (usa cache em `data/programs/`).
- `not_audits=true` traz so bounties. Pra incluir audits, mude `NOT_AUDITS = "false"` no script.
