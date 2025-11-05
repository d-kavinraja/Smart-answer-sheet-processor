# lms_project/urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from pdf_processor import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('api/upload/', views.upload_pdfs, name='upload_pdfs'),
    path('api/process/<int:pdf_id>/', views.process_pdf, name='process_pdf'),
    path('api/recheck/<int:pdf_id>/', views.recheck_configuration, name='recheck_configuration'),  # NEW
    path('api/upload-lms/<int:pdf_id>/', views.upload_to_lms, name='upload_to_lms'),
    path('api/upload-multiple-lms/', views.upload_multiple_to_lms, name='upload_multiple_lms'),
    path('api/delete/<int:pdf_id>/', views.delete_upload, name='delete_upload'),
    path('api/status/<int:pdf_id>/', views.get_upload_status, name='get_upload_status'),
    path('api/uploads/', views.get_all_uploads, name='get_all_uploads'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
