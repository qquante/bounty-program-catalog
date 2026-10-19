#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper dos programas do HackenProof (dashboard.hackenproof.com).

Usa a API JSON interna autenticada por cookie de sessao:
  - Listagem: /api/internal/user/opportunities?page=N&per_page=...
  - Detalhe:  /api/internal/user/opportunities/{slug}

COMO USAR
---------
1. Cole o header "cookie:" inteiro do DevTools no arquivo cookies.txt
   (Network -> clica na requisicao -> Request Headers -> copia o valor de "cookie").
2. (Opcional mas recomendado) Cole tambem o seu User-Agent em user_agent.txt
   -> precisa ser o MESMO do navegador, senao o cf_clearance do Cloudflare nao vale.
3. Rode:
     python scrape_hackenproof.py
4. Saidas:
     data/programs/<slug>.json   -> detalhe bruto de cada programa
     data/programs_summary.csv   -> planilha consolidada
     data/programs_summary.json  -> tudo num JSON so

OBS: os cookies (_hackenproof_session, cf_clearance) EXPIRAM. Se comecar a dar
401/403, recole o cookie atualizado no cookies.txt e rode de novo (ele retoma
de onde parou).
"""

import csv
import json
import os
import sys
import time
import random
from pathlib import Path

BASE = "https://dashboard.hackenproof.com"
LIST_URL = BASE + "/api/internal/user/opportunities"
DETAIL_URL = BASE + "/api/internal/user/opportunities/{slug}"

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
PROG_DIR = DATA_DIR / "programs"
COOKIES_FILE = ROOT / "cookies.txt"
UA_FILE = ROOT / "user_agent.txt"

# Cobre a listagem inteira sem hardcode de 32 paginas: vai ate a lista esvaziar.
PER_PAGE = 50
NOT_AUDITS = "true"          # mesmo filtro que voce capturou (so bounties)
ORDER_BY = "published_date"  # desc

# Pausa entre requisicoes (segundos) -> respeitoso, evita bloqueio.
MIN_DELAY = 0.6
MAX_DELAY = 1.4
MAX_RETRIES = 4

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
)


# --------------------------------------------------------------------------- #
# Sessao HTTP: prefere curl_cffi (imita TLS do Chrome -> passa pelo Cloudflare),
# cai pra httpx se nao tiver.
# --------------------------------------------------------------------------- #
def load_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def build_headers() -> dict:
    ua = load_text(UA_FILE) or DEFAULT_UA
    cookie = load_text(COOKIES_FILE)
    if not cookie:
        sys.exit(
            f"[ERRO] Cole o header 'cookie:' do DevTools em {COOKIES_FILE}\n"
            "       (Network -> requisicao -> Request Headers -> 'cookie')."
        )
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": BASE + "/user/programs?tab=bounties",
        "user-agent": ua,
        "cookie": cookie,
    }


class Client:
    """Wrapper fino sobre curl_cffi (preferido) ou httpx."""

    def __init__(self, headers: dict):
        self.headers = headers
        self.kind = None
        self._init_backend()

    def _init_backend(self):
        try:
            from curl_cffi import requests as creq  # type: ignore
            self._sess = creq.Session(impersonate="chrome", headers=self.headers)
            self.kind = "curl_cffi"
            return
        except Exception:
            pass
        try:
            import httpx  # type: ignore
            self._sess = httpx.Client(
                http2=True, headers=self.headers, timeout=30.0, follow_redirects=True
            )
            self.kind = "httpx"
            return
        except Exception:
            sys.exit(
                "[ERRO] Instale uma das libs:\n"
                "   pip install curl_cffi      (recomendado: passa pelo Cloudflare)\n"
                "   pip install 'httpx[http2]' (fallback)"
            )

    def get_json(self, url: str, params: dict | None = None):
        last_err = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = self._sess.get(url, params=params, timeout=30)
                code = r.status_code
                if code == 200:
                    return r.json()
                if code in (401, 403):
                    raise SystemExit(
                        f"[ERRO {code}] Cookie/sessao invalido ou expirado, ou bloqueio "
                        f"Cloudflare.\n  URL: {url}\n"
                        "  -> Recole o header 'cookie' atualizado em cookies.txt e garanta "
                        "o mesmo User-Agent em user_agent.txt.\n"
                        "  -> Se persistir: pip install curl_cffi"
                    )
                if code in (429, 500, 502, 503, 504):
                    wait = attempt * 3
                    print(f"  [{code}] backoff {wait}s (tentativa {attempt})")
                    time.sleep(wait)
                    continue
                last_err = f"HTTP {code}"
            except SystemExit:
                raise
            except Exception as e:
                last_err = repr(e)
                time.sleep(attempt * 2)
        raise RuntimeError(f"Falhou apos {MAX_RETRIES} tentativas: {url} ({last_err})")


def polite_sleep():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


# --------------------------------------------------------------------------- #
# Etapa 1: mapear todos os slugs percorrendo a listagem paginada.
# --------------------------------------------------------------------------- #
def fetch_all_slugs(client: Client) -> list[dict]:
    print("== Etapa 1: mapeando programas (listagem paginada) ==")
    found = {}
    page = 1
    while True:
        params = {
            "page": page,
            "per_page": PER_PAGE,
            "not_audits": NOT_AUDITS,
            "order_by[published_date]": "desc" if ORDER_BY == "published_date" else "desc",
        }
        data = client.get_json(LIST_URL, params=params)
        progs = data.get("programs", []) if isinstance(data, dict) else []
        if not progs:
            break
        for p in progs:
            slug = p.get("slug")
            if slug and slug not in found:
                found[slug] = p
        print(f"  pagina {page:>2}: +{len(progs)} programas (total unico: {len(found)})")
        if len(progs) < PER_PAGE:
            break
        page += 1
        polite_sleep()
    print(f"  -> {len(found)} programas no total.\n")
    return list(found.values())


# --------------------------------------------------------------------------- #
# Etapa 2: baixar o detalhe de cada programa (com cache/retomada).
# --------------------------------------------------------------------------- #
def fetch_details(client: Client, listing: list[dict], refresh: bool = False):
    print("== Etapa 2: baixando detalhe de cada programa ==")
    PROG_DIR.mkdir(parents=True, exist_ok=True)
    total = len(listing)
    for i, p in enumerate(listing, 1):
        slug = p["slug"]
        out = PROG_DIR / f"{slug}.json"
        if out.exists() and not refresh:
            print(f"  [{i}/{total}] {slug}  (cache)")
            continue
        detail = client.get_json(DETAIL_URL.format(slug=slug))
        out.write_text(json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            f"  [{i}/{total}] {slug}  reports={detail.get('submitted_reports')} "
            f"rewards=${detail.get('total_rewards')} rep={detail.get('min_reputation_points')}"
        )
        polite_sleep()
    print()


# --------------------------------------------------------------------------- #
# Etapa 3: consolidar tudo em CSV + JSON.
# --------------------------------------------------------------------------- #
def join_labels(labels: dict, key: str) -> str:
    if not isinstance(labels, dict):
        return ""
    return ";".join(labels.get(key, []) or [])


def flatten(d: dict) -> dict:
    labels = d.get("labels", {}) or {}
    rewards = d.get("rewards", {}) or {}
    status = d.get("status", {}) or {}
    company = d.get("company", {}) or {}
    sla = d.get("sla", {}) or {}
    scopes = d.get("scopes", []) or []
    in_scope = [s for s in scopes if not s.get("out_of_scope")]

    return {
        "slug": d.get("slug"),
        "title": d.get("title"),
        "company": company.get("company_name") or d.get("managed_by_company_name"),
        "state": d.get("state"),
        "status": status.get("name"),
        "private": d.get("private"),
        "new_program": d.get("new_program"),
        # dinheiro
        "min_bounty": d.get("min_bounty"),
        "max_bounty": d.get("max_bounty"),
        "total_rewards": d.get("total_rewards"),
        "submission_cost": d.get("submission_cost"),
        # reputacao / requisitos
        "min_reputation_points": d.get("min_reputation_points"),
        "reputation_required": d.get("reputation_required"),
        "kyc_required": d.get("kyc_required"),
        "kyc_required_for_payment": d.get("kyc_required_for_payment"),
        "poc_required": d.get("poc_required"),
        # submissions / atividade
        "submitted_reports": d.get("submitted_reports"),
        "valid_reports_count": d.get("valid_reports_count"),
        "hacker_ranks_count": d.get("hacker_ranks_count"),
        "views_count": d.get("views_count"),
        # faixas de recompensa
        "reward_critical_max": rewards.get("critical_max"),
        "reward_high_max": rewards.get("high_max"),
        "reward_medium_max": rewards.get("medium_max"),
        "reward_low_max": rewards.get("low_max"),
        # categorias
        "types": join_labels(labels, "types"),
        "languages": join_labels(labels, "languages"),
        "platforms": join_labels(labels, "platforms"),
        "project_types": join_labels(labels, "project_types"),
        # escopo
        "scopes_in_count": len(in_scope),
        "scopes_targets": ";".join(
            s.get("target", "") for s in in_scope if s.get("target")
        ),
        # SLA
        "sla_first_response": sla.get("first_response"),
        "sla_time_to_reward": sla.get("time_to_reward"),
        # datas
        "published_date": d.get("published_date"),
        "start_date": d.get("start_date"),
        "end_date": d.get("end_date"),
        "updated_at": d.get("updated_at"),
        "url": f"{BASE}/user/programs/{d.get('slug')}",
    }


def consolidate():
    print("== Etapa 3: consolidando CSV + JSON ==")
    rows = []
    for f in sorted(PROG_DIR.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            rows.append(flatten(d))
        except Exception as e:
            print(f"  [skip] {f.name}: {e}")
    if not rows:
        print("  Nenhum detalhe encontrado.")
        return

    # ordena por total de reports (mais ativos primeiro).
    # alguns programas trazem o numero como texto -> converte com seguranca.
    def _as_int(v):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return 0

    rows.sort(key=lambda r: _as_int(r.get("submitted_reports")), reverse=True)

    csv_path = DATA_DIR / "programs_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fp:
        w = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    json_path = DATA_DIR / "programs_summary.json"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  -> {len(rows)} programas")
    print(f"  -> {csv_path}")
    print(f"  -> {json_path}")


def main():
    refresh = "--refresh" in sys.argv
    only_consolidate = "--consolidate" in sys.argv

    if only_consolidate:
        consolidate()
        return

    headers = build_headers()
    client = Client(headers)
    print(f"[backend HTTP: {client.kind}]\n")

    listing = fetch_all_slugs(client)
    # guarda o snapshot da listagem (resumo) tambem
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "listing_raw.json").write_text(
        json.dumps(listing, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    fetch_details(client, listing, refresh=refresh)
    consolidate()
    print("\nPronto. ")


if __name__ == "__main__":
    main()
