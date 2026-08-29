# AI Quotation System — Render Deployment

## What's in this repo
- `render.yaml` — the Render **Blueprint**. Its presence at repo root is what enables
  Auto-Deploy and PR Previews.
- `main.py` — minimal FastAPI backend (health check + a `/generate-quotation` stub).
- `requirements.txt` — Python dependencies.

## One-time setup
1. Push this repo to GitHub (or GitLab).
2. In the Render Dashboard: **New > Blueprint**, then select this repo.
   Render will read `render.yaml` and provision:
   - a **Postgres database** (`quotation-db`)
   - a **web service** (`quotation-api`)
3. Set the `ANTHROPIC_API_KEY` environment variable on the `quotation-api`
   service in the Render dashboard (it's marked `sync: false` in the
   Blueprint on purpose, so it's never committed to the repo).
4. Deploy. Once live, hit `https://<your-service>.onrender.com/health` to confirm it's up.

## After setup, you automatically get
- **Auto-Deploy**: every push to `main` redeploys `quotation-api` automatically.
- **PR Previews**: every pull request spins up its own isolated copy of the
  service (and, depending on your plan, its own database), at a unique
  preview URL — so you can test changes before merging without touching
  production.

## Next steps to make this functional
- Flesh out `/generate-quotation` in `main.py` to call the Anthropic API,
  parse the request into line items, and match them against your printer
  catalog (brand, model, part number, GCC pricing, etc.).
- Add an endpoint (or admin UI) to load/update your product catalog.
- Add PDF/Word export for the final quotation document.
- Add authentication before this is customer-facing.
