# EIN Application Automation

This script automates filling out the IRS EIN (Employer Identification Number) application form using Playwright with anti-bot detection measures.

## Files Created

- `ein_data.json` - Your business data configuration file
- `ein_automation.py` - Main automation script
- `setup_ein_automation.py` - Installation and setup script
- `requirements.txt` - Python dependencies

## Quick Start

1. **Install dependencies:**
   ```bash
   python setup_ein_automation.py
   ```

2. **Edit your data:**
   Open `ein_data.json` and fill in all your business information

3. **Run the automation:**
   ```bash
   python ein_automation.py
   ```

## How It Works

1. **Data Review Modal**: Shows all your data for review before starting
2. **Site Availability Check**: Tests if IRS site is accessible
3. **Browser Automation**: Opens Chrome with anti-detection measures
4. **Form Filling**: Automatically fills form fields based on your data
5. **Manual Submission**: Stops before final submission for your control

## Key Features

### Anti-Bot Detection
- Realistic user agent strings
- Human-like typing delays
- Random mouse movements
- Proper browser fingerprinting

### Error Handling
- Multiple URL attempts
- Site outage detection
- Retry mechanisms
- Detailed logging

### Safety Features
- Always stops before final submission
- Screenshots saved for debugging
- Browser stays open for manual review
- Detailed logging to `ein_automation.log`

## Data File Structure

Edit `ein_data.json` with your information:

```json
{
  "business_info": {
    "legal_name": "Your Business Legal Name",
    "trade_name_dba": "Your DBA Name (if any)",
    "mailing_address": {
      "street": "123 Main St",
      "city": "Your City",
      "state": "ST",
      "zip_code": "12345"
    }
  },
  "responsible_party": {
    "name": "Your Full Name",
    "ssn_itin": "123-45-6789",
    "title": "Owner"
  }
  // ... more fields
}
```

## Important Notes

- **One EIN per day limit**: IRS only allows 1 EIN application per responsible party per day
- **15-minute timeout**: Application expires after 15 minutes of inactivity
- **Manual submission**: Script stops before final submission for your control
- **Site outages**: Handle intermittent IRS website issues gracefully

## Troubleshooting

### Site Access Issues
- Script checks multiple URLs automatically
- Handles 403/503 errors from IRS site
- Will notify you if site is down

### Browser Issues
- Uses Chrome with realistic settings
- Disable any ad blockers that might interfere
- Make sure Windows allows the browser to open

### Form Field Issues
- Script takes screenshots for debugging
- Check `screenshots/` folder if form isn't filling correctly
- Logs all actions to `ein_automation.log`

## Usage Tips

1. **Test with incomplete data first** to see how the form behaves
2. **Run during IRS business hours** (Mon-Fri, 7am-10pm ET)
3. **Have your data ready** - the 15-minute timeout is real
4. **Review everything** before final submission
5. **Keep the browser open** until you've successfully submitted

## Legal Disclaimer

This tool is for legitimate business EIN applications only. You are responsible for:
- Accuracy of all submitted information
- Compliance with IRS requirements
- Final review and submission of the application

The script is designed to assist with form filling only - you maintain full control over submission.