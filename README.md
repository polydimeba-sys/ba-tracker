# Polydime BA Team Tracker

A tiny self-contained team tracker: a Python standard-library HTTP server
(`server.py`) serving a single-page app (`polydime-ba-tracker.html`), with
data stored in a JSON file. No external Python packages required.

GitHub itself can only host **static** files, so it can't run `server.py`
directly. The way to "host it through GitHub" is:

1. Push this folder to a GitHub repo.
2. Connect that repo to a free host that runs Python and auto-deploys on
   every push (Railway is recommended below; Render works too).

## 1. Push to GitHub

```bash
cd ba-tracker
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

`tracker_data.json` is intentionally excluded via `.gitignore` — your real
data should live on the host's persistent volume, not in the repo.

## 2. Deploy on Railway (recommended)

1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. **New Project → Deploy from GitHub repo** → select this repo.
3. Railway auto-detects Python and uses the `Procfile` to start it.
4. **Add a Volume** (Project → your service → Volumes tab):
   - Mount path: `/data`
5. **Set environment variables** (Service → Variables tab):
   | Variable      | Value                          |
   |---------------|--------------------------------|
   | `DATA_DIR`    | `/data`                        |
   | `ADMIN_PASS`  | *your own admin password*      |
   | `MEMBER_PASS` | *your own team password*       |

   (`PORT` is set automatically by Railway — don't override it.)
6. Deploy. Railway gives you a public URL like
   `https://your-app.up.railway.app` — that's your live tracker.
7. From now on, every `git push` to `main` auto-redeploys.

## 2b. Deploy on Render (alternative)

Same idea, different platform:

1. [render.com](https://render.com) → **New → Web Service** → connect the
   GitHub repo.
2. Build command: *(leave blank)*. Start command: `python3 server.py`.
3. Add a **Disk** (Render's persistent storage) mounted at `/data`
   — note: persistent disks require a paid instance type on Render;
   the free tier's filesystem resets on every deploy.
4. Set the same environment variables as above (`DATA_DIR=/data`,
   `ADMIN_PASS`, `MEMBER_PASS`).

## Local development

Unchanged from before — env vars are optional locally:

```bash
python3 server.py
# open http://localhost:8080
```

## Security notes before going live

- Set real values for `ADMIN_PASS` and `MEMBER_PASS` as environment
  variables on the host. Don't leave the defaults in place, and don't
  commit real passwords into the repo.
- The host's free HTTPS (Railway and Render both provide it automatically)
  covers the "no HTTPS" gap from running this locally over plain HTTP.
- Back up `tracker_data.json` periodically — ask your host how to download
  files from its persistent volume/disk, or add a small script that copies
  it somewhere safe on a schedule.
