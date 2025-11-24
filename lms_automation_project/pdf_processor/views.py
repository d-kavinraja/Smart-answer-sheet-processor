import os
import json
import subprocess
import tempfile
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files import File
from pymongo import MongoClient
from bson import ObjectId
from .models import PDFUpload
import traceback
from concurrent.futures import ThreadPoolExecutor

upload_executor = ThreadPoolExecutor(max_workers=5)

def get_mongodb_connection():
    """Get MongoDB connection"""
    try:
        uri = getattr(settings, 'MONGODB_URI', 'mongodb://localhost:27017/')
        db_name = getattr(settings, 'MONGODB_NAME', 'lms_automation')
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # ping to raise an exception early if server is unreachable
        client.admin.command('ping')
        db = client[db_name]
        return db
    except Exception as e:
        print(f"Database connection error ({uri}): {e}")
        return None

def index(request):
    """Main page view"""
    status_filter = request.GET.get('status', 'all')
    
    if status_filter == 'pending':
        uploads = PDFUpload.objects.filter(is_uploaded=False).order_by('-created_at')
    elif status_filter == 'uploaded':
        uploads = PDFUpload.objects.filter(is_uploaded=True).order_by('-created_at')
    else:
        uploads = PDFUpload.objects.all().order_by('-created_at')
    
    total_count = PDFUpload.objects.count()
    pending_count = PDFUpload.objects.filter(is_uploaded=False).count()
    uploaded_count = PDFUpload.objects.filter(is_uploaded=True).count()
    
    return render(request, 'pdf_processor/index.html', {
        'uploads': uploads,
        'status_filter': status_filter,
        'total_count': total_count,
        'pending_count': pending_count,
        'uploaded_count': uploaded_count
    })

@csrf_exempt
@require_http_methods(["POST"])
def upload_pdfs(request):
    """Handle PDF uploads"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
        
    try:
        files = request.FILES.getlist('pdf_files')
        if not files:
            return JsonResponse({'success': False, 'error': 'No files uploaded'})

        db = get_mongodb_connection()
        if db is None:
            return JsonResponse({'success': False, 'error': 'System database unavailable'})
        
        uploaded_files_collection = db['uploaded_files']
        uploaded_files = []

        for file in files:
            if not file.name.lower().endswith('.pdf'):
                continue

            pdf_upload = PDFUpload.objects.create(
                filename=file.name,
                file_size=file.size,
                status='pending',
                is_uploaded=False
            )

            file_path = default_storage.save(
                f'uploads/{pdf_upload.id}_{file.name}',
                ContentFile(file.read())
            )

            pdf_upload.file = file_path
            pdf_upload.temp_pdf_path = pdf_upload.file.path
            pdf_upload.save()

            mongo_doc = {
                'filename': file.name,
                'registerNumber': '',
                'subjectCode': '',
                'pdfPath': pdf_upload.file.path,
                'status': 'Pending',
                'uploaded': False,
                'django_id': pdf_upload.id,
                'created_at': pdf_upload.created_at.isoformat()
            }
            
            result = uploaded_files_collection.insert_one(mongo_doc)
            pdf_upload.mongodb_id = str(result.inserted_id)
            pdf_upload.save()

            uploaded_files.append({
                'id': pdf_upload.id,
                'filename': pdf_upload.filename,
                'status': pdf_upload.status
            })

        return JsonResponse({
            'success': True,
            'files': uploaded_files,
            'message': f'{len(uploaded_files)} files uploaded successfully'
        })

    except Exception as e:
        print(f"Upload error: {str(e)}")  # Log for debugging
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': 'Upload failed. Please try again.'})

@csrf_exempt
@require_http_methods(["POST"])
def process_pdf(request, pdf_id):
    """Process PDF to extract information"""
    try:
        pdf_upload = get_object_or_404(PDFUpload, id=pdf_id)
        pdf_upload.mark_as_processing()

        file_path = pdf_upload.file.path
        ml_service_path = os.path.join(settings.BASE_DIR, 'services', 'ml_service.py')
        
        result = subprocess.run(
            ['python', ml_service_path, file_path],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )

        output = result.stdout

        try:
            json_start = output.find('{')
            json_end = output.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = output[json_start:json_end]
                ml_result = json.loads(json_str)
            else:
                raise ValueError("No JSON found")
        except Exception as e:
            pdf_upload.mark_as_failed('Unable to extract data from PDF')
            return JsonResponse({'success': False, 'error': 'Unable to extract data from PDF'})

        if ml_result.get('success'):
            data = ml_result.get('data', {})
            register_number = data.get('registerNumber')
            subject_code = data.get('subjectCode')
            temp_pdf_path = data.get('persistentPdfPath')
            register_image_path = data.get('registerImagePath')
            subject_image_path = data.get('subjectImagePath')

            pdf_upload.register_number = register_number
            pdf_upload.subject_code = subject_code
            pdf_upload.temp_pdf_path = temp_pdf_path
            
            if register_image_path and os.path.exists(register_image_path):
                with open(register_image_path, 'rb') as f:
                    pdf_upload.register_image.save(f'register_{pdf_upload.id}.jpg', File(f), save=False)
            
            if subject_image_path and os.path.exists(subject_image_path):
                with open(subject_image_path, 'rb') as f:
                    pdf_upload.subject_image.save(f'subject_{pdf_upload.id}.jpg', File(f), save=False)
            
            pdf_upload.status = 'extracted'
            pdf_upload.save()

            db = get_mongodb_connection()
            if db is not None:
                try:
                    credentials_collection = db['credentials']
                    credentials = credentials_collection.find_one({'registerNumber': register_number})

                    if credentials:
                        pdf_upload.username = credentials.get('username')
                        pdf_upload.password = credentials.get('password')
                        pdf_upload.save()
                except Exception as e:
                    print(f"Error fetching credentials: {e}")

            if pdf_upload.mongodb_id and db is not None:
                try:
                    uploaded_files_collection = db['uploaded_files']
                    uploaded_files_collection.update_one(
                        {'_id': ObjectId(pdf_upload.mongodb_id)},
                        {'$set': {
                            'registerNumber': register_number,
                            'subjectCode': subject_code,
                            'status': 'Extracted',
                            'pdfPath': temp_pdf_path
                        }}
                    )
                except:
                    pass

            return JsonResponse({
                'success': True,
                'data': {
                    'id': pdf_upload.id,
                    'filename': pdf_upload.filename,
                    'registerNumber': register_number,
                    'subjectCode': subject_code,
                    'username': pdf_upload.username,
                    'status': pdf_upload.status,
                    'hasCredentials': pdf_upload.has_credentials(),
                    'subjectUrlConfigured': pdf_upload.has_subject_url(),
                    'missingRequirements': pdf_upload.get_missing_requirements()
                }
            })
        else:
            error_msg = ml_result.get('error', 'Extraction failed')
            pdf_upload.mark_as_failed(error_msg)
            return JsonResponse({'success': False, 'error': error_msg})

    except subprocess.TimeoutExpired:
        pdf_upload.mark_as_failed('Processing timeout')
        return JsonResponse({'success': False, 'error': 'Processing timeout'})
    except Exception as e:
        pdf_upload.mark_as_failed('Processing error')
        return JsonResponse({'success': False, 'error': 'Processing error occurred'})

@csrf_exempt
@require_http_methods(["POST"])
def upload_to_lms(request, pdf_id):
    """Upload single PDF to LMS with comprehensive error checking"""
    try:
        pdf_upload = get_object_or_404(PDFUpload, id=pdf_id)

        # Idempotency Check: If already uploaded, return success immediately.
        if pdf_upload.is_uploaded:
            return JsonResponse({'success': True, 'message': 'Already uploaded', 'status': 'uploaded'})
        
        if pdf_upload.status == 'uploading':
            return JsonResponse({'success': False, 'error': 'An upload for this file is already in progress.', 'error_type': 'already_in_progress'})

        # Check credentials
        if not pdf_upload.has_credentials():
            return JsonResponse({
                'success': False,
                'error': f'LMS credentials not found for register number {pdf_upload.register_number}. Please contact administrator.',
                'error_type': 'credentials_missing'
            })

        # Check subject code
        if not pdf_upload.subject_code:
            return JsonResponse({
                'success': False,
                'error': 'Subject code not extracted',
                'error_type': 'subject_code_missing'
            })

        # Check PDF file
        if not pdf_upload.temp_pdf_path or not os.path.exists(pdf_upload.temp_pdf_path):
            return JsonResponse({
                'success': False,
                'error': 'PDF file not found',
                'error_type': 'file_missing'
            })

        # Check subject URL configuration
        if not pdf_upload.has_subject_url():
            return JsonResponse({
                'success': False,
                'error': f'Subject {pdf_upload.subject_code} URL not configured in system. Please contact administrator.',
                'error_type': 'subject_url_not_configured'
            })

        pdf_upload.mark_as_uploading()

        # Fetch submission URL
        db = get_mongodb_connection()
        submission_url = None
        
        if db is not None:
            try:
                subject_code_urls_collection = db['subject_code_urls']
                url_doc = subject_code_urls_collection.find_one({'subject_code': pdf_upload.subject_code})
                if url_doc:
                    submission_url = url_doc.get('url')
            except Exception as e:
                print(f"Error fetching URL: {e}")

        lms_automation_path = os.path.join(settings.BASE_DIR, 'services', 'lms_automation.py')
        
        cmd = ['python', lms_automation_path, pdf_upload.username, pdf_upload.password,
               pdf_upload.subject_code, pdf_upload.temp_pdf_path]
        
        if submission_url:
            cmd.append(submission_url)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, encoding='utf-8', errors='replace')

        output = result.stdout

        try:
            json_start = output.find("JSON_START")
            json_end = output.find("JSON_END")

            if json_start >= 0 and json_end > json_start:
                json_str = output[json_start + 10:json_end].strip()
                lms_result = json.loads(json_str)
            else:
                raise ValueError("No JSON found")
        except Exception as e:
            pdf_upload.mark_as_failed('LMS communication failed')
            return JsonResponse({'success': False, 'error': 'LMS communication failed', 'error_type': 'lms_error'})

        upload_result = lms_result.get('upload', {})

        if upload_result.get('success'):
            pdf_upload.mark_as_uploaded()

            if db is not None and pdf_upload.mongodb_id:
                try:
                    uploaded_files_collection = db['uploaded_files']
                    uploaded_files_collection.update_one(
                        {'_id': ObjectId(pdf_upload.mongodb_id)},
                        {'$set': {'status': 'Uploaded', 'uploaded': True}}
                    )
                except:
                    pass

            try:
                if pdf_upload.temp_pdf_path and os.path.exists(pdf_upload.temp_pdf_path):
                    os.remove(pdf_upload.temp_pdf_path)
            except:
                pass

            return JsonResponse({'success': True, 'message': 'Upload successful', 'status': 'uploaded'})
        else:
            error_msg = upload_result.get('message', 'Upload failed')
            pdf_upload.mark_as_failed(error_msg)
            return JsonResponse({'success': False, 'error': error_msg, 'error_type': 'upload_failed'})

    except subprocess.TimeoutExpired:
        pdf_upload.mark_as_failed('Upload timeout')
        return JsonResponse({'success': False, 'error': 'Upload timeout', 'error_type': 'timeout'})
    except Exception as e:
        pdf_upload.mark_as_failed('Upload error')
        return JsonResponse({'success': False, 'error': 'Upload error occurred', 'error_type': 'unknown'})
@csrf_exempt
@require_http_methods(["POST"])
def upload_multiple_to_lms(request):
    """Upload multiple PDFs in parallel"""
    try:
        data = json.loads(request.body)
        pdf_ids = data.get('pdf_ids', [])
        
        if not pdf_ids:
            return JsonResponse({'success': False, 'error': 'No PDFs selected'})
        
        uploads = []
        errors = []
        
        for pdf_id in pdf_ids:
            try:
                pdf_upload = PDFUpload.objects.get(id=pdf_id)
                
                if not pdf_upload.has_credentials():
                    errors.append(f"{pdf_upload.filename}: Credentials not found")
                    continue
                
                if not pdf_upload.subject_code:
                    errors.append(f"{pdf_upload.filename}: Subject code not found")
                    continue
                
                if not pdf_upload.temp_pdf_path or not os.path.exists(pdf_upload.temp_pdf_path):
                    errors.append(f"{pdf_upload.filename}: PDF file not found")
                    continue
                
                if not pdf_upload.has_subject_url():
                    errors.append(f"{pdf_upload.filename}: Subject {pdf_upload.subject_code} URL not configured")
                    continue
                
                pdf_upload.mark_as_uploading()
                
                submission_url = None
                db = get_mongodb_connection()
                if db is not None:
                    try:
                        subject_code_urls_collection = db['subject_code_urls']
                        url_doc = subject_code_urls_collection.find_one({'subject_code': pdf_upload.subject_code})
                        if url_doc:
                            submission_url = url_doc.get('url')
                    except:
                        pass
                
                uploads.append({
                    'id': pdf_upload.id,
                    'username': pdf_upload.username,
                    'password': pdf_upload.password,
                    'subject_code': pdf_upload.subject_code,
                    'pdf_path': pdf_upload.temp_pdf_path,
                    'submission_url': submission_url or ''
                })
                
            except PDFUpload.DoesNotExist:
                errors.append(f"PDF ID {pdf_id}: Not found")
        
        if not uploads:
            return JsonResponse({'success': False, 'error': 'No valid PDFs', 'errors': errors})
        
        def background_parallel_upload():
            parallel_lms_uploader_path = os.path.join(settings.BASE_DIR, 'services', 'parallel_lms_uploader.py')
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(uploads, f)
                temp_json_path = f.name
            
            try:
                result = subprocess.run(
                    ['python', parallel_lms_uploader_path, temp_json_path],
                    capture_output=True,
                    text=True,
                    timeout=3600,
                    encoding='utf-8',
                    errors='replace'
                )
                
                output = result.stdout
                
                try:
                    json_start = output.find("JSON_START")
                    json_end = output.find("JSON_END")
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = output[json_start + 10:json_end].strip()
                        results = json.loads(json_str)
                        
                        db = get_mongodb_connection()
                        for upload_id, result_data in results.items():
                            try:
                                pdf_upload = PDFUpload.objects.get(id=int(upload_id))
                                
                                if result_data['success']:
                                    pdf_upload.mark_as_uploaded()
                                    
                                    if db is not None and pdf_upload.mongodb_id:
                                        try:
                                            uploaded_files_collection = db['uploaded_files']
                                            uploaded_files_collection.update_one(
                                                {'_id': ObjectId(pdf_upload.mongodb_id)},
                                                {'$set': {'status': 'Uploaded', 'uploaded': True}}
                                            )
                                        except:
                                            pass
                                    
                                    try:
                                        if pdf_upload.temp_pdf_path and os.path.exists(pdf_upload.temp_pdf_path):
                                            os.remove(pdf_upload.temp_pdf_path)
                                    except:
                                        pass
                                else:
                                    error_msg = result_data.get('result', {}).get('error', 'Upload failed')
                                    pdf_upload.mark_as_failed(error_msg)
                                
                            except PDFUpload.DoesNotExist:
                                pass
                        
                except Exception as e:
                    print(f"Error parsing results: {e}")
                
            finally:
                try:
                    os.remove(temp_json_path)
                except:
                    pass
        
        upload_executor.submit(background_parallel_upload)
        
        return JsonResponse({
            'success': True,
            'message': f'Started parallel upload for {len(uploads)} documents',
            'count': len(uploads),
            'errors': errors if errors else None
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Parallel upload failed'})

@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def delete_upload(request, pdf_id):
    """Delete PDF upload"""
    try:
        pdf_upload = get_object_or_404(PDFUpload, id=pdf_id)

        db = get_mongodb_connection()
        if db is not None and pdf_upload.mongodb_id:
            try:
                uploaded_files_collection = db['uploaded_files']
                uploaded_files_collection.delete_one({'_id': ObjectId(pdf_upload.mongodb_id)})
            except:
                pass

        for file_field in [pdf_upload.file, pdf_upload.register_image, pdf_upload.subject_image]:
            if file_field:
                try:
                    if os.path.exists(file_field.path):
                        os.remove(file_field.path)
                    default_storage.delete(file_field.name)
                except:
                    pass

        if pdf_upload.temp_pdf_path and os.path.exists(pdf_upload.temp_pdf_path):
            try:
                os.remove(pdf_upload.temp_pdf_path)
            except:
                pass

        pdf_upload.delete()
        return JsonResponse({'success': True, 'message': 'Document deleted'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Delete failed'})

@csrf_exempt
def get_upload_status(request, pdf_id):
    """Get upload status"""
    try:
        pdf_upload = get_object_or_404(PDFUpload, id=pdf_id)
        has_credentials = pdf_upload.has_credentials()
        subject_url_configured = pdf_upload.has_subject_url()
        missing_requirements = []
        if not has_credentials:
            missing_requirements.append('credentials')
        if not subject_url_configured:
            missing_requirements.append('subject_url')

        register_image_url = pdf_upload.register_image.url if pdf_upload.register_image else None
        subject_image_url = pdf_upload.subject_image.url if pdf_upload.subject_image else None
        return JsonResponse({
            'success': True,
            'data': {
                'id': pdf_upload.id,
                'filename': pdf_upload.filename,
                'status': pdf_upload.status,
                'registerNumber': pdf_upload.register_number,
                'subjectCode': pdf_upload.subject_code,
                'username': pdf_upload.username,
                'errorMessage': pdf_upload.error_message,
                'isUploaded': pdf_upload.is_uploaded,
                'hasCredentials': has_credentials,
                'subjectUrlConfigured': subject_url_configured,
                'missingRequirements': missing_requirements,
                'registerImageUrl': register_image_url,
                'subjectImageUrl': subject_image_url,
                'createdAt': pdf_upload.created_at.isoformat(),
                'updatedAt': pdf_upload.updated_at.isoformat(),
                'statusDisplay': pdf_upload.get_status_display(),
                'fileSize': pdf_upload.file_size
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Status unavailable'})



@csrf_exempt
def get_all_uploads(request):
    """Get all uploads"""
    try:
        status_filter = request.GET.get('status', 'all')
        
        if status_filter == 'pending':
            uploads = PDFUpload.objects.filter(is_uploaded=False).order_by('-created_at')
        elif status_filter == 'uploaded':
            uploads = PDFUpload.objects.filter(is_uploaded=True).order_by('-created_at')
        else:
            uploads = PDFUpload.objects.all().order_by('-created_at')
        
        uploads_list = [{
            'id': u.id,
            'filename': u.filename,
            'status': u.status,
            'registerNumber': u.register_number,
            'subjectCode': u.subject_code,
            'isUploaded': u.is_uploaded
        } for u in uploads]
        
        return JsonResponse({'success': True, 'uploads': uploads_list, 'count': len(uploads_list)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Could not retrieve uploads'})

@csrf_exempt
@require_http_methods(["POST"])
def recheck_configuration(request, pdf_id):
    """Recheck credentials and subject URL configuration with detailed feedback"""
    try:
        pdf_upload = get_object_or_404(PDFUpload, id=pdf_id)
        
        if not pdf_upload.register_number or not pdf_upload.subject_code:
            return JsonResponse({
                'success': False,
                'error': 'Data not extracted yet. Please extract data first.'
            })
        
        db = get_mongodb_connection()
        
        if db is None:
            return JsonResponse({
                'success': False,
                'error': 'Database connection failed'
            })
        
        credentials_found = False
        subject_url_found = False
        username = None
        
        try:
            # Check credentials in MongoDB
            credentials_collection = db['credentials']
            credentials = credentials_collection.find_one({'registerNumber': pdf_upload.register_number})
            
            if credentials:
                username = credentials.get('username')
                password = credentials.get('password')
                
                if username and password:
                    pdf_upload.username = username
                    pdf_upload.password = password
                    credentials_found = True
                else:
                    # Clear credentials if incomplete
                    pdf_upload.username = None
                    pdf_upload.password = None
                    credentials_found = False
            else:
                # Clear credentials if not found in MongoDB
                pdf_upload.username = None
                pdf_upload.password = None
                credentials_found = False
            
            # Always save to update the database
            pdf_upload.save()
            
            # Check subject URL
            subject_code_urls_collection = db['subject_code_urls']
            url_doc = subject_code_urls_collection.find_one({'subjectcode': pdf_upload.subject_code})
            subject_url_found = bool(url_doc and url_doc.get('url'))
            
        except Exception as e:
            print(f"Error during recheck: {e}")
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': 'Error checking configuration'
            })
        
        # Build detailed response message
        if credentials_found and subject_url_found:
            message = f'✓ Configuration complete! Both LMS credentials and subject URL found.'
            message_type = 'success'
        elif not credentials_found and not subject_url_found:
            message = f'✗ Both missing: LMS credentials for register {pdf_upload.register_number} AND subject URL for {pdf_upload.subject_code} not found in system.'
            message_type = 'error'
        elif not credentials_found:
            message = f'⚠ LMS credentials for register number {pdf_upload.register_number} not found in system.'
            message_type = 'warning'
        elif not subject_url_found:
            message = f'⚠ Subject URL for {pdf_upload.subject_code} not configured in system.'
            message_type = 'warning'
        else:
            message = 'Unknown status'
            message_type = 'info'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'messageType': message_type,
            'data': {
                'hasCredentials': credentials_found,
                'subjectUrlConfigured': subject_url_found,
                'username': username if credentials_found else None,
                'registerNumber': pdf_upload.register_number,
                'subjectCode': pdf_upload.subject_code,
                'missingRequirements': pdf_upload.get_missing_requirements()
            }
        })
        
    except Exception as e:
        print(f"Recheck error: {e}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'Recheck failed. Please try again.'
        })
    except Exception as e:
        print(f"Recheck error: {e}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'Recheck failed. Please try again.'
        })
