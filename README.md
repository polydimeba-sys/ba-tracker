# Polydime BA Team Tracker (Firebase edition)

A team tracker with **no backend server** — the page talks directly to
Google Firestore (a free-tier cloud database), so it can be hosted as a
plain static site on GitHub Pages.

## What changed from the Python version

- `server.py` is gone. Data lives in Firestore instead of a local
  `tracker_data.json` file.
- Login still uses simple shared passwords (`ADMIN_PASS` / `MEMBER_PASS`,
  near the top of the `<script>` block in the HTML file) — same as
  before, just checked in the browser instead of on a server.
- **Important tradeoff**: since there's no server to hide anything, your
  Firebase config and these passwords are visible to anyone who views
  the page source. That's normal/expected for Firebase web apps — real
  protection comes from Firestore Security Rules (see below), not from
  hiding the config.

## One-time setup (you've already done most of this)

1. ✅ Firebase project created, Firestore database created (test mode)
2. ✅ Web app registered, config pasted into `polydime-ba-tracker.html`

### Apply the real security rules (do this before sharing the link)

Test mode leaves Firestore wide open and auto-locks after 30 days. Replace
it with the rules in `firestore.rules` now, rather than waiting:

1. Firebase Console → your project → **Firestore Database → Rules** tab
2. Delete everything in the editor, paste in the contents of
   `firestore.rules` from this folder
3. Click **Publish**

This allows anyone to *read* the team's data (needed for the login
dropdown and dashboards) but restricts *writes* to data that looks like
a legitimate member/entry — enough to block bots that scan for open
Firestore projects. It is **not** the same as real per-user
authentication; see the comments in `firestore.rules` for the details
and tradeoffs.

### Change the default passwords

Open `polydime-ba-tracker.html`, find these two lines near the top of
the `<script>` block, and set your own values:

```js
const ADMIN_PASS = 'admin2024';
const MEMBER_PASS = 'member123';
```

## Deploy to GitHub Pages

```bash
git add .
git commit -m "Switch to Firebase, remove Python backend"
git push
```

Then on GitHub:
1. Go to your repo → **Settings → Pages**
2. Under **Source**, choose **Deploy from a branch**
3. Branch: `main`, folder: `/ (root)` → **Save**
4. GitHub gives you a URL like `https://polydimeba-sys.github.io/ba-tracker/`
   — that's your live site (can take a minute or two to activate the first time)

Every future `git push` updates the live site automatically.

## Local testing

No server needed anymore — just open `polydime-ba-tracker.html` directly
in a browser, or serve it with any static file server:

```bash
python3 -m http.server 8080
# open http://localhost:8080/polydime-ba-tracker.html
```

## Notes

- First time anyone loads the app, it seeds the four default team members
  into Firestore automatically (Alice, Bob, Priya, David) — edit or add
  real ones from the Admin dashboard afterward.
- Excel export works exactly as before (client-side, via SheetJS).
- Firestore's free tier (Spark plan) comfortably covers a small internal
  team's daily usage.
