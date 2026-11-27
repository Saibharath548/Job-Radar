# JobRadar

A free-first personal dashboard for discovering and tracking game-development opportunities.

## Current features
- Manual job entry, search, match scoring, duplicate prevention, and application status tracking.
- One-click discovery from the public Himalayas Remote Jobs API (searches Unity Developer, Gameplay Programmer, and Game Developer roles with India eligibility).
- Direct search links for LinkedIn, Indeed India, Naukri, Internshala, and Hitmarker.
- SQLite storage; no third-party Python packages required.

## Run locally
Requires Python 3.9+.

```bash
python app.py
```

Open http://127.0.0.1:8000.

## Automatic discovery and platform limits
The Discover jobs button queries the Himalayas public JSON API from the Python backend, filters by India, and saves results. The API requires no key. JobRadar displays a visible Himalayas source link and keeps the API's applicationLink unchanged, as required by its API terms. See https://himalayas.app/docs/remote-jobs-api.

LinkedIn, Indeed, Naukri, Internshala, and Hitmarker are currently provided as direct search links, not crawled or automatically imported. Their general job-search pages do not provide a universally available public API for this use. Future integrations should use authorized partner APIs, permitted feeds, or job-alert emails the user explicitly connects. This project does not bypass logins, scrape restricted pages, or submit applications automatically.

## Matching profile
The initial heuristic profile is based on the user's resume: entry-level Gameplay Programmer; Unity 2D/3D; C#, C++; gameplay systems; FSM, Singleton, object pooling, event systems, coroutines, physics-based mechanics, Rigidbody movement, CharacterController, UI interaction and animation. Projects include Magnet Maniac, Bubble Rush (Global Game Jam 2025), and an FPS prototype. The resume lists a two-month Unity Developer internship and expected graduation in 2027.

Match scores are keyword heuristics, not an AI judgment or a guarantee of eligibility. Review each listing and its requirements before applying.

## Privacy and safety
Job data is stored in a local SQLite database. The database, virtual environments, Python caches, and .env files are excluded from Git. Do not commit credentials, private email contents, or personal application notes to a public repository.


## Deploy on Render (free prototype)
This repository includes a `render.yaml` Blueprint. To deploy:
1. Create or sign in to a Render account.
2. Connect your GitHub account and authorize access to this public repository.
3. In Render, choose **New → Blueprint**, select `Saibharath548/Job-Radar`, and apply the Blueprint.
4. Wait for the first deploy to finish; Render will show the public `onrender.com` URL.

The free web service sleeps after 15 minutes without traffic and can take about a minute to wake. Free services have an ephemeral filesystem: the SQLite database can be lost when the service restarts, sleeps, or redeploys. This deployment is therefore a demo, not durable personal job storage. A persistent database needs a separate database setup; do not store sensitive application notes in this demo.
