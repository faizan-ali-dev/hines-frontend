# Hines public frontend capture — partial

This folder contains a local testing copy of public pages from https://www.hines.com/.

## Run

**Open directly:** double-click `OPEN-FRONTEND.html`, or open `frontend/index.html`. Styles, images, fonts, and captured-page links use relative paths and work without installing anything.

**Use a local server:** double-click `start-local.cmd`, then visit http://127.0.0.1:8765/. Python 3 is required for the server and is installed on this computer. If a server is already running on that port, use its existing address.

Server-dependent services still require the original backend.

## Django backend

The local Django backend is in `backend/`. It provides session-based client authentication for the new signup, login, and dashboard experience.

```powershell
cd backend
python -m pip install -r ../requirements.txt
python manage.py migrate
python manage.py runserver
```

The authentication API is available at `http://127.0.0.1:8000/api/auth/`:

- `GET csrf/` sets the CSRF cookie for browser requests.
- `POST signup/` accepts `full_name`, `email`, `referral_code`, and `password`.
- `POST login/` accepts `username` (the signup email) and `password`.
- `POST logout/` ends the active session.
- `GET profile/` returns the signed-in user's profile.
- `GET dashboard/` returns protected dashboard data.

Run the backend test suite with `python manage.py test accounts` from `backend/`.

## Contents

The extracted website is in `frontend/`.

- `frontend/`: captured HTML, CSS, JavaScript, fonts, and images, with local asset and captured-page links.
- `selected-pages.json`: the retained page list.

## Selected pages and limitations

This is a selected subset of the original capture, containing only the 25 requested navigation pages. It is not a complete copy of every public Hines page.

This is browser-delivered frontend output, not Hines's private source repository or server application. No backend is included. Search, property filters, investor access, forms, maps, embedded charts/video, and other server-backed services are not guaranteed to work offline. External website links remain external. Form submissions are disabled in the local testing copy.

The testing copy removes analytics/consent loaders, adjusts file links and integrity attributes, and resets captured carousel wrappers so the downloaded JavaScript can initialize them. Responsive images may reuse a downloaded larger variant. Original rendered captures are retained separately.

This package contains the 25 pages selected from the main site navigation. Links to pages outside this local set open the corresponding page on hines.com, so the retained pages do not contain dead links. Investor Login retains its original external investor-portal links. No additional pages are being extracted. Offline maps use a clearly labeled placeholder because live map tiles are not included.

The retained pages were checked in local Chromium at desktop (1440 × 900) and mobile (390 × 844) sizes, with remote requests blocked. Refresh the browser with Ctrl+F5 after updating an existing copy.
