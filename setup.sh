#!/bin/bash
# Setup script for the form automation tool

set -e

echo "=================================="
echo "Form Automation Tool Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "Virtual environment created!"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo ""

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo ""

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium
echo ""

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs
echo ""

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created! Please edit it with your settings."
else
    echo "✓ .env file already exists"
fi
echo ""

echo "=================================="
echo "Setup completed successfully!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your preferred settings"
echo "2. Run a test: python main.py --test"
echo "3. Inspect the website and update form selectors in form_filler.py"
echo "4. Enable form submission in form_filler.py (see README)"
echo "5. Run on schedule: python main.py --schedule"
echo ""
echo "For more information, see README.md"
