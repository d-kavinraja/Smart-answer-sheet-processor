from django.db import models
from django.utils import timezone

class PDFUpload(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('extracted', 'Extracted'),
        ('uploading', 'Uploading'),
        ('uploaded', 'Uploaded'),
        ('failed', 'Failed'),
    ]
    
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/')
    file_size = models.IntegerField(default=0)
    
    register_number = models.CharField(max_length=20, blank=True, null=True)
    subject_code = models.CharField(max_length=20, blank=True, null=True)
    
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    
    temp_pdf_path = models.CharField(max_length=500, blank=True, null=True)
    register_image = models.ImageField(upload_to='cropped/register/', blank=True, null=True)
    subject_image = models.ImageField(upload_to='cropped/subject/', blank=True, null=True)
    
    mongodb_id = models.CharField(max_length=100, blank=True, null=True)
    
    is_uploaded = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} - {self.status}"
    
    def mark_as_processing(self):
        self.status = 'processing'
        self.save()
    
    def mark_as_uploading(self):
        self.status = 'uploading'
        self.save()
    
    def mark_as_uploaded(self):
        self.status = 'uploaded'
        self.is_uploaded = True
        self.error_message = None
        self.save()
    
    def mark_as_failed(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        self.save()
    
    def has_subject_url(self):
        """Check if subject URL is configured in database"""
        if not self.subject_code:
            return False
        
        try:
            from pymongo import MongoClient
            client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
            db = client['lms_automation']
            subject_code_urls_collection = db['subject_code_urls']
            url_doc = subject_code_urls_collection.find_one({'subject_code': self.subject_code})
            return bool(url_doc and url_doc.get('url'))
        except:
            return False
    
    def has_credentials(self):
        """Check if user has credentials"""
        return bool(self.username and self.password)
    
    def get_missing_requirements(self):
        """Get list of missing requirements for upload"""
        missing = []
        if not self.has_credentials():
            missing.append('credentials')
        if not self.has_subject_url():
            missing.append('subject_url')
        return missing
