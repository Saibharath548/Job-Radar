# JobRadar

A free-first dashboard for collecting and tracking game-development job opportunities.

## Current MVP
- Add job listings manually from LinkedIn, Indeed, Naukri, Internshala, Hitmarker, studio career pages, and other sources.
- View a transparent keyword-based match score against the starter candidate profile.
- Prevent duplicate non-empty job URLs.
- Track application status.
- Store data locally in SQLite.

## Starter candidate profile
Based on the supplied resume: entry-level Gameplay Programmer; Unity 2D/3D; C#, C++; gameplay systems; finite state machines; Singleton; object pooling; event systems; coroutines; physics-based mechanics; Rigidbody movement; CharacterController; UI interaction and animation. Projects: Magnet Maniac, Bubble Rush (Global Game Jam 2025), and an FPS prototype. Resume lists a two-month Unity Developer internship at SR Edu Technologies (30 March–31 May 2026) and expected graduation in 2027.

## Run locally
Requires Python 3.9 or newer. No third-party packages are required.

```bash
python app.py
```

Then open http://127.0.0.1:8000.

## Important limitations
This is the first MVP, not an automatic multi-platform crawler. Add listings manually for now. Future integrations should use official APIs, permitted RSS/public feeds, and job-alert emails the user chooses to connect. Do not scrape sites or automate applications in ways that violate platform terms. Daily unattended operation and public hosting require separate deployment and scheduler setup; free tiers have limits.

## Matching approach
The initial match score is a transparent keyword heuristic, not an AI assessment or a guarantee of eligibility. It rewards relevant skills, role terms, and junior/internship language, and penalizes explicit seniority terms. Adjust `PROFILE` and `score()` in `app.py` as needed.

## Development approach
Start with a small runnable product: collect listings, show them in one responsive interface, score them transparently, and track application status. Add data integrations only after the core workflow is verified.
