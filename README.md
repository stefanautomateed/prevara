# Noro.rs Form Automation Tool

Automated form filling tool for noro.rs using Playwright. This tool generates random Serbian names, addresses, and phone numbers to fill out forms multiple times per day.

## Features

- 🤖 Automated form filling with Playwright
- 🇷🇸 Random Serbian data generation (names, addresses, phone numbers)
- ⏰ Scheduled runs at configurable times
- 📝 Comprehensive logging
- 🎭 Stealth mode to avoid detection
- 📸 Screenshot capture for debugging

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd prevara
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

5. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

## Configuration

Edit the `.env` file to configure the tool:

```bash
# Schedule times (24-hour format, comma-separated)
SCHEDULE_TIMES=10:00,14:00,18:00

# Target website
TARGET_URL=https://noro.rs/

# Browser settings
HEADLESS=false  # Set to true to run without visible browser

# Delays between actions (seconds)
MIN_DELAY=1
MAX_DELAY=3
```

## Usage

### Test Mode (Run Once)

Run the form filler once with a visible browser to test and debug:

```bash
python main.py --test
```

Run once in headless mode:

```bash
python main.py --test --headless
```

### Run Once Immediately

Run once with the settings from `.env`:

```bash
python main.py --now
```

### Scheduled Mode

Run the form filler on the schedule defined in `.env`:

```bash
python main.py --schedule
```

Or simply:

```bash
python main.py
```

The scheduler will run continuously and execute form fills at the specified times.

### Custom URL

Override the target URL from command line:

```bash
python main.py --test --url "https://example.com"
```

## Project Structure

```
prevara/
├── main.py                      # Main entry point
├── form_filler.py              # Core form filling logic
├── scheduler.py                 # Scheduling functionality
├── serbian_data_generator.py   # Random Serbian data generation
├── requirements.txt             # Python dependencies
├── .env                         # Configuration (create from .env.example)
├── .env.example                 # Example configuration
├── .gitignore                   # Git ignore rules
├── logs/                        # Log files and screenshots (auto-created)
└── README.md                    # This file
```

## Generated Data

The tool generates realistic Serbian data:

### Names
- Common Serbian first names (male/female)
- Common Serbian last names
- Example: "Marko Jovanović", "Ana Petrović"

### Phone Numbers
- Starts with 063, 064, or 069
- Format: 06X/XXXXXXX or 06XXXXXXXXX
- Example: "0631234567"

### Addresses
- Common Serbian street names
- Random street numbers
- Serbian cities
- Postal codes
- Example: "Kralja Petra 45, Beograd, 11000"

### Emails
- Generated from names with random numbers
- Common domains (gmail.com, yahoo.com, etc.)
- Example: "marko.jovanovic123@gmail.com"

## Important Notes

### Form Submission Safety

**By default, the actual form SUBMISSION is DISABLED** in `form_filler.py` for safety.

To enable actual form submission:

1. Open `form_filler.py`
2. Find the section with `# UNCOMMENT TO ACTUALLY SUBMIT THE FORM`
3. Uncomment the submit button click code
4. Test thoroughly before running on schedule

### Customizing Form Selectors

The current form selectors are **generic placeholders**. You need to:

1. Run in test mode: `python main.py --test`
2. Inspect the website's actual form fields
3. Update the selectors in `form_filler.py` to match the real form
4. Look for the selector lists in the `fill_form()` method

Example fields to customize:
- `name_selectors`
- `phone_selectors`
- `email_selectors`
- `address_selectors`
- `city_selectors`
- `postal_selectors`
- `submit_selectors`

### Debugging

- Check `logs/` directory for:
  - `form_filler.log` - Form filling logs
  - `scheduler.log` - Scheduler logs
  - `main.log` - Main application logs
  - Screenshots (taken before/after form submission and on errors)

## Running in Background

### Linux/Mac (using screen or tmux)

```bash
# Using screen
screen -S form-filler
python main.py --schedule
# Press Ctrl+A then D to detach

# To reattach
screen -r form-filler
```

```bash
# Using tmux
tmux new -s form-filler
python main.py --schedule
# Press Ctrl+B then D to detach

# To reattach
tmux attach -t form-filler
```

### As a systemd service (Linux)

Create `/etc/systemd/system/form-filler.service`:

```ini
[Unit]
Description=Form Filler Service
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/prevara
ExecStart=/path/to/prevara/venv/bin/python main.py --schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable form-filler
sudo systemctl start form-filler
sudo systemctl status form-filler
```

## Troubleshooting

### Playwright timeout errors
- Increase timeout values in `form_filler.py`
- Check your internet connection
- Ensure the website is accessible

### Form fields not found
- Run in test mode with visible browser
- Inspect the actual HTML elements on the website
- Update selectors in `form_filler.py`
- Check screenshots in `logs/` directory

### Browser not launching
- Run `playwright install chromium` again
- Check system dependencies: `playwright install-deps chromium`

### 403 Forbidden errors
- The website may have anti-bot protection
- Try running in non-headless mode
- Increase delays between actions
- Consider adding more human-like behavior

## Development

### Testing the data generator

```bash
python serbian_data_generator.py
```

### Adding new features

1. Test locally with `--test` mode first
2. Check logs in `logs/` directory
3. Review screenshots for debugging
4. Update this README with new features

## License

This tool is for educational and testing purposes only. Use responsibly and in accordance with the target website's terms of service.

## Security

- Never commit `.env` file to version control
- Keep logs directory out of version control
- Review screenshots before sharing as they may contain sensitive data
