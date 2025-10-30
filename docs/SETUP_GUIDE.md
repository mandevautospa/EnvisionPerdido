# Community Event Classification System - Configuration

## System Overview
This system automatically scrapes events from the Perdido Chamber of Commerce website, classifies them as community/non-community events using machine learning, and prepares them for upload to your community calendar.

## Setup Instructions

### 1. Email Configuration
For email notifications, set these environment variables in PowerShell:

```powershell
# For Gmail (recommended for testing)
$env:SMTP_SERVER = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SENDER_EMAIL = "your_email@gmail.com"
$env:EMAIL_PASSWORD = "your_app_password"  # Use Gmail App Password, not regular password
$env:RECIPIENT_EMAIL = "your_email@gmail.com"
```

**Gmail App Password Setup:**
1. Go to Google Account settings
2. Security → 2-Step Verification → App passwords
3. Generate an app password for "Mail"
4. Use that password in EMAIL_PASSWORD

### 2. Run the Pipeline Manually

```powershell
python scripts\automated_pipeline.py
```

This will:
- Scrape current and next month's events
- Classify them using your trained model
- Send an email with results
- Save CSV files for calendar upload

### 3. Schedule Automatic Execution

#### Option A: Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Name: "Community Event Classification"
4. Trigger: Weekly (e.g., every Monday at 9 AM)
5. Action: Start a program
   - Program: `path\to\EnvisionPerdido\.venvEnvisionPerdido\Scripts\python.exe`
   - Arguments: `scripts\automated_pipeline.py`
   - Start in: `path\to\EnvisionPerdido`

#### Option B: PowerShell Script
Create a `.bat` file:
```batch
@echo off
cd path\to\EnvisionPerdido
call .venvEnvisionPerdido\Scripts\activate.bat
python scripts\automated_pipeline.py
```

### 4. Calendar Platform Integration

**You need to provide:**
- What calendar platform is your supervisor using? (WordPress, Google Calendar, custom PHP, etc.)
- Does it have an API or import functionality?
- What format does it accept? (CSV, iCal .ics, JSON, API)

**Common Integration Methods:**

#### WordPress with Events Plugin:
- Most accept CSV import or iCal files
- May have REST API for programmatic upload
- We can create a PHP plugin if needed

#### Google Calendar:
- Can use Google Calendar API
- Requires OAuth2 authentication
- Can import iCal (.ics) files

#### Custom PHP Calendar:
- Need database schema and API documentation
- Can create custom PHP upload script
- May need FTP/SSH access

## Output Files

All output is saved to `pipeline_output/` directory:
- `scraped_events_TIMESTAMP.csv` - Raw scraped data
- `calendar_upload_TIMESTAMP.csv` - Classified community events ready for upload

## Email Review Workflow

1. **Receive Email**: Check your inbox for classification results
2. **Review Events**: Check events marked "Review Needed" (low confidence)
3. **Download CSV**: Attached file contains all community events
4. **Upload to Calendar**: Use the upload method for your calendar platform

## Troubleshooting

### Email not sending?
- Check SMTP credentials
- For Gmail, ensure "Less secure app access" is enabled OR use App Password
- Check firewall settings

### Low classification accuracy?
- Retrain model with more labeled data
- Run: `python scripts\auto_label_and_train.py`

### Missing events?
- Check website is accessible
- Verify chamber website hasn't changed structure
- Check scraper logs for errors

## Next Steps

1. **Test the pipeline**: Run `python scripts\automated_pipeline.py`
2. **Check email**: Verify you receive the notification
3. **Provide calendar details**: Tell us about your calendar platform
4. **We'll build the upload mechanism**: Custom integration for your specific platform

## Questions to Answer

Please find out from your supervisor:
1. What is the calendar platform/CMS?
2. Do you have admin access to it?
3. Can it import CSV or iCal files?
4. Does it have an API we can use?
5. Do you need a PHP plugin created?

Once we know these details, we can build the final piece: automated calendar upload!
