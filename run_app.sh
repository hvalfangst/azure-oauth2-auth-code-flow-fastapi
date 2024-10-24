#!/bin/bash

# Check if virtual environment exists, if not, create it
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python -m venv venv
fi

# Activate the virtual environment (use Scripts for Windows)
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" ]]; then
  # For Windows
  source venv/Scripts/activate
else
  # For Linux/Mac
  source venv/bin/activate
fi

# Upgrade pip to the latest version
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r server/requirements.txt

# Run the FastAPI application using uvicorn
echo "Starting FastAPI application..."
python -m uvicorn server.main:app --reload