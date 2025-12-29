# Workspace Guide (local)

## Repo overview

- `README.md`
  - Main documentation about Google dorking operators and examples.
- `google-dork/`, `lists/`
  - Dork collections and categorized lists.
- `exploit-database.md` / `exploit-database.xlsx`
  - Additional curated datasets.
- `tools/`
  - Small helper scripts and lists.

## Quick navigation

- Dorks/categories: `google-dork/`
- Lists: `lists/`
- Tools: `tools/`

## Running the helper tool: Dorkinho

There is a small automation script in `tools/dorkinho.py` that opens Google searches in a browser.

### Requirements

- Python 3
- Selenium
- Firefox
- GeckoDriver available on your PATH (required by Selenium/Firefox)

Install Selenium (example):

```powershell
pip install selenium
```

### Usage

Run from the repo root via VS Code tasks, or from `tools/` directory.

List available dorks:

```powershell
python tools\dorkinho.py example.com -l
```

Open a small set of dorks (opens multiple tabs):

```powershell
python tools\dorkinho.py example.com -a
```

Open one specific dork by name (use `-l` to discover names):

```powershell
python tools\dorkinho.py example.com -e documents
```

Notes:

- The script uses Google queries. Use ethically and respect local laws and the project disclaimer.
- If Firefox/GeckoDriver is not configured, Selenium will fail to start the browser.
