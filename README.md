# Last Flight Reporter

A modular Python application that fetches the latest flight arrival information and optionally sends email reports to your manager.

## Features

- **Modular Architecture**: Separate concerns into distinct modules:
  - `api_client.py` - API communication
  - `data_processor.py` - Data filtering and formatting
  - `email_service.py` - Email sending functionality
  - `config.py` - Centralized configuration management

- **Configurable**: All settings via environment variables
- **Email Reporting**: Send formatted HTML/plain text emails
- **Logging**: Comprehensive logging to file and console
- **GitHub Actions Ready**: Works perfectly with scheduled workflows

## Project Structure

```
Project_last_flight/
├── app.py                 # Main application orchestrator
├── api_client.py          # AirLabs API client
├── data_processor.py      # Flight data processing
├── email_service.py       # Email sending service
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- AirLabs API key (get one at https://airlabs.co/)

### Setup

1. Clone the repository and navigate to the project directory:
```bash
cd Project_last_flight
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the template:
```bash
cp .env.example .env
```

5. Edit `.env` and add your configuration:
```env
AIRLABS_API_KEY=your_actual_api_key
AIRPORT_ICAO=KDAL
AIRLINES_FILTER=WN,DL
FLIGHTS_LIMIT=10
EMAIL_ENABLED=False  # Set to True when ready to send emails
```

## Configuration

All settings are managed through environment variables in `.env`:

### API Settings
- `AIRLABS_API_KEY` (**Required**) - Your AirLabs API key
- `AIRPORT_ICAO` - Airport ICAO code (default: `KDAL`)
- `AIRLINES_FILTER` - Comma-separated airline IATA codes (default: `WN,DL`)
- `FLIGHTS_LIMIT` - Maximum flights to report (default: `10`)

### Email Settings (Optional)
- `EMAIL_ENABLED` - Set to `True` to enable email (default: `False`)
- `EMAIL_SENDER` - Sender email address (required if enabled)
- `EMAIL_SENDER_PASSWORD` - **Gmail: Use an App-Specific Password**, not your regular password
- `EMAIL_RECIPIENT` - Manager's email address
- `EMAIL_SMTP_SERVER` - SMTP server (default: `smtp.gmail.com`)
- `EMAIL_SMTP_PORT` - SMTP port (default: `587`)

### Logging Settings
- `LOG_LEVEL` - Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)
- `LOG_FILE` - Log file name (default: `flights.log`)

### Gmail App-Specific Password Setup

If you're using Gmail as the email sender:

1. Enable 2-Step Verification on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer" (or your device)
4. Google will generate a 16-character password
5. Use this password in `EMAIL_SENDER_PASSWORD` (remove spaces)

## Usage

### Local Testing

Run the application:
```bash
python app.py
```

Expected output:
```
SCH        ETA                FLIGHT     FROM   STATUS
------------------------------------------------------------
14:30      14:45              SW4521     LAX    landed
15:00      15:15              DL2891     JFK    scheduled
...
```

### GitHub Actions Setup

Create a `.github/workflows/flight-report.yml` file:

```yaml
name: Daily Flight Report

on:
  schedule:
    # Run at 8 AM every day (UTC)
    - cron: '0 8 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  send-flight-report:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

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

      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: flight-report-logs
          path: Project_last_flight/flights.log
```

#### GitHub Secrets Setup

Add these secrets to your repository (Settings → Secrets and variables → Actions):

- `AIRLABS_API_KEY` - Your AirLabs API key
- `EMAIL_SENDER` - Your Gmail address
- `EMAIL_SENDER_PASSWORD` - Gmail app-specific password
- `EMAIL_RECIPIENT` - Manager's email address

**Important**: Never commit `.env` files with real credentials to public repositories!

## Customization

### Changing Airlines
Edit the `AIRLINES_FILTER` environment variable:
```env
AIRLINES_FILTER=UA,AA,BA  # United, American, British Airways
```

### Changing Airport
Edit the `AIRPORT_ICAO` variable:
```env
AIRPORT_ICAO=KORD  # Chicago O'Hare
```

### Changing Email Formatting
Edit the `_format_html_content()` and `_format_text_content()` methods in `email_service.py`.

### Adding New Features
The modular structure makes it easy to extend:
- Add filters in `data_processor.py`
- Add API endpoints in `api_client.py`
- Add notification methods (Slack, Teams) alongside `email_service.py`

## Troubleshooting

### "AIRLABS_API_KEY is required"
Make sure your `.env` file exists and contains `AIRLABS_API_KEY=your_key`

### Email not sending
- Check that `EMAIL_ENABLED=True`
- Verify Gmail 2-Step Verification is enabled
- Confirm you're using an app-specific password, not your regular password
- Check `flights.log` for detailed error messages

### API errors
- Verify your API key is valid
- Check your network connection
- Review AirLabs API documentation

### Logs
Check `flights.log` for detailed debugging information.

## License

MIT License - feel free to use this in your own projects!

## Support

For issues with AirLabs API, visit https://airlabs.co/docs/
For Gmail password issues, visit https://support.google.com/accounts/answer/185833
