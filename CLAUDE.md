# CLAUDE.md

This file provides guidance to Claude Code when working across all projects in this repository.

## Repository Overview

This is a multi-project monorepo containing internal tools and systems for business operations. All projects are authored by Sugihara Tatsuya. The primary language is Japanese for UI/docs, English for code.

### Projects

| Directory | Description | Tech Stack |
|---|---|---|
| `slack-dashboard/` | Slack activity analytics dashboard | Python, Streamlit, Plotly, SQLite, pandas |
| `order-management-system/` | Wholesale order management system (受発注管理システム) | Node.js, Express, Sequelize, PostgreSQL |
| `xorder-kentei/` | Quiz/certification app for the order system (クロスオーダー検定) | Vanilla HTML/CSS/JS, Google Apps Script |
| `xorder_kyushoku_manual/` | User manual docs for the order system (給食向けマニュアル) | Markdown (exported from Notion) |
| `docs/` | GitHub Pages deployment target | Static HTML |

### Relationships

- `order-management-system` is the core product
- `xorder-kentei` is a training/quiz tool for users of the order system
- `xorder_kyushoku_manual` provides how-to documentation for school meal (給食) customers
- `slack-dashboard` is an independent internal tool for monitoring team Slack activity

## Common Commands

**Git & Deploy:**
```bash
git push origin main                    # triggers GitHub Pages deploy for docs/
```

**GitHub Actions:**
- Slack dashboard auto-updates every 6 hours via `.github/workflows/update-dashboard.yml`
- Manual trigger: `gh workflow run update-dashboard.yml`

**Per-project commands:** see each project's own CLAUDE.md (e.g., `slack-dashboard/CLAUDE.md`).

## Coding Conventions

- **Language:** Code in English (variable names, comments), UI strings in Japanese
- **Commit messages:** English, imperative mood, concise (see git log for style)
- **No tests currently exist** across any project -- when adding features, consider suggesting tests
- **Environment variables:** stored in `.env` files (never committed); `.env.example` provided as templates
- **Secrets:** Slack tokens, DB credentials, and API keys must never appear in code or commits

## CI/CD

- **GitHub Pages:** `docs/` directory on `main` branch serves static content
- **Slack Dashboard pipeline:** GitHub Actions collects Slack data -> generates static HTML -> deploys to Pages
- **DB persistence:** SQLite DB stored as a GitHub Release asset (`db-latest`), downloaded/uploaded each run

## When Working on This Repo

- Always check for a project-specific CLAUDE.md before diving into a subproject
- The `docs/` folder is auto-generated for slack-dashboard; do not manually edit `docs/slack-dashboard.html`
- For `xorder-kentei`, the GAS backend is in `gas/Code.gs`; changes there must be deployed via Apps Script editor
- Use `/commit` for all commits to maintain co-authorship tracking
