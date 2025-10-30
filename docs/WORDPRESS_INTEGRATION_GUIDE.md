# Complete WordPress Calendar Integration Guide

## System Overview

Your automated community calendar system is now complete! Here's the full workflow:

```
Chamber Website → Scrape Events → Classify with ML → Email Review → Upload to WordPress
```

## Part 1: WordPress Setup (One-Time)

### Step 1: Create WordPress Application Password

1. Log into WordPress admin at: https://your-wordpress-site.org/wp-admin
2. Go to **Users → Profile**
3. Scroll down to **Application Passwords** section
4. Enter a name: "Event Classification System"
5. Click **Add New Application Password**
6. **Copy the password** - it looks like: `xxxx xxxx xxxx xxxx xxxx xxxx`
7. Save it somewhere safe!

### Step 2: Set Environment Variables

In PowerShell, run these commands (replace with your actual values):

```powershell
# WordPress credentials
$env:WP_SITE_URL = "https://your-wordpress-site.org"
$env:WP_USERNAME = "your_wordpress_username"
$env:WP_APP_PASSWORD = "xxxx xxxx xxxx xxxx xxxx xxxx"

# Email credentials (for review emails)
$env:SMTP_SERVER = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SENDER_EMAIL = "your_email@gmail.com"
$env:EMAIL_PASSWORD = "your_gmail_app_password"
$env:RECIPIENT_EMAIL = "your_email@gmail.com"
```

**To make these permanent:**
1. Windows Search → "Environment Variables"
2. "Edit the system environment variables"
3. Click "Environment Variables" button
4. Under "User variables", click "New"
5. Add each variable name and value

## Part 2: Complete Workflow

### Option A: Fully Automated (Recommended)

Create a batch file `run_pipeline.bat`:

```batch
@echo off
cd path\to\EnvisionPerdido
call .venvEnvisionPerdido\Scripts\activate.bat

echo ========================================
echo Running Event Classification Pipeline
echo ========================================
python scripts\automated_pipeline.py

echo.
echo Pipeline complete! Check your email for review.
echo.
pause
```

**Schedule it to run weekly:**
1. Open Task Scheduler
2. Create Basic Task → Name: "Community Events Pipeline"
3. Trigger: Weekly, Monday 9:00 AM
4. Action: Start a program → Browse to your `run_pipeline.bat`

### Option B: Manual Review Workflow

**Step 1: Run the pipeline**
```powershell
python scripts\automated_pipeline.py
```

This will:
- Scrape latest events from chamber website
- Classify them with your ML model (96.47% accuracy!)
- Send you an email with results
- Save CSV file in `pipeline_output/`

**Step 2: Review the email**
- Check events marked "Review Needed" (low confidence)
- Review the CSV file attached
- Make any corrections needed

**Step 3: Upload to WordPress**
```powershell
python scripts\wordpress_uploader.py
```

This will:
- Test WordPress connection
- Show you all events in dry-run mode
- Ask for confirmation
- Upload events as DRAFTS first
- Ask if you want to publish

**Step 4: Final review in WordPress**
- Log into WordPress admin
- Go to Events → All Events
- Review draft events
- Publish when ready!

## Part 3: Complete Hands-Off Setup

For completely automated operation with human-in-the-loop review:

### Create Master Script `automated_review.py`:

```python
# This would:
# 1. Run pipeline
# 2. Send email with approve/reject links
# 3. Wait for your email reply
# 4. Auto-upload approved events
# 5. Send confirmation
```

**Would you like me to build this next?**

## Understanding the System

### File Structure
```
EnvisionPerdido/
├── scripts/
│   ├── automated_pipeline.py       # Main automation script
│   ├── wordpress_uploader.py       # WordPress upload script
│   ├── auto_label_and_train.py    # Retrain model with new data
│   └── ...
├── pipeline_output/                # Generated files
│   ├── scraped_events_*.csv       # Raw scraped data
│   └── calendar_upload_*.csv      # Classified community events
├── event_classifier_model.pkl     # Trained ML model (96.47% accurate)
├── event_vectorizer.pkl           # Feature extractor
└── perdido_events_2025_labeled.csv # Training data (424 events)
```

### Data Flow

1. **Scraping**: Chamber website → Raw CSV
2. **Classification**: ML model → Community vs Non-community
3. **Review**: Email notification → Your review
4. **Upload**: WordPress REST API → Calendar

### Model Performance

Current model statistics:
- **Accuracy**: 96.47%
- **Training data**: 424 labeled events
- **Features**: Title, description, location, category
- **Method**: SVM with TF-IDF vectorization

## Troubleshooting

### WordPress Upload Issues

**"Authentication failed"**
- Verify Application Password is correct
- Check username matches WordPress admin
- Ensure REST API is enabled

**"Event not created"**
- Check EventON plugin is active
- Verify you have permission to create events
- Check WordPress error logs

**"Location not found"**
- Locations will be created automatically
- Check EventON location settings

### Email Issues

**Email not sending**
- For Gmail: Use App Password, not regular password
- Enable "Less secure app access" if needed
- Check firewall/antivirus settings

**Email in spam**
- Add sender to contacts
- Mark as "Not spam"

### Classification Issues

**Low accuracy**
- Retrain model: `python scripts\auto_label_and_train.py`
- Add more labeled training data
- Review mislabeled events

**Too many events need review**
- Model is being cautious (confidence < 75%)
- This is good! Better safe than sorry
- Over time, retrain with corrections

## Testing the System

### Test 1: Pipeline Only (No Upload)
```powershell
python scripts\automated_pipeline.py
```
Check: Email received, CSV generated

### Test 2: WordPress Connection
```powershell
python scripts\wordpress_uploader.py
```
Check: Connection successful, events shown in dry-run

### Test 3: Upload One Event
1. Create test CSV with one event
2. Run uploader
3. Confirm upload
4. Check WordPress admin

### Test 4: Full End-to-End
1. Run pipeline
2. Review email
3. Upload to WordPress
4. Verify on website

## Maintenance

### Weekly Tasks
- Review email notifications
- Upload approved events
- Check classification accuracy

### Monthly Tasks
- Retrain model with new data
- Review any consistently mislabeled events
- Update keywords if needed

### As Needed
- Update WordPress credentials if changed
- Adjust confidence threshold
- Add new event types

## Next Steps

1. **Get WordPress credentials** from your supervisor
2. **Run test**: `python scripts\wordpress_uploader.py`
3. **Set up email** if you want notifications
4. **Schedule automation** with Task Scheduler
5. **Document for supervisor** - show them the workflow!

## Questions?

Common questions:
- **Is it safe?** Yes, events upload as DRAFTS first for your review
- **What if it makes mistakes?** You review before publishing
- **Can I edit events?** Yes, edit in WordPress admin anytime
- **How often should I run it?** Weekly or bi-weekly is typical
- **What if the chamber website changes?** We'll update the scraper

## Success Metrics

You'll know it's working when:
✓ Pipeline runs without errors
✓ You receive regular email notifications  
✓ Classification accuracy stays high (>90%)
✓ Events appear correctly in WordPress
✓ Website shows community events properly

---

**Ready to test?** Let's start with:
```powershell
python scripts\wordpress_uploader.py
```

This will guide you through the WordPress setup and test your connection!
