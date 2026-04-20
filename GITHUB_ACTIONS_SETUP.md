# GitHub Actions Setup Guide

This guide will help you set up the Last Flight Reporter to run automatically on a schedule using GitHub Actions.

## Step 1: Prepare Your Repository

Make sure you have:
1. Created a public GitHub repository
2. Cloned it to your local machine
3. Added the project files to it
4. Created a `.env.example` file (not `.env` - no credentials!)

**Critical**: Never commit `.env` files with real credentials to a public repository!

## Step 2: Create GitHub Secrets

Your API keys and email credentials should be stored as **GitHub Secrets**, not in code.

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these secrets:

| Secret Name | Value | Where to Get |
|-------------|-------|-------------|
| `AIRLABS_API_KEY` | Your AirLabs API key | https://airlabs.co/ (sign up, then API section) |
| `EMAIL_SENDER` | Your Gmail address | example@gmail.com |
| `EMAIL_SENDER_PASSWORD` | Gmail app-specific password | See below |
| `EMAIL_RECIPIENT` | Manager's email | manager@example.com |

### Getting Gmail App-Specific Password

Since Gmail blocks regular password login from apps for security reasons:

1. Enable 2-Step Verification on your Google account:
   - Go to https://myaccount.google.com
   - Click "Security" in the left sidebar
   - Enable "2-Step Verification"

2. Generate app-specific password:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or your device type)
   - Google generates a 16-character password
   - **Copy it (it won't be shown again)**
   - Remove spaces and add it as `EMAIL_SENDER_PASSWORD` secret

## Step 3: Create the Workflow File

Create a new file: `.github/workflows/flight-report.yml`

```yaml
name: Daily Flight Report

on:
  schedule:
    # Run at 8 AM EST every day (convert to UTC: 8 AM EST = 1 PM UTC = 13:00)
    # Cron format: minute hour day month day-of-week
    - cron: '0 13 * * *'
  
  # Allow manual trigger from Actions tab
  workflow_dispatch:

jobs:
  send-flight-report:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r Project_last_flight/requirements.txt

      - name: Run flight reporter
        env:
          AIRLABS_API_KEY: ${{ secrets.AIRLABS_API_KEY }}
          EMAIL_ENABLED: 'True'
          EMAIL_SENDER: ${{ secrets.EMAIL_SENDER }}
          EMAIL_SENDER_PASSWORD: ${{ secrets.EMAIL_SENDER_PASSWORD }}
          EMAIL_RECIPIENT: ${{ secrets.EMAIL_RECIPIENT }}
          AIRPORT_ICAO: KDAL
          AIRLINES_FILTER: WN,DL
          FLIGHTS_LIMIT: 10
        run: |
          cd Project_last_flight
          python app.py

      - name: Upload logs as artifacts
        if: always()  # Upload even if the job fails
        uses: actions/upload-artifact@v4
        with:
          name: flight-report-logs
          path: Project_last_flight/flights.log
          retention-days: 7

      - name: Notify on failure
        if: failure()
        run: echo "Flight report failed - check logs in Actions tab"
```

## Step 4: Understanding the Cron Schedule

The cron expression `0 13 * * *` means:
- **0** = at minute 0
- **13** = at 13:00 (1 PM UTC)
- **\*** = every day
- **\*** = every month
- **\*** = every day of the week

### Common Schedule Examples:

```yaml
# Every day at 8 AM EST (1 PM UTC)
- cron: '0 13 * * *'

# Every day at 9 AM EST (2 PM UTC)
- cron: '0 14 * * *'

# Every weekday at 8 AM EST (Monday-Friday)
- cron: '0 13 * * 1-5'

# Every Monday at 8 AM EST
- cron: '0 13 * * 1'

# Every 6 hours
- cron: '0 */6 * * *'

# Every day at midnight EST (5 AM UTC)
- cron: '0 5 * * *'
```

**Tip**: Use https://crontab.guru to validate cron expressions

## Step 5: Test the Workflow

### Manual Test (First Time)

1. Go to your repository
2. Click **Actions** tab
3. Click **Daily Flight Report** workflow on the left
4. Click **Run workflow** → **Run workflow**

### Expected Results

After the workflow runs:
1. Email should be sent to your manager
2. Check logs by:
   - Going to **Actions** tab
   - Clicking the workflow run
   - Clicking the **send-flight-report** job
   - Scrolling to see output
   - Downloading **flight-report-logs** artifact to see detailed logs

## Step 6: Monitor and Troubleshoot

### Check Logs in GitHub

1. **Actions** tab → Latest workflow run
2. Look for **send-flight-report** job
3. Expand steps to see detailed output

### Common Issues

**Email not sending:**
- Verify `EMAIL_SENDER_PASSWORD` is the app-specific password (16 chars), not regular password
- Confirm 2-Step Verification is enabled
- Check if Gmail blocked the login (check Gmail security alerts)

**API Error:**
- Verify `AIRLABS_API_KEY` is correct
- Check if API key has reached rate limit
- Visit https://airlabs.co/status to check API status

**Workflow not triggering:**
- Go to **Actions** tab and enable workflows (if disabled)
- Verify the `.github/workflows/flight-report.yml` file is in main branch
- Wait up to 10 minutes for cron to trigger (GitHub doesn't guarantee exact timing)

### View Workflow Status

Add a status badge to your README:

```markdown
![Workflow Status](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/flight-report.yml/badge.svg)
```

## Step 7: Customize the Schedule

### Run Multiple Times Per Day

```yaml
on:
  schedule:
    - cron: '0 13 * * *'  # 1 PM UTC
    - cron: '0 19 * * *'  # 7 PM UTC
```

### Run on Push to Main

```yaml
on:
  push:
    branches:
      - main
  schedule:
    - cron: '0 13 * * *'
```

### Add Slack Notifications

Add this step after the flight reporter runs:

```yaml
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "Flight Report Status: ${{ job.status }}"
      }
```

## Step 8: Advanced Configuration

### Different Settings for Different Schedules

```yaml
jobs:
  morning-report:
    # Morning report with different settings
    ...
  
  evening-report:
    # Evening report with different settings
    ...
```

### Add Email Notifications to GitHub

```yaml
- name: Slack notification
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Flight report workflow failed'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## Security Best Practices

✅ **DO:**
- Store all credentials in GitHub Secrets
- Use app-specific passwords for Gmail
- Keep `.env` file in `.gitignore`
- Review scheduled workflow logs regularly
- Rotate API keys periodically

❌ **DON'T:**
- Commit `.env` files with credentials
- Hardcode API keys in workflow files
- Use your Gmail password directly
- Share secret values in issues/PRs
- Use overly permissive cron schedules

## Troubleshooting Checklist

- [ ] Workflow file created in `.github/workflows/flight-report.yml`
- [ ] All 4 secrets added: AIRLABS_API_KEY, EMAIL_SENDER, EMAIL_SENDER_PASSWORD, EMAIL_RECIPIENT
- [ ] Gmail 2-Step Verification enabled
- [ ] Gmail app-specific password used (not regular password)
- [ ] Cron expression validated on crontab.guru
- [ ] Workflow enabled in Actions tab
- [ ] Test manual run from Actions tab
- [ ] Check logs after first scheduled run

## Need Help?

- **Cron timing issues**: https://crontab.guru
- **GitHub Actions docs**: https://docs.github.com/en/actions
- **Gmail setup issues**: https://support.google.com/accounts/answer/185833
- **AirLabs API issues**: https://airlabs.co/docs/
