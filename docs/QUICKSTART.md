# Community Calendar Automation - Quick Start Guide

### Step 1: Run the Automated Pipeline (Weekly/Monthly)

```powershell
python scripts\automated_pipeline.py
```

**What it does:**
1. ✓ Scrapes events for **current month + next month** only
2. ✓ Classifies using your **96.47% accurate ML model**
3. ✓ Saves classified events to CSV in `output/pipeline/`
4. ✓ Sends beautiful HTML email with:
   - Summary statistics
   - List of community events
   - Events flagged for review (low confidence)
   - Attached CSV file

### Step 2: Review Email & Approve

1. Check your inbox for "Community Event Review" email
2. Review the events table (especially ones marked "⚠️ Review Needed")
3. Download attached CSV if you want detailed info
4. Make decision: approve or edit

### Step 3: Upload to WordPress (After Approval)

```powershell
python scripts\wordpress_uploader.py
```

**What it does:**
1.  Tests WordPress connection
2.  Shows you all events in dry-run mode (preview)
3.  Asks for your confirmation: "Upload these events? (yes/no)"
4.  Uploads as **DRAFTS** first (safe!)
5.  Asks if you want to publish: "Publish them? (yes/no)"

---

## Email Setup (One-Time)

To receive email notifications, you need a Gmail App Password:

### Create Gmail App Password:
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification (if not already)
3. Go to App Passwords: https://myaccount.google.com/apppasswords
4. Select app: "Mail", device: "Windows Computer"
5. Click "Generate"
6. Copy the 16-character password

### Set Environment Variables (PowerShell):

```powershell
$env:SENDER_EMAIL = "your_email@gmail.com"
$env:EMAIL_PASSWORD = "your_16_char_app_password"
$env:RECIPIENT_EMAIL = "your_email@gmail.com"
```

**Make it permanent:**
- Windows Search → "Environment Variables"
- Edit system environment variables → Environment Variables
- Add under "User variables"

---

## WordPress Setup (One-Time)

### Create WordPress Application Password:
1. Login to: https://your-wordpress-site.org/wp-admin
2. Users → Your Profile
3. Scroll to "Application Passwords"
4. Name: "Event Uploader"
5. Click "Add New Application Password"
6. Copy the password (format: `xxxx xxxx xxxx xxxx xxxx xxxx`)

### Set Environment Variables (PowerShell):

```powershell
$env:WP_SITE_URL = "https://your-wordpress-site.org"
$env:WP_USERNAME = "your_wordpress_username"
$env:WP_APP_PASSWORD = "xxxx xxxx xxxx xxxx xxxx xxxx"
```

---

## Scheduling (Optional)

To run automatically every Monday at 9 AM:

1. Open **Task Scheduler**
2. Create Basic Task → "Community Events Pipeline"
3. Trigger: Weekly, Monday, 9:00 AM
4. Action: Start a program
   - Program: `path\to\EnvisionPerdido\.venvEnvisionPerdido\Scripts\python.exe`
   - Arguments: `scripts\automated_pipeline.py`
   - Start in: `path\to\EnvisionPerdido`

---

## Current System Status

✅ **Model Accuracy**: 96.47%  
✅ **Training Data**: 424 labeled events  
✅ **Confidence Threshold**: 75% (lower = flagged for review)  
✅ **Scraping**: Current month + next month only  

---

## File Locations

- **Pipeline Script**: `scripts/automated_pipeline.py`
- **Uploader Script**: `scripts/wordpress_uploader.py`
- **ML Model**: `data/artifacts/event_classifier_model.pkl` (96.47% accurate)
- **Output Files**: `output/pipeline/calendar_upload_*.csv`

---

## Common Questions

**Q: Do I need to scrape manually first?**  
A: No! The pipeline scrapes automatically. Just run `automated_pipeline.py`

**Q: What if I want to review before uploading?**  
A: Perfect! That's exactly how it works. Email → Review → Then manually run uploader.

**Q: Can I change what months to scrape?**  
A: Yes, it's set to current + next month. You can modify `scrape_events()` in the pipeline script.

**Q: What if the model makes a mistake?**  
A: Events upload as DRAFTS first. You can edit/delete in WordPress admin before publishing.

**Q: How often should I run this?**  
A: Weekly or bi-weekly is typical. Monthly works too.

---

## Next Steps

1. **Set up email credentials** (see above)
2. **Test the pipeline**: `python scripts\automated_pipeline.py`
3. **Check your email** for the review notification
4. **Set up WordPress credentials** (when ready to upload)
5. **Test upload**: `python scripts\wordpress_uploader.py`
6. **Schedule automation** (optional)

---

## Support

For issues or questions:
1. Check `WORDPRESS_INTEGRATION_GUIDE.md` for detailed docs
2. Review `SETUP_GUIDE.md` for troubleshooting
3. Check pipeline output logs for errors
