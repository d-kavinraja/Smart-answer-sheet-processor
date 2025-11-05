from django.contrib import admin
from .models import PDFUpload

@admin.register(PDFUpload)
class PDFUploadAdmin(admin.ModelAdmin):
    list_display = ['filename', 'register_number', 'subject_code', 'status', 'is_uploaded', 'created_at']
    list_filter = ['status', 'is_uploaded', 'created_at']
    search_fields = ['filename', 'register_number', 'subject_code', 'username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('File Information', {
            'fields': ('filename', 'file', 'file_size', 'temp_pdf_path')
        }),
        ('Extracted Data', {
            'fields': ('register_number', 'subject_code', 'register_image', 'subject_image')
        }),
        ('Credentials', {
            'fields': ('username', 'password')
        }),
        ('Status', {
            'fields': ('status', 'is_uploaded', 'error_message')
        }),
        ('Database IDs', {
            'fields': ('mongodb_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
