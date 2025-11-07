# Smart Answer Sheet Processor - MongoDB Setup

This guide walks you through setting up the **MongoDB** database for the **Smart Answer Sheet Processor** Django application using the provided `setup_mongodb.py` script.

---

## `setup_mongodb.py`

> **Save this file in your project root directory** (same location as `manage.py`)

```python
""" MongoDB Database Setup Script for Smart Answer Sheet Processor
===============================================================
This script sets up MongoDB database with:
1. Three collections: student_credentials, subject_urls, pdf_uploads
2. Indexes for faster queries
3. Sample data for testing

Author: Smart Answer Sheet Processor Team
Date: November 2025
"""
import sys
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, CollectionInvalid, DuplicateKeyError
from datetime import datetime

# ==================== CONFIGURATION ====================
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "lms_automation"

COLLECTION_CREDENTIALS = "student_credentials"
COLLECTION_URLS = "subject_urls"
COLLECTION_UPLOADS = "pdf_uploads"

# ==================== HELPER FUNCTIONS ====================

def print_header():
    print("\n" + "=" * 70)
    print(" SMART ANSWER SHEET PROCESSOR - MONGODB SETUP")
    print("=" * 70 + "\n")


def print_success(message):
    print(f"✓ {message}")


def print_error(message):
    print(f"✗ ERROR: {message}", file=sys.stderr)


def print_warning(message):
    print(f"⚠ WARNING: {message}")


def print_section(section_num, total, title):
    print(f"\n[{section_num}/{total}] {title}")


def print_info(message):
    print(f"ℹ {message}")

# ==================== DATABASE OPERATIONS ====================

def connect_mongodb():
    try:
        print_info(f"Connecting to: {MONGODB_URI}")
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        return client
    except ConnectionFailure as e:
        print_error(f"Failed to connect to MongoDB: {e}")
        print()
        print("Please ensure MongoDB is running:")
        print(" → Windows: Services → MongoDB Server → Start")
        print(" → Linux: sudo systemctl start mongod")
        print(" → macOS: brew services start mongodb-community@7.0")
        print()
        print("To verify MongoDB is running:")
        print(" → Run: mongosh")
        sys.exit(1)


def create_collections(db):
    collections = [COLLECTION_CREDENTIALS, COLLECTION_URLS, COLLECTION_UPLOADS]
    created_count = existing_count = 0
    for name in collections:
        try:
            db.create_collection(name)
            print_success(f"Created collection: {name}")
            created_count += 1
        except CollectionInvalid:
            print_warning(f"Collection already exists: {name}")
            existing_count += 1
    return created_count, existing_count


def create_indexes(db):
    try:
        db[COLLECTION_CREDENTIALS].create_index([("register_number", ASCENDING)], unique=True, name="register_number_unique")
        print_success(f"Created unique index on {COLLECTION_CREDENTIALS}.register_number")

        db[COLLECTION_URLS].create_index([("subject_code", ASCENDING)], unique=True, name="subject_code_unique")
        print_success(f"Created unique index on {COLLECTION_URLS}.subject_code")

        db[COLLECTION_UPLOADS].create_index([("django_id", ASCENDING)], unique=True, sparse=True, name="django_id_unique")
        print_success(f"Created unique index on {COLLECTION_UPLOADS}.django_id")

        db[COLLECTION_UPLOADS].create_index([("register_number", ASCENDING)])
        db[COLLECTION_UPLOADS].create_index([("subject_code", ASCENDING)])
        db[COLLECTION_UPLOADS].create_index([("status", ASCENDING)])
        print_success("Created additional indexes for faster queries")
    except Exception as e:
        print_warning(f"Some indexes might already exist: {e}")


def insert_sample_credentials(db):
    sample_credentials = [
        {"register_number": "212221230038", "username": "22008681", "password": "student123", "created_at": datetime.now()},
        {"register_number": "212221230039", "username": "22008682", "password": "student123", "created_at": datetime.now()},
        {"register_number": "212221230040", "username": "22008683", "password": "student123", "created_at": datetime.now()},
        {"register_number": "212221230041", "username": "22008684", "password": "student123", "created_at": datetime.now()},
        {"register_number": "212221230042", "username": "22008685", "password": "student123", "created_at": datetime.now()},
        {"register_number": "212221230043", "username": "22008686", "password": "student123", "created_at": datetime.now()},
        {"register_number": "212221230044", "username": "22008687", "password": "student123", "created_at": datetime.now()},
        {"register_number": "212221230045", "username": "22008688", "password": "student123", "created_at": datetime.now()}
    ]
    try:
        deleted = db[COLLECTION_CREDENTIALS].delete_many({})
        if deleted.deleted_count > 0:
            print_info(f"Cleared {deleted.deleted_count} existing credentials")
        result = db[COLLECTION_CREDENTIALS].insert_many(sample_credentials)
        print_success(f"Inserted {len(result.inserted_ids)} student credentials")
        return len(result.inserted_ids)
    except DuplicateKeyError as e:
        print_error(f"Duplicate key error: {e}")
        return 0
    except Exception as e:
        print_error(f"Failed to insert credentials: {e}")
        return 0


def insert_sample_subject_urls(db):
    sample_urls = [
        {"subject_code": "19AI505", "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=1041", "subject_name": "Deep Learning", "created_at": datetime.now()},
        {"subject_code": "19AI407", "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=1042", "subject_name": "Machine Learning", "created_at": datetime.now()},
        {"subject_code": "19AI506", "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=1043", "subject_name": "Natural Language Processing", "created_at": datetime.now()},
        {"subject_code": "19CSE501", "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=2001", "subject_name": "Database Management Systems", "created_at": datetime.now()},
        {"subject_code": "19CSE502", "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=2002", "subject_name": "Computer Networks", "created_at": datetime.now()},
        {"subject_code": "19AI601", "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=3001", "subject_name": "Computer Vision", "created_at": datetime.now()},
        {"subject_code": "19AI602", "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=3002", "subject_name": "Reinforcement Learning", "created_at": datetime.now()},
        {"subject_code": "19CSE503", "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=2003", "subject_name": "Operating Systems", "created_at": datetime.now()}
    ]
    try:
        deleted = db[COLLECTION_URLS].delete_many({})
        if deleted.deleted_count > 0:
            print_info(f"Cleared {deleted.deleted_count} existing subject URLs")
        result = db[COLLECTION_URLS].insert_many(sample_urls)
        print_success(f"Inserted {len(result.inserted_ids)} subject URLs")
        return len(result.inserted_ids)
    except DuplicateKeyError as e:
        print_error(f"Duplicate key error: {e}")
        return 0
    except Exception as e:
        print_error(f"Failed to insert subject URLs: {e}")
        return 0


def verify_setup(db):
    print_info("Verifying database setup...")
    all_good = True
    collections = db.list_collection_names()
    required = [COLLECTION_CREDENTIALS, COLLECTION_URLS, COLLECTION_UPLOADS]
    for col in required:
        if col in collections:
            print_success(f"Collection exists: {col}")
        else:
            print_error(f"Collection missing: {col}")
            all_good = False

    cred_count = db[COLLECTION_CREDENTIALS].count_documents({})
    url_count = db[COLLECTION_URLS].count_documents({})
    print_success(f"Credentials count: {cred_count}") if cred_count > 0 else print_error("No credentials found!")
    print_success(f"Subject URLs count: {url_count}") if url_count > 0 else print_error("No subject URLs found!")

    cred_idx = list(db[COLLECTION_CREDENTIALS].list_indexes())
    url_idx = list(db[COLLECTION_URLS].list_indexes())
    print_success(f"Indexes on credentials: {len(cred_idx)}")
    print_success(f"Indexes on subject_urls: {len(url_idx)}")
    return all_good


def display_sample_data(db):
    print("\n" + "=" * 70)
    print(" SAMPLE DATA PREVIEW")
    print("=" * 70)

    cred = db[COLLECTION_CREDENTIALS].find_one()
    if cred:
        print("\n📋 Sample Student Credential:")
        print(f" Register Number: {cred.get('register_number')}")
        print(f" Username: {cred.get('username')}")
        print(f" Password: {cred.get('password')}")

    url = db[COLLECTION_URLS].find_one()
    if url:
        print("\n📚 Sample Subject URL:")
        print(f" Subject Code: {url.get('subject_code')}")
        print(f" Subject Name: {url.get('subject_name')}")
        print(f" LMS URL: {url.get('lms_url')[:60]}...")


def print_footer(db):
    cred_count = db[COLLECTION_CREDENTIALS].count_documents({})
    url_count = db[COLLECTION_URLS].count_documents({})
    print("\n" + "=" * 70)
    print(" ✓ MONGODB SETUP COMPLETED SUCCESSFULLY")
    print("=" * 70 + "\n")
    print("📊 Database Summary:")
    print(f" • Database: {DATABASE_NAME}")
    print(f" • Student Credentials: {cred_count} records")
    print(f" • Subject URLs: {url_count} records")
    print(f" • Collections: 3 created\n")
    print("📝 Next Steps:")
    print(" 1. Run Django migrations:\n    → python manage.py migrate\n")
    print(" 2. Create Django admin user:\n    → python manage.py createsuperuser\n")
    print(" 3. Start the development server:\n    → python manage.py runserver\n")
    print("🔍 To view data in MongoDB:")
    print(f" → mongosh {DATABASE_NAME}")
    print(f" → db.{COLLECTION_CREDENTIALS}.find().pretty()")
    print(f" → db.{COLLECTION_URLS}.find().pretty()\n")
    print("🌐 Access Application:\n → http://127.0.0.1:8000/")



def main():
    print_header()
    try:
        print_section(1, 6, "Connecting to MongoDB")
        client = connect_mongodb()
        db = client[DATABASE_NAME]
        print_success("Connected to MongoDB successfully")
        print_info(f"Using database: {DATABASE_NAME}")

        print_section(2, 6, "Creating Collections")
        created, existing = create_collections(db)
        print_info(f"Collections: {created} created, {existing} already existed")

        print_section(3, 6, "Creating Indexes")
        create_indexes(db)

        print_section(4, 6, "Inserting Sample Student Credentials")
        insert_sample_credentials(db)

        print_section(5, 6, "Inserting Sample Subject URLs")
        insert_sample_subject_urls(db)

        print_section(6, 6, "Verifying Setup")
        verify_setup(db) and print_success("All verification checks passed!") or print_warning("Some checks failed.")

        display_sample_data(db)
        print_footer(db)
        client.close()
        return 0
    except KeyboardInterrupt:
        print("\n✗ Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        import traceback; traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

## Run instructions

### Prerequisites

- MongoDB must be installed and running on the host where you run this script.
- Python 3.8+ with `pymongo` installed (see `requirements.txt` in the repo).

### Start MongoDB

Windows (PowerShell):

```powershell
# Start MongoDB service (if installed as a Windows Service)
Start-Service -Name "MongoDB"  # run as Administrator if needed

# Verify that mongosh can connect
mongosh
```

Linux (systemd):

```bash
sudo systemctl start mongod
sudo systemctl status mongod
mongosh
```

macOS (Homebrew):

```bash
brew services start mongodb-community@7.0
mongosh
```

### How to run the setup script

From your project root (same folder as `manage.py` and this file):

```powershell
python setup_mongodb.py
```

If `mongosh` connects successfully, the script will create the collections, indexes and insert the sample data. Use `mongosh` to inspect the data:

```javascript
use lms_automation
db.student_credentials.find().pretty()
db.subject_urls.find().pretty()
```

---

If you'd like, I can also add a small command in `requirements.txt` or a tiny README snippet showing how to install `pymongo` (`pip install -r requirements.txt`) — tell me if you want that.














































































































