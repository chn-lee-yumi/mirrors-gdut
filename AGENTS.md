## Agent skills

### Issue tracker

Issues live in GitHub Issues (repo `gregPerlinLi/mirrors-gdut`), operated via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Five default canonical triage labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`) used as-is. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

### File sync rules

`pages/mirror.css` and `pages/mirror.js` are shared with `Nginx-Fancyindex-Theme/gdut-mirrors/mirror.css` and `Nginx-Fancyindex-Theme/gdut-mirrors/mirror.js`. Any change to one copy MUST be synced to the other before committing.
