# Deployment Guide

This guide explains how to deploy the Proven Savings Calculator web application.

## Required Files

1. **Application Files**:
   - `app.py` - Main Flask application
   - `data_analysis/bank_stats.py` - Core business logic
   - `templates/new_index.html` - Web interface template
   - `data/money_saved_JPM2025.csv` - JPM savings data
   - `data/money_saved_svb2024.csv` - SVB savings data
   - `deployment_requirements.txt` - Python dependencies

## Deployment Steps

1. **Set Up Python Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r deployment_requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```

3. **For Production Deployment**:
   - Use a production-grade WSGI server like Gunicorn
   - Set up a reverse proxy (e.g., Nginx)
   - Configure SSL/TLS for HTTPS
   - Set environment variables:
     ```bash
     export FLASK_ENV=production
     export FLASK_APP=app.py
     ```

## Directory Structure
```
proven_savings/
├── app.py
├── data_analysis/
│   └── bank_stats.py
├── templates/
│   └── new_index.html
├── data/
│   ├── money_saved_JPM2025.csv
│   └── money_saved_svb2024.csv
└── deployment_requirements.txt
```
