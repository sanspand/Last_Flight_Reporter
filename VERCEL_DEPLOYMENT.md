# Deploy Last Flight to Vercel

This repository deploys as a Flask API. `pyproject.toml` explicitly selects
`server:app`, while `app.py` remains the command-line flight reporter.
`vercel.json` selects Flask and allows requests to run for up to 60 seconds.
`.python-version` selects Python 3.12; dependencies come from `requirements.txt`.

## Deploy from Git

1. Commit and push these files to your Git repository.
2. In Vercel, choose **Add New > Project** and import the repository.
3. Set **Root Directory** to the directory containing `vercel.json` and
   `requirements.txt` (the repository root for this layout).
4. Use the **Flask** framework preset. Leave Build Command, Install Command,
   and Output Directory at their defaults. No Gunicorn start command is needed.
5. Add the environment variables below to the Production environment. Add them
   to Preview too if you want to exercise `/run` on preview deployments.
6. Deploy, then open `https://YOUR-PROJECT.vercel.app/health`.
   It should return a JSON response with `"status": "healthy"`.

## Environment variables

| Variable | Value / purpose |
| --- | --- |
| `AIRLABS_API_KEY` | Required for flight retrieval. |
| `RUN_ID` | Required to authorize `/run`; choose a long random secret. |
| `AIRPORT_ICAO` | Optional; defaults to `KDAL`. |
| `AIRLINES_FILTER` | Optional; defaults to `WN,DL`. |
| `FLIGHTS_LIMIT` | Optional; defaults to `10`. |
| `EMAIL_ENABLED` | `False` initially; use `True` to send reports. |
| `BREVO_API_KEY` | Required when email is enabled. |
| `EMAIL_SENDER` | Required when email is enabled; a verified Brevo sender. |
| `EMAIL_RECIPIENT` | Required when email is enabled. |
| `EMAIL_SENDER_NAME` | Optional; defaults to `Last Flight Bot`. |
| `LOG_LEVEL` | Optional; defaults to `INFO`. |

Use `.env.example` as the settings reference. Local `.env` files are excluded
from deployment. Redeploy after changing Vercel environment variables.

## Endpoints

- `GET /health`: health check; does not call AirLabs or send email.
- `GET /status`: current non-secret configuration.
- `POST /run?id=YOUR_RUN_ID` (or `GET`): retrieve flights and, if enabled, send
  the email report. Missing, empty, or incorrect run IDs return HTTP 403.

For example, using curl (`curl.exe` in Windows PowerShell):

```bash
curl https://YOUR-PROJECT.vercel.app/health
curl -X POST "https://YOUR-PROJECT.vercel.app/run?id=YOUR_URL_ENCODED_RUN_ID"
```

The root URL `/` has no page and returns 404; use `/health` to check deployment.
Health alone does not validate API credentials. A successful authorized `/run`
checks the integration and may send a real email when enabled.

## Logs and scheduling

On Vercel, server logs go to stdout and appear in the deployment's runtime logs.
Local and Render server runs still write to `LOG_FILE`. The Brevo request has
a 15-second timeout so an unresponsive email service does not wait indefinitely.

No Vercel cron job is enabled by this configuration. The repository already has
a scheduled GitHub Actions workflow. To trigger this API from an external
scheduler, use the authenticated `/run` URL above. Avoid scheduling the same
report in multiple places if you want only one email.

The existing `Procfile`, `render.yaml`, and `runtime.txt` are for the previous
hosting setup; Vercel uses the configuration described above.

References: [Flask on Vercel](https://vercel.com/docs/frameworks/backend/flask)
and [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python).
