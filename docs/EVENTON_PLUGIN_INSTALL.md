# EventON REST API Meta Fields - Installation Guide

## Problem
The WordPress REST API doesn't automatically save EventON's custom metadata fields (event dates, times, locations, etc.), so uploaded events appear in WordPress but not on the calendar.

## Solution
This PHP plugin registers EventON meta fields with the WordPress REST API so they save properly.

## Installation Steps

### Method 1: Direct File Upload (Recommended)

1. **Upload the plugin file:**
   - Log into your WordPress hosting (cPanel, FTP, or file manager)
   - Navigate to: `wp-content/plugins/`
   - Upload `eventon-rest-api-meta.php` to this directory

2. **Activate the plugin:**
   - Log into WordPress admin: https://sandbox.envisionperdido.org/wp-admin
   - Go to: **Plugins → Installed Plugins**
   - Find: **"EventON REST API Meta Fields"**
   - Click: **Activate**

3. **Verify activation:**
   - You should see a success message
   - The plugin will appear in your active plugins list

### Method 2: Via WordPress Admin (If File Upload Not Available)

1. **Create plugin folder:**
   - Ask your hosting provider or supervisor to create: `wp-content/plugins/eventon-rest-api-meta/`

2. **Upload file:**
   - Place `eventon-rest-api-meta.php` in that folder

3. **Activate** (same as Method 1, step 2)

## After Installation

### Delete the Old Events (IDs 608-684)
Since the old events don't have proper metadata, delete them:

1. Go to: **WordPress Admin → Events → All Events**
2. Select events with IDs 608-684 (or filter by date: Oct 29, 2025)
3. **Bulk Actions → Move to Trash**
4. Click **Apply**

### Re-upload Events with Proper Metadata

Run the upload script again:

```powershell
cd C:\Users\scott\UWF-Code\EnvisionPerdido
.\.venvEnvisionPerdido\Scripts\Activate.ps1
python scripts\wordpress_uploader.py pipeline_output\calendar_upload_20251020_225559.csv
```

This time the events will save with proper EventON metadata and appear on the calendar!

## Verification

After re-uploading, check:
1. **Calendar page**: https://sandbox.envisionperdido.org/events
2. **Events should now appear** with proper dates and times
3. **Format should match** the existing events you showed in the screenshot

## Troubleshooting

**If events still don't appear:**

1. Check plugin is activated: **Plugins → Installed Plugins**
2. Verify EventON is active
3. Clear WordPress cache: **Settings → EventON → Clear Cache**
4. Check event dates are in the future (past events may be hidden)

**If you get permission errors:**

- Ensure your WordPress Application Password has admin rights
- Check file permissions on the plugin file (should be 644)

## Technical Details

The plugin:
- Registers 25+ EventON meta fields with REST API
- Hooks into `rest_api_init` to expose fields
- Hooks into `rest_insert_ajde_events` to save metadata
- Sanitizes all input data for security
- Only allows authenticated users with edit permissions

## Files

- `eventon-rest-api-meta.php` - The WordPress plugin (place in wp-content/plugins/)
- This file explains installation and usage

## Support

If you have issues:
1. Check WordPress error logs
2. Verify EventON plugin is active
3. Confirm REST API is working: https://sandbox.envisionperdido.org/wp-json/wp/v2/ajde_events
4. Contact your supervisor or hosting provider for file access
