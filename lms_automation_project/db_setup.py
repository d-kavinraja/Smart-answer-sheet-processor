"""
MongoDB Database Setup Script for Smart Answer Sheet Processor
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

# MongoDB Configuration
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "lms_automation"

# Collection Names (matching your application)
COLLECTION_CREDENTIALS = "credentials"
COLLECTION_URLS = "subject_code_urls"
COLLECTION_UPLOADS = "uploaded_files"

# ==================== HELPER FUNCTIONS ====================

def print_header():
    """Print setup header"""
    print("\n" + "=" * 70)
    print("  SMART ANSWER SHEET PROCESSOR - MONGODB SETUP")
    print("=" * 70)
    print()

def print_success(message):
    """Print success message"""
    print(f"✓ {message}")

def print_error(message):
    """Print error message"""
    print(f"✗ ERROR: {message}", file=sys.stderr)

def print_warning(message):
    """Print warning message"""
    print(f"⚠ WARNING: {message}")

def print_section(section_num, total, title):
    """Print section header"""
    print(f"\n[{section_num}/{total}] {title}")

def print_info(message):
    """Print info message"""
    print(f"ℹ {message}")

# ==================== DATABASE OPERATIONS ====================

def connect_mongodb():
    """Connect to MongoDB server"""
    try:
        print_info(f"Connecting to: {MONGODB_URI}")
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.server_info()
        return client
    
    except ConnectionFailure as e:
        print_error(f"Failed to connect to MongoDB: {e}")
        print()
        print("Please ensure MongoDB is running:")
        print("  → Windows: Services → MongoDB Server → Start")
        print("  → Linux: sudo systemctl start mongod")
        print("  → macOS: brew services start mongodb-community@7.0")
        print()
        print("To verify MongoDB is running:")
        print("  → Run: mongosh")
        sys.exit(1)

def create_collections(db):
    """Create required collections"""
    collections = [
        COLLECTION_CREDENTIALS,
        COLLECTION_URLS,
        COLLECTION_UPLOADS
    ]
    
    created_count = 0
    existing_count = 0
    
    for collection_name in collections:
        try:
            db.create_collection(collection_name)
            print_success(f"Created collection: {collection_name}")
            created_count += 1
        except CollectionInvalid:
            print_warning(f"Collection already exists: {collection_name}")
            existing_count += 1
    
    return created_count, existing_count

def create_indexes(db):
    """Create indexes for better query performance"""
    try:
        # Index on register_number (unique)
        db[COLLECTION_CREDENTIALS].create_index(
            [("register_number", ASCENDING)],
            unique=True,
            name="register_number_unique"
        )
        print_success(f"Created unique index on {COLLECTION_CREDENTIALS}.register_number")
        
        # Index on subject_code (unique)
        db[COLLECTION_URLS].create_index(
            [("subject_code", ASCENDING)],
            unique=True,
            name="subject_code_unique"
        )
        print_success(f"Created unique index on {COLLECTION_URLS}.subject_code")
        
        # Index on django_id (unique) for pdf_uploads
        db[COLLECTION_UPLOADS].create_index(
            [("django_id", ASCENDING)],
            unique=True,
            sparse=True,  # Allow documents without django_id
            name="django_id_unique"
        )
        print_success(f"Created unique index on {COLLECTION_UPLOADS}.django_id")
        
        # Additional indexes for common queries
        db[COLLECTION_UPLOADS].create_index([("register_number", ASCENDING)])
        db[COLLECTION_UPLOADS].create_index([("subject_code", ASCENDING)])
        db[COLLECTION_UPLOADS].create_index([("status", ASCENDING)])
        
        print_success("Created additional indexes for faster queries")
        
    except Exception as e:
        print_warning(f"Some indexes might already exist: {e}")

def insert_sample_credentials(db):
    """Insert sample student credentials"""
    sample_credentials = [
        {
            "register_number": "212221230038",
            "username": "22008681",
            "password": "student123",
            "created_at": datetime.now()
        },
        {
            "register_number": "212221230039",
            "username": "22008682",
            "password": "student123",
            "created_at": datetime.now()
        },
        {
            "register_number": "212221230040",
            "username": "22008683",
            "password": "student123",
            "created_at": datetime.now()
        },
        {
            "register_number": "212221230041",
            "username": "22008684",
            "password": "student123",
            "created_at": datetime.now()
        },
        {
            "register_number": "212221230042",
            "username": "22008685",
            "password": "student123",
            "created_at": datetime.now()
        },
        {
            "register_number": "212221230043",
            "username": "22008686",
            "password": "student123",
            "created_at": datetime.now()
        },
        {
            "register_number": "212221230044",
            "username": "22008687",
            "password": "student123",
            "created_at": datetime.now()
        },
        {
            "register_number": "212221230045",
            "username": "22008688",
            "password": "student123",
            "created_at": datetime.now()
        }
    ]
    
    try:
        # Clear existing data
        deleted = db[COLLECTION_CREDENTIALS].delete_many({})
        if deleted.deleted_count > 0:
            print_info(f"Cleared {deleted.deleted_count} existing credentials")
        
        # Insert new data
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
    """Insert sample subject URLs"""
    sample_urls = [
        {
            "subject_code": "19AI505",
            "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=1041",
            "subject_name": "Deep Learning",
            "created_at": datetime.now()
        },
        {
            "subject_code": "19AI407",
            "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=1042",
            "subject_name": "Machine Learning",
            "created_at": datetime.now()
        },
        {
            "subject_code": "19AI506",
            "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=1043",
            "subject_name": "Natural Language Processing",
            "created_at": datetime.now()
        },
        {
            "subject_code": "19CSE501",
            "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=2001",
            "subject_name": "Database Management Systems",
            "created_at": datetime.now()
        },
        {
            "subject_code": "19CSE502",
            "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=2002",
            "subject_name": "Computer Networks",
            "created_at": datetime.now()
        },
        {
            "subject_code": "19AI601",
            "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=3001",
            "subject_name": "Computer Vision",
            "created_at": datetime.now()
        },
        {
            "subject_code": "19AI602",
            "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=3002",
            "subject_name": "Reinforcement Learning",
            "created_at": datetime.now()
        },
        {
            "subject_code": "19CSE503",
            "lms_url": "https://lms2.ai.saveetha.in/mod/assign/view.php?id=2003",
            "subject_name": "Operating Systems",
            "created_at": datetime.now()
        }
    ]
    
    try:
        # Clear existing data
        deleted = db[COLLECTION_URLS].delete_many({})
        if deleted.deleted_count > 0:
            print_info(f"Cleared {deleted.deleted_count} existing subject URLs")
        
        # Insert new data
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
    """Verify database setup"""
    print_info("Verifying database setup...")
    
    all_good = True
    
    # Check collections exist
    collections = db.list_collection_names()
    required_collections = [COLLECTION_CREDENTIALS, COLLECTION_URLS, COLLECTION_UPLOADS]
    
    for collection in required_collections:
        if collection in collections:
            print_success(f"Collection exists: {collection}")
        else:
            print_error(f"Collection missing: {collection}")
            all_good = False
    
    # Check credentials count
    credentials_count = db[COLLECTION_CREDENTIALS].count_documents({})
    if credentials_count > 0:
        print_success(f"Credentials count: {credentials_count}")
    else:
        print_error("No credentials found!")
        all_good = False
    
    # Check subject URLs count
    urls_count = db[COLLECTION_URLS].count_documents({})
    if urls_count > 0:
        print_success(f"Subject URLs count: {urls_count}")
    else:
        print_error("No subject URLs found!")
        all_good = False
    
    # Check indexes
    credentials_indexes = list(db[COLLECTION_CREDENTIALS].list_indexes())
    urls_indexes = list(db[COLLECTION_URLS].list_indexes())
    
    print_success(f"Indexes on credentials: {len(credentials_indexes)}")
    print_success(f"Indexes on subject_urls: {len(urls_indexes)}")
    
    return all_good

def display_sample_data(db):
    """Display sample data from collections"""
    print("\n" + "=" * 70)
    print("  SAMPLE DATA PREVIEW")
    print("=" * 70)
    
    # Sample credential
    print("\n📋 Sample Student Credential:")
    sample_cred = db[COLLECTION_CREDENTIALS].find_one()
    if sample_cred:
        print(f"  Register Number: {sample_cred.get('register_number')}")
        print(f"  Username: {sample_cred.get('username')}")
        print(f"  Password: {sample_cred.get('password')}")
    
    # Sample subject URL
    print("\n📚 Sample Subject URL:")
    sample_url = db[COLLECTION_URLS].find_one()
    if sample_url:
        print(f"  Subject Code: {sample_url.get('subject_code')}")
        print(f"  Subject Name: {sample_url.get('subject_name')}")
        print(f"  LMS URL: {sample_url.get('lms_url')[:60]}...")

def print_footer(db):
    """Print completion message"""
    credentials_count = db[COLLECTION_CREDENTIALS].count_documents({})
    urls_count = db[COLLECTION_URLS].count_documents({})
    
    print("\n" + "=" * 70)
    print("  ✓ MONGODB SETUP COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("📊 Database Summary:")
    print(f"  • Database: {DATABASE_NAME}")
    print(f"  • Student Credentials: {credentials_count} records")
    print(f"  • Subject URLs: {urls_count} records")
    print(f"  • Collections: 3 created")
    print()
    print("📝 Next Steps:")
    print("  1. Run Django migrations:")
    print("     → python manage.py migrate")
    print()
    print("  2. Create Django admin user:")
    print("     → python manage.py createsuperuser")
    print()
    print("  3. Start the development server:")
    print("     → python manage.py runserver")
    print()
    print("🔍 To view data in MongoDB:")
    print(f"  → mongosh {DATABASE_NAME}")
    print(f"  → db.{COLLECTION_CREDENTIALS}.find().pretty()")
    print(f"  → db.{COLLECTION_URLS}.find().pretty()")
    print()
    print("🌐 Access Application:")
    print("  → http://127.0.0.1:8000/")
    print()

# ==================== MAIN FUNCTION ====================

def main():
    """Main setup function"""
    print_header()
    
    try:
        # Step 1: Connect to MongoDB
        print_section(1, 6, "Connecting to MongoDB")
        client = connect_mongodb()
        db = client[DATABASE_NAME]
        print_success("Connected to MongoDB successfully")
        print_info(f"Using database: {DATABASE_NAME}")
        
        # Step 2: Create collections
        print_section(2, 6, "Creating Collections")
        created, existing = create_collections(db)
        print_info(f"Collections: {created} created, {existing} already existed")
        
        # Step 3: Create indexes
        print_section(3, 6, "Creating Indexes")
        create_indexes(db)
        
        # Step 4: Insert sample credentials
        print_section(4, 6, "Inserting Sample Student Credentials")
        cred_count = insert_sample_credentials(db)
        
        # Step 5: Insert sample subject URLs
        print_section(5, 6, "Inserting Sample Subject URLs")
        url_count = insert_sample_subject_urls(db)
        
        # Step 6: Verify setup
        print_section(6, 6, "Verifying Setup")
        if verify_setup(db):
            print_success("All verification checks passed!")
        else:
            print_warning("Some verification checks failed. Please review.")
        
        # Display sample data
        display_sample_data(db)
        
        # Print completion message
        print_footer(db)
        
        # Close connection
        client.close()
        
        return 0
    
    except KeyboardInterrupt:
        print()
        print_error("Setup interrupted by user")
        return 1
    
    except Exception as e:
        print()
        print_error(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
