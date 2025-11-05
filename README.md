# Smart Answer Sheet Processor

Intelligent PDF processing system for automated data extraction and LMS integration at Saveetha Engineering College.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-darkgreen.svg)](https://www.djangoproject.com/)
[![MongoDB](https://img.shields.io/badge/mongodb-4.0+-green.svg)](https://www.mongodb.com/)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Overview

Smart Answer Sheet Processor automates the extraction of student information from answer sheet PDFs, verifies LMS credentials, and uploads documents directly to the Saveetha Engineering College Learning Management System (LMS).

### What it does

1. Accepts PDF uploads from students
2. Extracts register numbers and subject codes using ML
3. Verifies credentials and subject URLs
4. Uploads directly to LMS via Selenium automation
5. Provides real-time status updates

## Features

- Batch PDF Upload - Upload multiple PDFs simultaneously
- ML-Powered Extraction - Automatic register number and subject code extraction
- Credential Verification - Real-time validation against MongoDB
- Subject URL Lookup - Automatic discovery of LMS submission endpoints
- LMS Automation - Direct upload via Selenium with Chrome
- Parallel Processing - Multi-threaded uploads (3 simultaneous)
- Real-time Monitoring - Live status polling with UI updates
- Recheck Configuration - Verify setup without re-uploading
- Error Handling - Detailed error messages for quick resolution
- Enterprise UI - Professional, clean interface

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend Framework | Django | 5.2.7 |
| Python Version | Python | 3.9+ |
| Database (NoSQL) | MongoDB | 4.0+ |
| Database (Local) | SQLite | Built-in |
| Automation | Selenium | 4.15.2 |
| ML/Deep Learning | PyTorch | 2.1.1 |
| Computer Vision | OpenCV | 4.8.1 |
| Task Queue | ThreadPoolExecutor | Built-in |

## Prerequisites

### System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10+, Linux, macOS |
| Python | 3.9 or higher |
| MongoDB | 4.0 or higher |
| Chrome/Chromium | Latest version |
| RAM | 4GB minimum, 8GB recommended |
| Storage | 2GB free space |

### Before You Start

Ensure you have:
- Python 3.9+ installed
- MongoDB Community Edition running
- Google Chrome browser
- Git installed
- Text editor (VS Code recommended)

## Installation

### Step 1: System Setup

#### Windows

Download and install:
1. Python 3.9+ from https://www.python.org/downloads/ (CHECK: "Add Python to PATH")
2. MongoDB from https://www.mongodb.com/try/download/community (CHECK: "Install MongoD as a Service")
3. Google Chrome from https://www.google.com/chrome/
4. Git from https://git-scm.com/

Verify installations:
```bash
python --version
mongosh
git --version
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Verify
mongosh  # Should connect successfully
```

#### macOS

```bash
# Install Homebrew first if not installed:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.9
brew tap mongodb/brew
brew install mongodb-community
brew install git

# Start MongoDB
brew services start mongodb-community

# Verify
mongosh
```

### Step 2: Repository Clone

```bash
# Clone the repository
git clone https://github.com/d-kavinraja/smart-answer-sheet-processor.git

# Navigate to project directory
cd smart-answer-sheet-processor

# Verify files
ls -la  # Linux/macOS
dir     # Windows
```

Expected output:
```
README.md
requirements.txt
.env.example
setup_db.py
manage.py
lms_project/
pdf_processor/
services/
```

### Step 3: Virtual Environment

A virtual environment isolates project dependencies.

#### Windows

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Expected: (venv) prompt appears
```

#### Linux/macOS

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Expected: (venv) prompt appears
```

Verify activation:
```bash
python --version
pip --version
# Should show correct paths inside venv
```

### Step 4: Dependencies

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This installs:
# - Django 5.2.7
# - PyMongo 4.6.0
# - Selenium 4.15.2
# - PyTorch 2.1.1
# - OpenCV 4.8.1.78
# - Plus 15+ more packages

# Verify installation
pip list | grep Django
pip list | grep pymongo
```

Note: Installation may take 5-10 minutes due to PyTorch size.

### Step 5: Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file (optional for development):
# On Windows: notepad .env
# On Linux/Mac: nano .env

# Add your configuration:
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Step 6: Database Setup

This creates MongoDB collections and inserts sample data.

```bash
# Run database setup script
python setup_db.py

# Expected output:
# ======================================================================
# Smart Answer Sheet Processor - MongoDB Setup
# ======================================================================
# 
# Connecting to MongoDB...
# Connected to MongoDB successfully
# 
# Creating collections...
#   Created collection: credentials
#   Created collection: subject_code_urls
#   Created collection: uploaded_files
# 
# Inserting sample credentials...
#   Inserted 5 credentials
# 
# Inserting sample subject code URLs...
#   Inserted 6 subject URLs
# 
# SAMPLE DATA CREATED SUCCESSFULLY
# ======================================================================
```

If MongoDB fails:
```bash
# Check MongoDB is running
mongosh

# Windows: Services → MongoDB → Start
# Linux: sudo systemctl start mongod
# macOS: brew services start mongodb-community
```

### Step 7: Django Setup

Django requires database migrations before first run.

```bash
# Apply database migrations
python manage.py migrate

# Expected output:
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, pdf_processor, sessions
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   Applying admin.0001_initial... OK
#   Applying pdf_processor.0001_initial... OK
#   Applying sessions.0001_initial... OK
```

### Step 8: Create Admin Account

Create a superuser account for Django admin.

```bash
python manage.py createsuperuser

# Interactive prompts:
# Username: admin
# Email address: admin@example.com
# Password: (enter secure password)
# Password (again): (confirm password)
# Superuser created successfully.
```

Save credentials - You will need these to log in.

### Step 9: Run Application

```bash
# Start development server
python manage.py runserver

# Expected output:
# Watching for file changes with StatReloader
# Performing system checks...
# 
# System check identified no issues (0 silenced).
# November 05, 2025 - 17:30:00
# Django version 5.2.7, using settings 'lms_project.settings'
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CTRL-BREAK.
```

### Access Application

Open your browser and go to: http://127.0.0.1:8000/

## Database Schema

### 1. Credentials Collection

Stores LMS login credentials mapped to student register numbers.

```javascript
{
  "_id": ObjectId,
  "registerNumber": "212221230038",
  "username": "22008681",
  "password": "encrypted_password",
  "createdAt": ISODate("2025-11-05T16:00:00Z")
}
```

Add new credentials:
```bash
mongosh lms_automation
```

```javascript
db.credentials.insertOne({
  "registerNumber": "212221230043",
  "username": "22008690",
  "password": "password123"
})
```

### 2. Subject Code URLs Collection

Maps subject codes to LMS assignment submission URLs.

```javascript
{
  "_id": ObjectId,
  "subject_code": "19AI505",
  "url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=1041&action=view",
  "createdAt": ISODate("2025-11-05T16:00:00Z")
}
```

Add new subject:
```javascript
db.subject_code_urls.insertOne({
  "subject_code": "19CSE503",
  "url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=500&action=view"
})
```

### 3. Uploaded Files Collection

Tracks all uploaded files and processing status.

```javascript
{
  "_id": ObjectId,
  "filename": "00001_212221230038_19AI505_CIA2.pdf",
  "registerNumber": "212221230038",
  "subjectCode": "19AI505",
  "pdfPath": "/path/to/file.pdf",
  "status": "Uploaded",
  "uploaded": true,
  "django_id": 1,
  "created_at": ISODate("2025-11-05T16:00:00Z")
}
```

## API Endpoints

All endpoints accept JSON and return JSON responses.

| HTTP | Endpoint | Description |
|------|----------|-------------|
| GET | `/` | Main dashboard |
| POST | `/api/upload/` | Upload PDF files |
| POST | `/api/process/<id>/` | Extract data from PDF |
| POST | `/api/recheck/<id>/` | Verify configuration |
| POST | `/api/upload-lms/<id>/` | Upload to LMS (single) |
| POST | `/api/upload-multiple-lms/` | Batch upload to LMS |
| POST | `/api/delete/<id>/` | Delete document |
| GET | `/api/status/<id>/` | Get upload status |
| GET | `/api/uploads/` | List all uploads |

Example API Call:
```bash
# Check status of upload ID 1
curl http://127.0.0.1:8000/api/status/1/

# Response:
{
  "success": true,
  "data": {
    "id": 1,
    "filename": "test.pdf",
    "status": "uploaded",
    "registerNumber": "212221230038",
    "subjectCode": "19AI505",
    "isUploaded": true
  }
}
```

## Usage Guide

### Complete Workflow

Step 1: Upload PDF
- User selects PDF file

Step 2: Extract Data
- ML extracts register & subject
- Click "Extract Data" button

Step 3: Verify Configuration
- Check credentials & subject URL
- Click "Recheck Configuration"

Step 4: Upload to LMS
- Click "Upload to LMS" button
- Selenium automates submission
- Status updates to "uploaded"

### User Instructions

1. Upload Document
   - Click "Choose PDF Files"
   - Select answer sheet PDF
   - Click "Upload Selected Files"

2. Extract Data
   - Click "Extract Data"
   - System extracts register number and subject code
   - Wait for "extracted" status

3. Verify Setup
   - Click "Recheck Configuration"
   - System checks credentials and subject URL
   - If missing, contact admin to update database

4. Upload to LMS
   - Once verified, click "Upload to LMS"
   - Confirm upload
   - Monitor real-time progress
   - Status updates to "uploaded" when done

5. Bulk Upload (Multiple Documents)
   - Extract data from multiple PDFs first
   - Click "Upload All Ready Documents"
   - Batch processes up to 3 documents simultaneously

## Troubleshooting

### MongoDB Connection Failed

Error: `ServerSelectionTimeoutError: localhost:27017`

Solutions:
```bash
# Check if MongoDB is running
mongosh

# Windows: Open Services app → Find MongoDB → Right-click → Start
# Linux: sudo systemctl start mongod
# macOS: brew services start mongodb-community

# Verify connection
mongosh lms_automation
```

### Credentials Not Found

Error: `LMS credentials not found for register 212221230038`

Solution:
```bash
# Check if credentials exist
mongosh lms_automation
db.credentials.findOne({registerNumber: "212221230038"})

# If not found, add credentials
db.credentials.insertOne({
  registerNumber: "212221230038",
  username: "22008681",
  password: "password123"
})
```

### Subject URL Not Configured

Error: `Subject URL for 19AI505 not configured`

Solution:
```bash
# Check if subject exists
mongosh lms_automation
db.subject_code_urls.findOne({subject_code: "19AI505"})

# If not found, add subject
db.subject_code_urls.insertOne({
  subject_code: "19AI505",
  url: "https://lms2.ai.saveetha.in/mod/assign/view.php?id=1041&action=view"
})
```

### PDF Data Extraction Failed

Error: `Unable to extract data from PDF`

Solutions:
- Ensure PDF is clear and readable
- Check register number and subject code are visible
- Try another PDF
- Verify text is not overlapping

### Port 8000 Already in Use

Error: `Address already in use (:8000)`

Solution:
```bash
# Use different port
python manage.py runserver 8001

# Or kill process using port 8000
# Windows: netstat -ano | findstr :8000
# Linux: lsof -i :8000
# macOS: lsof -i :8000
```

### Virtual Environment Not Activating

Error: `'venv' is not recognized` (Windows)

Solution:
```bash
# Try PowerShell instead of CMD
# Or use full path
C:\full\path\to\project\venv\Scripts\activate

# Or create venv again
python -m venv venv
venv\Scripts\activate
```

### Import Errors

Error: `ModuleNotFoundError: No module named 'django'`

Solution:
```bash
# Verify you're in virtual environment
# Check: (venv) should be in prompt

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
```

## Project Structure

```
smart-answer-sheet-processor/
|
├── README.md                   # Project documentation
├── INSTALLATION.md             # Installation guide
├── DEVELOPMENT.md              # Developer guide
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── .gitignore                  # Git ignore patterns
├── setup_db.py                 # Database setup script
├── manage.py                   # Django command manager
|
├── lms_project/                # Main Django project
│   ├── __init__.py
│   ├── settings.py             # Configuration
│   ├── urls.py                 # URL routing
│   └── wsgi.py                 # WSGI config
|
├── pdf_processor/              # Main app
│   ├── migrations/             # Database changes
│   ├── models.py               # Database models
│   ├── views.py                # Business logic (API)
│   ├── urls.py                 # App routing
│   ├── apps.py                 # App config
│   ├── admin.py                # Django admin
│   ├── templates/
│   │   └── pdf_processor/
│   │       └── index.html      # Main UI
│   └── tests.py                # Tests
|
├── services/                   # External services
│   ├── ml_service.py           # PDF text extraction
│   ├── lms_automation.py       # Selenium LMS upload
│   └── parallel_lms_uploader.py # Batch upload
|
├── media/                      # User uploads (auto-created)
│   ├── uploads/
│   └── cropped/
│       ├── register/
│       └── subject/
|
└── models/                     # ML models (auto-created)
    ├── improved_weights.pt
    └── best_model.pth
```

## Contributing

We welcome contributions! Here's how to contribute:

1. Fork Repository
   - Go to https://github.com/d-kavinraja/smart-answer-sheet-processor
   - Click "Fork" button

2. Clone Your Fork
   ```bash
   git clone https://github.com/d-kavinraja/smart-answer-sheet-processor.git
   cd smart-answer-sheet-processor
   ```

3. Create Feature Branch
   ```bash
   git checkout -b feature/amazing-feature
   ```

4. Commit Changes
   ```bash
   git add .
   git commit -m "Add amazing feature"
   ```

5. Push to Branch
   ```bash
   git push origin feature/amazing-feature
   ```

6. Open Pull Request
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Describe your changes
   - Submit!

## License

This project is licensed under the MIT License - see the LICENSE file for details.

MIT License Summary:
- Commercial use allowed
- Modification allowed
- Distribution allowed
- Private use allowed
- No liability (not liable for damages)
- No warranty (provided as-is)

## Support & Contact

Questions or Issues?

1. Check Troubleshooting section
2. Review DEVELOPMENT.md for detailed guides
3. Check INSTALLATION.md for setup issues
4. Create GitHub issue with:
   - Error message
   - Steps to reproduce
   - System information
   - Screenshots

## Additional Resources

- Django Documentation: https://docs.djangoproject.com/
- MongoDB Manual: https://docs.mongodb.com/manual/
- Selenium Documentation: https://www.selenium.dev/documentation/
- PyTorch Tutorials: https://pytorch.org/tutorials/
- OpenCV Documentation: https://docs.opencv.org/

## Learning Path

For New Users:
1. Read this README
2. Follow Installation steps
3. Run application
4. Test with sample PDFs
5. Read DEVELOPMENT.md

For Developers:
1. Read DEVELOPMENT.md
2. Understand project architecture
3. Review API endpoints
4. Explore codebase
5. Make contributions

---

