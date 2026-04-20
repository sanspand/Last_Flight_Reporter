# Render Deployment Checklist

This checklist helps you deploy the Last Flight application to Render.

## Pre-Deployment

- [ ] All code committed to GitHub
- [ ] `.env` file is NOT committed (check `.gitignore`)
- [ ] `requirements.txt` updated with all dependencies
- [ ] `Procfile` exists with: `web: gunicorn server:app`
- [ ] `runtime.txt` specifies Python version
- [ ] Local testing completed: `python server.py` works
- [ ] Test the `/health` endpoint responds with status 200

## Render Setup

- [ ] Render account created at https://render.com
- [ ] Repository connected to Render
- [ ] Web Service created
- [ ] Build Command set to: `pip install -r requirements.txt`
- [ ] Start Command set to: `gunicorn server:app`

## Environment Variables in Render

Add these environment variables in Render Dashboard → Environment:

**Required:**
- [ ] `AIRLABS_API_KEY` - Your AirLabs API key
- [ ] `AIRPORT_ICAO` - Airport code (e.g., KDAL)

**Optional but Recommended:**
- [ ] `AIRLINES_FILTER` - Comma-separated airline codes (e.g., WN,DL)
- [ ] `FLIGHTS_LIMIT` - Maximum flights to show (e.g., 10)
- [ ] `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING, ERROR)

**Email Configuration (if using email):**
- [ ] `EMAIL_ENABLED` - Set to `true` to enable
- [ ] `EMAIL_SENDER` - Sender's Gmail address
- [ ] `EMAIL_SENDER_PASSWORD` - Gmail app-specific password
- [ ] `EMAIL_RECIPIENT` - Manager's email address

## Testing on Render

After deployment:

1. [ ] Health check passes: `curl https://your-service.onrender.com/health`
2. [ ] Status endpoint works: `curl https://your-service.onrender.com/status`
3. [ ] Run endpoint works: `curl -X POST https://your-service.onrender.com/run`
4. [ ] Check logs in Render dashboard for any errors

## External Cron Setup

Using cron-job.org or EasyCron:

- [ ] Create new scheduled job
- [ ] URL: `https://your-service.onrender.com/run`
- [ ] Method: POST
- [ ] Schedule: Set your desired time (e.g., 8:00 AM daily)
- [ ] Notifications: Enable email alerts on failure

## Troubleshooting

**Service won't start:**
- Check Render logs for error messages
- Verify all environment variables are set
- Ensure `requirements.txt` has all dependencies (Flask, Gunicorn)

**Cron job not triggering:**
- Verify the URL is correct
- Try manual curl from your terminal
- Check Render service is running (status should be "Live")

**Emails not sending:**
- Verify `EMAIL_ENABLED=true`
- Check Gmail app-specific password is correct
- Review logs in Render dashboard

**Cold start issues:**
- Render free tier shuts down after 15 minutes
- Use cron service to wake it up before actual scheduled time
- Or use paid tier for always-on service

## Useful Commands

**Local testing:**
```bash
python server.py  # Runs on http://localhost:5000
```

**Test endpoints locally:**
```bash
curl http://localhost:5000/health
curl -X POST http://localhost:5000/run
curl http://localhost:5000/status
```

**View logs:**
- Render Dashboard → Your Service → Logs tab
- Or check `flights.log` file if viewing logs locally

## Support

- Render Docs: https://render.com/docs
- AirLabs API Docs: https://airlabs.co/docs/
- Flask Docs: https://flask.palletsprojects.com/
- Gunicorn Docs: https://docs.gunicorn.org/
