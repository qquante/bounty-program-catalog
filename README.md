# Bounty Program Catalog

![Language: Python](https://img.shields.io/badge/Language-Python-3776AB?style=flat-square&logo=python) ![Exports: CSV and JSON](https://img.shields.io/badge/Exports-CSV%20and%20JSON-555555?style=flat-square) [![License: MIT](https://img.shields.io/badge/License-MIT-555555?style=flat-square)](LICENSE)

Collect HackenProof program metadata into local JSON/CSV and build a self-contained HTML catalogue for comparison.

This is a small collection toolkit, not a vulnerability scanner. The useful output is a local inventory of programs that can be filtered and reviewed without repeatedly opening individual program pages.

## Files in the collection workflow

| File | Reads | Produces |
| --- | --- | --- |
| [scrape_hackenproof.py](scrape_hackenproof.py) | Authenticated program list and details | `data/programs/<slug>.json`, summary JSON and CSV |
| [build_dashboard.py](build_dashboard.py) | `data/programs_summary.json` | Self-contained `dashboard.html` |

The collector paginates until the list is exhausted, pauses between requests and retries bounded failures. Authentication depends on an existing authorized session; expired cookies can stop collection.

## Install and inspect

```console
python -m venv .venv
python -m pip install -r requirements.txt
python -m py_compile scrape_hackenproof.py build_dashboard.py wallet_finder.py
```

For authorized collection, supply the local `cookies.txt` and optional matching `user_agent.txt` expected by the scraper, then run `python scrape_hackenproof.py`. Never commit either session file. With a summary JSON available, `python build_dashboard.py` rebuilds the dashboard; open the generated HTML locally.

## Separate utility in this snapshot

[wallet_finder.py](wallet_finder.py) is an unrelated local wallet-file inventory utility. It is not required for program collection. Its optional reveal mode and generated reports can expose sensitive local material, so do not include them in catalogue exports or automated collection jobs.

The source depends on an internal authenticated API and its schema may change. Syntax checking does not establish current account access, catalogue completeness or a passing behavioral test suite.

**Technology:** Python · curl-cffi · httpx · JSON/CSV · static HTML dashboard

Project-authored source: [MIT](LICENSE). Third-party components retain their own notices and terms.
