# Bounty Program Catalog

A Python collector that consolidates authorized bounty-program metadata into local JSON/CSV and dashboard views.

## Features

- Listing/detail collection normalizes program metadata.
- Consolidation can rebuild local summary files.
- A static dashboard presents the collected catalogue.

## Stack

Python · curl-cffi · httpx · JSON/CSV · static HTML dashboard

Downloaded program details and consolidated exports are local files. Session cookies and the original collected dataset are excluded.

## Getting started

Install requirements.txt in an isolated environment. Inspect the collector's configuration before any network run; use synthetic JSON to develop the dashboard.

## How it works

```text
Authorized catalogue access → listing/details → normalization and local cache → CSV/JSON → dashboard
```

## Current limitations

The collector uses a session-dependent upstream interface. No login, collection or cookie validation was performed. Current provider behavior and access terms require separate review.

## License

Project-authored source code is licensed under the [MIT License](LICENSE). Third-party components and datasets retain their respective rights and licenses.
