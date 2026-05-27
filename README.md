# BPCL PNG Sitapur Dashboard

A Streamlit dashboard and portal for PNG connection analysis, search, and online GitHub-backed data entry for Sitapur operations. The project uses root CSV files such as `Connection-Data.csv`, `Conversion-Data.csv`, `AREAs.csv`, and `MRUs.csv` as the current source of truth in the codebase. [cite:138]

## Features

- Interactive Streamlit dashboard for PNG connection analysis and summaries based on the current CSV workflow. [cite:138][cite:167]
- PNG Assistant search mode with both single search and multi-meter search for pasted Excel meter columns. [cite:143][cite:146]
- Portal tabs for adding new connection and conversion records through GitHub-backed CSV updates. [cite:126][cite:128]
- Authentication support using credentials loaded from Streamlit secrets via `app_users`. [cite:157]

## Project files

| File | Purpose |
|---|---|
| `main.py` | Main Streamlit app entry point. [cite:157] |
| `data_loader.py` | Loads and prepares dashboard data from the root CSV files. [cite:138][cite:167] |
| `portal_tabs.py` | Portal UI for new connection and converted connection entry. [cite:126][cite:128] |
| `bot_tab.py` | PNG Assistant UI with search, summaries, and analysis tools. [cite:143][cite:146] |
| `github_db.py` | GitHub API read/write helpers for CSV storage. [cite:126][cite:157] |
| `auth.py` | Login/auth logic using Streamlit secrets. [cite:157] |
| `config.py` | Central configuration for repo, branch, CSV names, and schemas. [cite:138][cite:140] |

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

The generated `requirements.txt` is based on the imports currently present in the codebase: `streamlit`, `pandas`, `numpy`, `plotly`, `scipy`, and `requests`. [cite:167][cite:168]

## Data files

Place these files in the repository root:

- `Connection-Data.csv` [cite:138]
- `Conversion-Data.csv` [cite:138]
- `AREAs.csv` [cite:138]
- `MRUs.csv` [cite:138]

The current config is set to use branch `main`, with GitHub-backed portal writes targeting `Connection-Data.csv` and `Conversion-Data.csv`. [cite:139][cite:140]

## Streamlit secrets

Add the following in Streamlit Community Cloud Secrets or local `.streamlit/secrets.toml`:

```toml
GITHUB_TOKEN = "your_github_token_here"

[app_users]
admin = "your_password_here"
```

The code expects `GITHUB_TOKEN` at the top level and login credentials inside the `app_users` section. [cite:157]

## Run locally

```bash
pip install -r requirements.txt
streamlit run main.py
```

## Deployment notes

- Upload the project to a GitHub repository. [web:123]
- Keep the CSV files in the repo root if the deployed app should read them directly by name. [cite:139][cite:141]
- Add `GITHUB_TOKEN` in Streamlit app Secrets so the deployed app can update CSV files through the GitHub API. [cite:157][web:150]
- Restart or redeploy the app after changing Secrets. [web:148][web:150]
