#!/usr/bin/env python3
"""
wallet_finder.py — Inventário READ-ONLY de arquivos de carteira cripto.

Objetivo: ajudar você a reencontrar SUAS PRÓPRIAS carteiras/keystores/anotações
de seed phrase que ficaram esquecidas em pastas antigas, NA SUA PRÓPRIA MÁQUINA.

Princípios de segurança embutidos:
  * 100% offline — o script não faz nenhuma conexão de rede.
  * Somente leitura — nunca cria, move, modifica ou apaga arquivos.
  * Saída redactada por padrão — mostra CAMINHO + TIPO, não o segredo em texto puro.
  * Relatório salvo com permissão 600 (só o dono lê).

Uso:
    python3 wallet_finder.py /caminho/da/pasta
    python3 wallet_finder.py            # usa a sua pasta home
    python3 wallet_finder.py /pasta --reveal   # mostra valores (use só offline!)

Depois de localizar os arquivos, abra cada um na ferramenta certa
(MetaMask, Phantom, Electrum, Bitcoin Core...) e descriptografe com a SUA senha.
"""

import argparse
import csv
import json
import os
import re
import stat
import sys
import time
from pathlib import Path

# ----------------------------------------------------------------------------
# Configuração
# ----------------------------------------------------------------------------

# Pastas que normalmente não contêm carteiras suas e só deixam a varredura lenta.
IGNORE_DIRS = {
    "node_modules", ".git", ".cache", "__pycache__", "site-packages",
    "Library/Caches", "AppData/Local/Temp", "$Recycle.Bin", "System Volume Information",
    ".npm", ".gradle", ".m2", "venv", ".venv", "snap",
}

# Só lemos o conteúdo de arquivos que pareçam texto e não sejam gigantes.
TEXT_EXTS = {
    # texto / dados
    ".txt", ".json", ".csv", ".tsv", ".md", ".log", ".bak", ".dat", ".rtf",
    ".env", ".conf", ".cfg", ".ini", ".yaml", ".yml", ".toml", ".xml", ".html",
    ".htm", ".tex", ".note", ".memo", ".asc", ".gpg", ".old", ".tmp", ".sav",
    # carteiras / chaves
    ".keystore", ".key", ".pem", ".pub", ".wallet", ".seed", ".mnemonic", ".kdbx",
    # código (pode conter chave colada em teste)
    ".py", ".js", ".ts", ".jsx", ".tsx", ".sh", ".bash", ".rb", ".go", ".rs",
    ".java", ".php", ".c", ".cpp", ".cs", ".sql", ".sol", ".vy", ".ipynb",
    "",  # arquivos sem extensão
}

# Extensões claramente binárias: pular sempre, mesmo em modo --all-text
# (ler isso como texto só gasta tempo e não acha nada).
BINARY_EXTS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".ico", ".svg",
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac",
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".zip", ".rar", ".7z", ".gz", ".tar", ".bz2", ".xz", ".iso", ".dmg",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".msi", ".apk", ".deb", ".rpm",
    ".ttf", ".otf", ".woff", ".woff2", ".pdf", ".psd", ".ai", ".sketch",
}
MAX_TEXT_BYTES = 5 * 1024 * 1024  # 5 MB — acima disso, só olhamos o nome do arquivo.

# Nomes/arquivos de carteiras conhecidas (casados pelo nome, sem ler conteúdo).
KNOWN_FILENAMES = {
    "wallet.dat": "Bitcoin Core wallet.dat",
    "default_wallet": "Electrum wallet",
    "electrum.dat": "Electrum",
    "keystore": "Keystore (pasta/arquivo)",
}

# Regex de hex de 64 caracteres (possível chave privada EVM/Ethereum em texto).
RE_HEX64 = re.compile(r"\b(?:0x)?[0-9a-fA-F]{64}\b")

# ----------------------------------------------------------------------------
# Utilidades de redação
# ----------------------------------------------------------------------------

def redact(value: str, reveal: bool) -> str:
    """Mostra só início...fim, a menos que --reveal esteja ativo."""
    value = value.strip()
    if reveal:
        return value
    if len(value) <= 12:
        return "****"
    return f"{value[:6]}...{value[-4:]}  (len={len(value)})"


def looks_high_entropy(hex_str: str) -> bool:
    """Heurística simples: descarta hex repetitivo tipo 0000... ou ababab..."""
    s = hex_str.lower().removeprefix("0x")
    if len(set(s)) < 6:          # pouca variedade de caracteres -> provável lixo
        return False
    if s == s[0] * len(s):
        return False
    return True

# ----------------------------------------------------------------------------
# Detectores (cada um recebe caminho e, se aplicável, conteúdo)
# ----------------------------------------------------------------------------

def detect_keystore_v3(text: str):
    """Keystore Ethereum V3: JSON com 'crypto' (ou 'Crypto') + 'version'."""
    try:
        data = json.loads(text)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    crypto = data.get("crypto") or data.get("Crypto")
    if isinstance(crypto, dict) and "ciphertext" in crypto and "version" in data:
        addr = data.get("address", "")
        return f"Keystore Ethereum V3 (criptografado){' addr=0x' + addr if addr else ''}"
    return None


def detect_solana_keypair(text: str):
    """Keypair Solana: JSON que é um array de 64 inteiros entre 0 e 255."""
    try:
        data = json.loads(text)
    except Exception:
        return None
    if (isinstance(data, list) and len(data) in (64, 32)
            and all(isinstance(b, int) and 0 <= b <= 255 for b in data)):
        return f"Keypair Solana (array de {len(data)} bytes — NÃO criptografado)"
    return None


def detect_seed_phrase(text: str, reveal: bool):
    """
    Heurística de baixa confiança para anotações de seed phrase:
    procura janelas de 12/15/18/21/24 palavras curtas, minúsculas e só letras
    (formato típico BIP39). Não valida contra o dicionário para manter offline,
    então é marcado como 'possível'.
    """
    results = []
    for line in text.splitlines():
        words = re.findall(r"\b[a-z]{3,8}\b", line.strip())
        if len(words) in (12, 15, 18, 21, 24):
            snippet = " ".join(words)
            shown = redact(snippet, reveal) if reveal else f"{len(words)} palavras (oculto)"
            results.append(f"Possível seed phrase BIP39 — {shown}")
    return results or None


def detect_hex_keys(text: str, reveal: bool):
    """Possíveis chaves privadas EVM em texto puro (hex de 64 chars, alta entropia)."""
    results = []
    seen = set()
    for m in RE_HEX64.findall(text):
        if m in seen or not looks_high_entropy(m):
            continue
        seen.add(m)
        results.append(f"Possível chave EVM (hex64) — {redact(m, reveal)}")
        if len(results) >= 20:   # evita inundar o relatório por arquivo
            break
    return results or None

# ----------------------------------------------------------------------------
# Varredura
# ----------------------------------------------------------------------------

def _fmt_secs(s: float) -> str:
    m, sec = divmod(int(s), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h{m:02d}m{sec:02d}s"
    if m:
        return f"{m}m{sec:02d}s"
    return f"{sec}s"


def _shorten(text: str, width: int) -> str:
    """Encurta um caminho no meio para caber na largura dada."""
    if len(text) <= width:
        return text.ljust(width)
    keep = width - 3
    head = keep // 2
    tail = keep - head
    return (text[:head] + "..." + text[-tail:]).ljust(width)


def scan(base: Path, reveal: bool, all_text: bool = False):
    findings = []          # tuplas (tipo, caminho, detalhe)
    scanned = 0
    read_count = 0         # quantos arquivos tiveram o conteúdo lido
    start = time.time()
    last_draw = 0.0

    def draw_progress(current_dir: str, force: bool = False):
        nonlocal last_draw
        now = time.time()
        if not force and (now - last_draw) < 0.2:
            return
        last_draw = now
        elapsed = now - start
        rate = scanned / elapsed if elapsed > 0 else 0
        line = (f"\r  {_fmt_secs(elapsed)} | "
                f"{scanned} arq | "
                f"{read_count} lidos | "
                f"{len(findings)} achados | "
                f"{rate:5.0f}/s | "
                f"{_shorten(current_dir, 45)}")
        # \033[K limpa o resto da linha; tudo vai para stderr
        sys.stderr.write(line[:160] + "\033[K")
        sys.stderr.flush()

    for root, dirs, files in os.walk(base, topdown=True):
        # poda de diretórios ignorados
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".Trash")]
        draw_progress(root)

        for name in files:
            path = Path(root) / name
            scanned += 1
            if scanned % 200 == 0:
                draw_progress(root)

            # 1) Casamento por nome de arquivo conhecido (sem ler conteúdo)
            low = name.lower()
            for known, label in KNOWN_FILENAMES.items():
                if low == known or low.startswith(known):
                    findings.append((label, str(path), "(detectado pelo nome do arquivo)"))

            # arquivos UTC--... são keystores Ethereum por convenção de nome
            if low.startswith("utc--"):
                findings.append(("Keystore Ethereum (nome UTC--...)", str(path),
                                 "(detectado pelo nome do arquivo)"))

            # 2) Leitura de conteúdo
            ext = path.suffix.lower()
            if all_text:
                # lê qualquer arquivo, exceto os claramente binários
                if ext in BINARY_EXTS:
                    continue
            else:
                # modo padrão: só extensões de texto/código conhecidas
                if ext not in TEXT_EXTS:
                    continue
            try:
                if path.stat().st_size > MAX_TEXT_BYTES:
                    continue
                # 'r' = somente leitura; errors='ignore' para não travar em binários
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                read_count += 1
            except (PermissionError, OSError):
                continue

            for detector in (detect_keystore_v3, detect_solana_keypair):
                hit = detector(text)
                if hit:
                    findings.append((hit.split(" ")[0], str(path), hit))

            for multi_detector, args in (
                (detect_seed_phrase, (text, reveal)),
                (detect_hex_keys, (text, reveal)),
            ):
                hits = multi_detector(*args)
                if hits:
                    for h in hits:
                        findings.append((h.split(" —")[0], str(path), h))

    draw_progress("concluído", force=True)
    sys.stderr.write("\n")   # encerra a linha de progresso
    sys.stderr.flush()
    return findings, scanned

# ----------------------------------------------------------------------------
# Relatório
# ----------------------------------------------------------------------------

def write_report(findings, scanned, base, reveal):
    base = Path(base)
    out_dir = base if base.is_dir() else base.parent
    txt_path = out_dir / "wallet_findings_report.txt"
    csv_path = out_dir / "wallet_findings_report.csv"

    lines = []
    lines.append("=" * 70)
    lines.append("RELATÓRIO DE RECUPERAÇÃO DE CARTEIRAS — TRATE COMO SENSÍVEL")
    lines.append("=" * 70)
    lines.append(f"Pasta-base varrida : {base}")
    lines.append(f"Arquivos verificados: {scanned}")
    lines.append(f"Itens encontrados  : {len(findings)}")
    lines.append(f"Modo               : {'REVELADO (valores em texto puro!)' if reveal else 'redactado'}")
    lines.append("")

    # Agrupa por tipo
    groups = {}
    for tipo, path, detalhe in findings:
        groups.setdefault(tipo, []).append((path, detalhe))

    for tipo in sorted(groups):
        lines.append(f"\n### {tipo}  ({len(groups[tipo])})")
        for path, detalhe in groups[tipo]:
            lines.append(f"  - {path}")
            lines.append(f"      {detalhe}")

    if not findings:
        lines.append("Nenhum item encontrado nessa pasta. Tente outro caminho/drive.")

    lines.append("\n" + "=" * 70)
    lines.append("Próximo passo: abra cada arquivo na ferramenta de origem")
    lines.append("(MetaMask, Phantom, Electrum, Bitcoin Core) e use a SUA senha.")
    lines.append("Apague estes relatórios depois de mover suas chaves para um cofre seguro.")
    lines.append("=" * 70)

    text = "\n".join(lines)

    # --- .txt ---
    txt_path.write_text(text, encoding="utf-8")

    # --- .csv (colunas: tipo, caminho, detalhe) — fácil de filtrar/ordenar no Excel ---
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["tipo", "caminho", "detalhe"])
        for tipo, path, detalhe in sorted(findings):
            writer.writerow([tipo, path, detalhe])

    # permissão 600 quando o SO suportar (Linux/Mac); no Windows é ignorado
    for p in (txt_path, csv_path):
        try:
            os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

    return txt_path, csv_path, text

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Inventário read-only de carteiras cripto na sua máquina.")
    ap.add_argument("base", nargs="?", default=str(Path.home()),
                    help="Pasta-base para varrer (padrão: sua home).")
    ap.add_argument("--reveal", action="store_true",
                    help="Mostra valores em texto puro. Use SOMENTE offline e apague o relatório depois.")
    ap.add_argument("--all-text", action="store_true", dest="all_text",
                    help="Lê o conteúdo de QUALQUER arquivo (pula só binários: vídeo, imagem, zip, exe). "
                         "Mais lento e com mais falso positivo, mas não deixa passar nada legível.")
    args = ap.parse_args()

    base = Path(args.base).expanduser()
    if not base.exists():
        print(f"Caminho não existe: {base}", file=sys.stderr)
        sys.exit(1)

    print(f"Varrendo (somente leitura): {base}", file=sys.stderr)
    if args.reveal:
        print("** MODO --reveal ATIVO: o relatório terá segredos em texto puro. **", file=sys.stderr)

    findings, scanned = scan(base, args.reveal, args.all_text)
    txt_path, csv_path, text = write_report(findings, scanned, base, args.reveal)

    # Resumo no terminal (sempre redactado, mesmo com --reveal, pra não vazar no histórico)
    print("\n--- RESUMO ---")
    groups = {}
    for tipo, _, _ in findings:
        groups[tipo] = groups.get(tipo, 0) + 1
    for tipo in sorted(groups):
        print(f"  {groups[tipo]:>4}  {tipo}")
    print(f"\nRelatórios salvos em:")
    print(f"  TXT: {txt_path}")
    print(f"  CSV: {csv_path}")


if __name__ == "__main__":
    main()
