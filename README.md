# Live update Streamlit upgrade

This package upgrades your current Excel-backed Streamlit map into a version that supports:
- automatic data reloads from a shared Excel file,
- an in-app admin portal for add/edit/delete,
- GitHub-friendly deployment,
- website updates whenever code is redeployed.

## What changed
- `app.py` now has two modes: Dashboard and Admin Portal.
- Data is loaded through a cached loader with a short TTL.
- Admin users can add, edit, and delete rows from the same Excel source.
- The app writes back to `Connection-Data.xlsx`, so fresh entries show in the dashboard.

## Important limitation
This version still uses Excel as the backend, so it is best for a single-admin or low-conflict workflow. For full multi-user live sync, move to Supabase/Postgres next.

## Deployment flow
1. Put `app.py`, `requirements.txt`, and `Connection-Data.xlsx` in your GitHub repo.
2. Deploy to Streamlit Community Cloud, Render, or Railway.
3. Set environment variable `ADMIN_PASSWORD`.
4. When you update code locally and push to GitHub, the site redeploys automatically.
5. When you edit data through the admin portal on the deployed app, the live site updates from that shared deployed file.

## Better production flow
For long-term use:
- keep code in GitHub,
- keep live data in Supabase,
- make admin portal write to Supabase,
- let Streamlit read from Supabase instead of Excel.

## Suggested Git commands
```bash
git add .
git commit -m "Add admin portal and live Excel updates"
git push origin main
```
# BPCL_PNG_Model_Sitapur
