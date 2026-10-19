# Bounty Program Catalog

> **Local private review:** publication is paused. See [security review and remaining release conditions](docs/SECURITY_REVIEW.md). Local fixes have not been pushed.


A Python collector that consolidates authorized bounty-program metadata into local JSON/CSV and dashboard views.

![review](https://img.shields.io/badge/review-private-374151) ![primary](https://img.shields.io/badge/primary-Python-2563EB) [![LinkedIn](https://img.shields.io/badge/LinkedIn-Douglas%20Silva-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/douglas-silva-data-analyst/)

[Overview](#overview) · [Architecture](#architecture) · [Setup](#setup) · [Validation](#validation) · [Roadmap](#roadmap) · [Review notes](docs/REVIEW.md)

## Overview

- Listing/detail collection normalizes program metadata.
- Consolidation can rebuild local summary files.
- A static dashboard presents the collected catalogue.

**Technology:** Python · curl-cffi · httpx · JSON/CSV · static HTML dashboard

**Persistence and data:** Downloaded program details and consolidated exports are local files. Session cookies and the original collected dataset are excluded.

## Architecture

```text
Authorized catalogue access → listing/details → normalization and local cache → CSV/JSON → dashboard
```

| Location | Review focus |
| --- | --- |
| [`scrape_hackenproof.py`](scrape_hackenproof.py) | Source/configuration inspected for scope and structure |
| [`build_dashboard.py`](build_dashboard.py) | Source/configuration inspected for scope and structure |
| [`wallet_finder.py`](wallet_finder.py) | Source/configuration inspected for scope and structure |
| [`requirements.txt`](requirements.txt) | Source/configuration inspected for scope and structure |

Internal package and module names are retained where changing them would affect imports or compatibility. This descriptive repository name does not imply a completed package/API migration.

## Setup

Install requirements.txt in an isolated environment. Inspect the collector's configuration before any network run; use synthetic JSON to develop the dashboard.

Start from an isolated environment. Use `.env.example` when present and inspect the configuration loader: an example file is not necessarily loaded automatically. Runtime databases, real account sessions and private credentials are not bundled. Live integration prerequisites are separate from local tests.

## Validation

Static parsing checked 3 Python files and 0 strict JSON files. Python syntax errors: 0; JSON errors: 0. No functional test/build result is claimed for this preparation.

Available test scripts are inventoried in [the review notes](docs/REVIEW.md). Choose offline checks before operating any integration.

These results apply to the selected checks on the preparation copy. They do not establish deployment readiness, full coverage, live provider availability or measured performance. CI definitions, when present under `docs/ci-templates/`, are inactive review templates; no remote CI badge is claimed.

## Limits and current status

The collector uses a session-dependent upstream interface. No login, collection or cookie validation was performed. Current provider behavior and access terms require separate review.

This private snapshot is for code and portfolio review. Generated runtime material and unreviewed binary assets may be excluded. [Review notes](docs/REVIEW.md) record preparation scope, findings and outstanding validation.

## Roadmap

- [ ] Add a synthetic catalogue fixture and schema tests.
- [ ] Separate collection from dashboard rendering.
- [ ] Document access prerequisites without embedding cookies or account data.

## History and attribution

No recoverable original Git history was verified for this snapshot. Import and preparation commits use their actual current dates; filesystem timestamps are not treated as development dates.

No open-source license is granted by this preparation. A license and attribution review is required before public redistribution.

## Maintainer and feedback

Douglas de Oliveira Silva · [GitHub](https://github.com/qquante) · [LinkedIn](https://www.linkedin.com/in/douglas-silva-data-analyst/)

For this private review, report reproducible issues with a minimal fixture and the exact check output. Keep account data, credentials and generated sensitive reports out of issues and commits. Existing contribution guidelines apply where present.

**Topics:** `python`, `data-collection`, `csv`, `security-research`, `dashboard`, `etl`
