"""
Parallel LMS Upload Service
Handles simultaneous uploads using multiple Chrome instances
"""

import os
import sys
import json
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import subprocess

log_lock = Lock()

def safe_print(message):
    """Thread-safe printing"""
    with log_lock:
        print(message, file=sys.stderr)

def upload_single_pdf(upload_data):
    """Upload a single PDF using subprocess"""
    upload_id = upload_data['id']
    username = upload_data['username']
    password = upload_data['password']
    subject_code = upload_data['subject_code']
    pdf_path = upload_data['pdf_path']
    submission_url = upload_data.get('submission_url', '')
    
    try:
        safe_print(f"\n{'='*80}")
        safe_print(f"🚀 Starting upload for ID: {upload_id}")
        safe_print(f"   Subject: {subject_code}")
        safe_print(f"   User: {username}")
        safe_print(f"{'='*80}")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        lms_automation_path = os.path.join(current_dir, 'lms_automation.py')
        
        cmd = ['python', lms_automation_path, username, password, subject_code, pdf_path]
        
        if submission_url:
            cmd.append(submission_url)
            safe_print(f"✅ Using direct URL for {subject_code}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            encoding='utf-8',
            errors='replace'
        )
        
        output = result.stdout
        error_output = result.stderr
        
        try:
            json_start = output.find("JSON_START")
            json_end = output.find("JSON_END")
            
            if json_start >= 0 and json_end > json_start:
                json_str = output[json_start + 10:json_end].strip()
                lms_result = json.loads(json_str)
            else:
                raise ValueError("No JSON markers found")
        except Exception as e:
            safe_print(f"❌ Failed to parse result for ID {upload_id}: {e}")
            return (upload_id, False, {
                'error': f'Failed to parse automation result: {str(e)}',
                'stdout': output,
                'stderr': error_output
            })
        
        upload_result = lms_result.get('upload', {})
        success = upload_result.get('success', False)
        
        if success:
            safe_print(f"✅ Upload successful for ID: {upload_id}")
        else:
            safe_print(f"❌ Upload failed for ID: {upload_id}")
        
        return (upload_id, success, lms_result)
        
    except subprocess.TimeoutExpired:
        safe_print(f"⏰ Timeout for ID: {upload_id}")
        return (upload_id, False, {'error': 'Upload timeout after 10 minutes'})
    
    except Exception as e:
        safe_print(f"❌ Exception for ID {upload_id}: {e}")
        safe_print(traceback.format_exc())
        return (upload_id, False, {'error': str(e)})

def parallel_upload(uploads_data, max_workers=3):
    """Upload multiple PDFs in parallel"""
    results = {}
    
    safe_print(f"\n{'='*80}")
    safe_print(f"🚀 PARALLEL UPLOAD STARTED")
    safe_print(f"   Total uploads: {len(uploads_data)}")
    safe_print(f"   Max workers: {max_workers}")
    safe_print(f"{'='*80}\n")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {
            executor.submit(upload_single_pdf, upload_data): upload_data['id']
            for upload_data in uploads_data
        }
        
        for future in as_completed(future_to_id):
            upload_id = future_to_id[future]
            try:
                upload_id, success, result = future.result()
                results[upload_id] = {
                    'success': success,
                    'result': result
                }
                
                status = "✅ SUCCESS" if success else "❌ FAILED"
                safe_print(f"\n{status} - Upload ID: {upload_id}")
                
            except Exception as e:
                safe_print(f"❌ Exception processing upload {upload_id}: {e}")
                results[upload_id] = {
                    'success': False,
                    'result': {'error': str(e)}
                }
    
    safe_print(f"\n{'='*80}")
    safe_print(f"📊 PARALLEL UPLOAD COMPLETED")
    safe_print(f"   Total: {len(results)}")
    safe_print(f"   Successful: {sum(1 for r in results.values() if r['success'])}")
    safe_print(f"   Failed: {sum(1 for r in results.values() if not r['success'])}")
    safe_print(f"{'='*80}\n")
    
    return results

def main():
    """Main function for command-line usage"""
    if len(sys.argv) < 2:
        print("Usage: python parallel_lms_uploader.py <uploads_json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            uploads_data = json.load(f)
        
        max_workers = int(os.environ.get('MAX_PARALLEL_UPLOADS', 3))
        
        results = parallel_upload(uploads_data, max_workers)
        
        print("JSON_START")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        print("JSON_END")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
