# Hines public frontend capture — partial

This folder contains a local testing copy of public pages from https://www.hines.com/.

## Run

**Open directly:** double-click `OPEN-FRONTEND.html`, or open `frontend/index.html`. Styles, images, fonts, and captured-page links use relative paths and work without installing anything.

**Use a local server:** double-click `start-local.cmd`, then visit http://127.0.0.1:8765/. Python 3 is required for the server and is installed on this computer. If a server is already running on that port, use its existing address.

Server-dependent services still require the original backend.

## Django backend

The local Django application is in `backend/`. It serves the captured public frontend and provides session-based client authentication, employee dashboards, and the customized Django admin control panel.

```powershell
cd backend
python -m pip install -r ../requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` to use the public site and browser pages built with plain HTML, CSS, JavaScript, and Django templates:

- `/sign-up/` creates an employee account.
- `/client-login/` signs in with the registration email and password.
- `/dashboard/demo/` displays the 15-lot Demo Assignment.
- `/dashboard/client/` displays the 35-lot Client Assignment after staff activation.
- `/admin/` opens the staff control panel.

### Assignment rules

- Every signup receives 15 Demo lots and 35 Client lots.
- Staff set the completed lot count in the customized Django admin employee table. The backend marks only the first matching lots complete and recalculates earnings from the stored per-lot amounts.
- Staff can change an employee's assignment stage between Demo and Client directly from the employee table. The first Client activation carries the employee's current Demo earnings once into Client totals.
- Detailed task configuration is available in Django admin. Staff can create, edit, or delete Demo and Client tasks for an employee, including the lot number, task name, description, value, earning, link, and completion status. The browser never controls completion or financial calculations.
- Pending tasks display `$0.00` in the employee earning column. The stored earning appears only after staff mark that task complete.

For production, set `DJANGO_DEBUG=false`, `DJANGO_SECRET_KEY` to a long private value, and `DJANGO_ALLOWED_HOSTS` to the deployed hostname. The application uses Django sessions, CSRF protection, secure production cookies, and login-attempt throttling.

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
