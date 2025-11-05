"""
ML Service for Answer Sheet Processing - Enhanced Version
This script integrates YOLO and CRNN models for text extraction
with improved register number prediction accuracy
"""

import os
import sys
import json
import torch
import cv2
import numpy as np
from PIL import Image
from torchvision import transforms
import torch.nn as nn
import tempfile
import traceback
import shutil
import time

# Add imports based on available packages
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False
    print("Warning: YOLO not available", file=sys.stderr)

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False
    print("Warning: pdf2image not available", file=sys.stderr)

def debug_print(message):
    """Print debug messages to stderr to avoid interfering with JSON output"""
    print(message, file=sys.stderr)

def validate_register_number(register_number):
    """Validate that register number is 12 digits"""
    if not register_number:
        return False
    cleaned = register_number.strip().replace(' ', '')
    return len(cleaned) == 12 and cleaned.isdigit()

def validate_subject_code(subject_code):
    """Validate subject code format"""
    if not subject_code:
        return False
    cleaned = subject_code.strip().replace(' ', '').upper()
    return 5 <= len(cleaned) <= 8 and cleaned.isalnum()

# Define the CRNN model class
class CRNN(nn.Module):
    def __init__(self, num_classes):
        super(CRNN, self).__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.3),
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d((2, 1), (2, 1)),
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.MaxPool2d((2, 1), (2, 1)),
            nn.Dropout2d(0.3),
            nn.Conv2d(512, 512, kernel_size=(2, 1)),
            nn.BatchNorm2d(512),
            nn.ReLU(),
        )
        
        self.rnn = nn.LSTM(512, 256, num_layers=2, bidirectional=True, dropout=0.3)
        self.dropout = nn.Dropout(0.5)
        self.fc = nn.Linear(512, num_classes)

    def forward(self, x):
        x = self.cnn(x)
        x = x.squeeze(2)
        x = x.permute(2, 0, 1)
        x, _ = self.rnn(x)
        x = self.dropout(x)
        x = self.fc(x)
        return x

class AnswerSheetExtractor:
    def __init__(self, yolo_primary_path=None, yolo_fallback_path=None, crnn_register_path=None, crnn_subject_path=None):
        # Ensure directories exist
        os.makedirs("temp", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        debug_print(f"Using device: {self.device}")
        
        # Set model paths relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.primary_yolo_path = yolo_primary_path or os.path.join(project_root, "models", "improved_weights.pt")
        self.fallback_yolo_path = yolo_fallback_path or os.path.join(project_root, "models", "weights.pt")
        self.register_crnn_path = crnn_register_path or os.path.join(project_root, "models", "best_crnn_model(git).pth")
        self.subject_crnn_path = crnn_subject_path or os.path.join(project_root, "models", "best_subject_model_final.pth")
        
        try:
            self.load_models()
        except Exception as e:
            debug_print(f"Error loading models: {e}")
            self.models_loaded = False

    def load_models(self):
        """Load all ML models"""
        # Load YOLO models
        if HAS_YOLO and os.path.exists(self.primary_yolo_path):
            try:
                self.primary_yolo_model = YOLO(self.primary_yolo_path)
                debug_print("Primary YOLO model loaded")
            except Exception as e:
                debug_print(f"Error loading primary YOLO model: {e}")
        else:
            debug_print(f"Warning: Primary YOLO model not found at {self.primary_yolo_path}")
        
        if HAS_YOLO and os.path.exists(self.fallback_yolo_path):
            try:
                self.fallback_yolo_model = YOLO(self.fallback_yolo_path)
                debug_print("Fallback YOLO model loaded")
            except Exception as e:
                debug_print(f"Error loading fallback YOLO model: {e}")
        else:
            debug_print(f"Warning: Fallback YOLO model not found at {self.fallback_yolo_path}")

        # Load Register Number CRNN model
        if os.path.exists(self.register_crnn_path):
            try:
                self.register_crnn_model = CRNN(num_classes=11)  # 10 digits + blank
                self.register_crnn_model.to(self.device)
                checkpoint = torch.load(self.register_crnn_path, map_location=self.device)
                state_dict = checkpoint.get('model_state_dict', checkpoint)
                new_state_dict = {}
                for k, v in state_dict.items():
                    if k.startswith('module.'):
                        new_state_dict[k[7:]] = v
                    else:
                        new_state_dict[k] = v
                self.register_crnn_model.load_state_dict(new_state_dict)
                self.register_crnn_model.eval()
                debug_print("Register CRNN model loaded")
            except Exception as e:
                debug_print(f"Error loading register CRNN model: {e}")
        else:
            debug_print(f"Warning: Register CRNN model not found at {self.register_crnn_path}")

        # Load Subject Code CRNN model
        if os.path.exists(self.subject_crnn_path):
            try:
                self.subject_crnn_model = CRNN(num_classes=37)  # blank + 0-9 + A-Z
                self.subject_crnn_model.to(self.device)
                subject_checkpoint = torch.load(self.subject_crnn_path, map_location=self.device)
                subject_state_dict = subject_checkpoint.get('model_state_dict', subject_checkpoint)
                new_subject_state_dict = {}
                for k, v in subject_state_dict.items():
                    if k.startswith('module.'):
                        new_subject_state_dict[k[7:]] = v
                    else:
                        new_subject_state_dict[k] = v
                self.subject_crnn_model.load_state_dict(new_subject_state_dict)
                self.subject_crnn_model.eval()
                debug_print("Subject CRNN model loaded")
            except Exception as e:
                debug_print(f"Error loading subject CRNN model: {e}")
        else:
            debug_print(f"Warning: Subject CRNN model not found at {self.subject_crnn_path}")

        # Define image transforms
        self.register_transform = transforms.Compose([
            transforms.Resize((32, 256)),
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,))
        ])
        
        self.subject_transform = transforms.Compose([
            transforms.Resize((32, 128)),
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,))
        ])

        # Define character map for subject code
        self.char_map = {i: str(i-1) for i in range(1, 11)}  # 1-10 -> 0-9
        self.char_map.update({i: chr(i - 11 + ord('A')) for i in range(11, 37)})  # 11-36 -> A-Z
        self.char_map[0] = ''  # Map blank (index 0) to empty string
        
        self.models_loaded = True

    def save_persistent_pdf_for_lms(self, pdf_buffer, filename):
        """Save uploaded PDF directly in temp folder for LMS upload"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            temp_dir = os.path.join(project_root, "temp")
            os.makedirs(temp_dir, exist_ok=True)

            timestamp = int(time.time())
            base_name = os.path.splitext(filename)[0]
            safe_filename = base_name.replace(' ', '_').replace('(', '').replace(')', '').replace('[', '').replace(']', '')
            persistent_pdf_filename = f"{timestamp}_{safe_filename}.pdf"
            persistent_pdf_path = os.path.join(temp_dir, persistent_pdf_filename)

            with open(persistent_pdf_path, 'wb') as f:
                f.write(pdf_buffer)

            debug_print(f"✅ PDF saved to temp folder: {persistent_pdf_path}")
            
            abs_persistent_pdf_path = os.path.abspath(persistent_pdf_path)
            return abs_persistent_pdf_path

        except Exception as e:
            debug_print(f"❌ Error saving PDF to temp folder: {e}")
            raise

    def save_cropped_images(self, register_regions, subject_regions):
        """Save cropped images and return paths for verification"""
        register_image_path = None
        subject_image_path = None
        
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cropped_dir = os.path.join(project_root, "media", "cropped")
            os.makedirs(os.path.join(cropped_dir, "register"), exist_ok=True)
            os.makedirs(os.path.join(cropped_dir, "subject"), exist_ok=True)
            
            # Save register number image
            if register_regions and len(register_regions) > 0:
                best_register = max(register_regions, key=lambda x: x[1])
                if os.path.exists(best_register[0]):
                    timestamp = int(time.time())
                    register_image_filename = f"register_{timestamp}.jpg"
                    register_image_path = os.path.join(cropped_dir, "register", register_image_filename)
                    shutil.copy(best_register[0], register_image_path)
                    debug_print(f"✅ Register image saved: {register_image_path}")
            
            # Save subject code image
            if subject_regions and len(subject_regions) > 0:
                best_subject = max(subject_regions, key=lambda x: x[1])
                if os.path.exists(best_subject[0]):
                    timestamp = int(time.time())
                    subject_image_filename = f"subject_{timestamp}.jpg"
                    subject_image_path = os.path.join(cropped_dir, "subject", subject_image_filename)
                    shutil.copy(best_subject[0], subject_image_path)
                    debug_print(f"✅ Subject image saved: {subject_image_path}")
            
            return register_image_path, subject_image_path
            
        except Exception as e:
            debug_print(f"Error saving cropped images: {e}")
            return None, None

    def convert_pdf_to_image_for_processing(self, pdf_buffer, filename):
        """Convert PDF to image for ML processing only"""
        try:
            temp_dir = tempfile.mkdtemp(prefix="pdf_processing_")
            temp_pdf_path = os.path.join(temp_dir, filename)
            
            with open(temp_pdf_path, 'wb') as f:
                f.write(pdf_buffer)

            first_page_image_path = os.path.join(temp_dir, 'first_page.jpg')

            if HAS_PDF2IMAGE:
                try:
                    images = convert_from_path(temp_pdf_path, dpi=300, first_page=1, last_page=1, fmt='jpeg')
                    
                    if images and len(images) > 0:
                        images[0].save(first_page_image_path, 'JPEG', quality=95)
                        debug_print(f"✅ PDF converted to image")
                        return first_page_image_path, temp_dir
                except Exception as pdf_error:
                    debug_print(f"pdf2image conversion failed: {pdf_error}")

            try:
                import fitz  # PyMuPDF
                pdf_document = fitz.open(temp_pdf_path)
                if len(pdf_document) > 0:
                    page = pdf_document[0]
                    mat = fitz.Matrix(2.0, 2.0)
                    pix = page.get_pixmap(matrix=mat)
                    pix.save(first_page_image_path)
                    pdf_document.close()
                    debug_print(f"✅ PyMuPDF conversion successful")
                    return first_page_image_path, temp_dir
            except:
                pass

            return first_page_image_path, temp_dir

        except Exception as e:
            debug_print(f"Error in convert_pdf_to_image_for_processing: {e}")
            raise

    def detect_regions(self, image_path):
        """Detect register number and subject code regions using YOLO"""
        if not self.models_loaded or not HAS_YOLO:
            return [(f"mock_register_{image_path}", 0.95)], [(f"mock_subject_{image_path}", 0.90)]

        try:
            image = cv2.imread(image_path)
            if image is None:
                return [(f"mock_register_{image_path}", 0.95)], [(f"mock_subject_{image_path}", 0.90)]

            register_regions = []
            subject_regions = []

            # Try primary YOLO model
            if hasattr(self, 'primary_yolo_model'):
                results_primary = self.primary_yolo_model(image, verbose=False)
                detections_primary = results_primary[0].boxes
                classes_primary = results_primary[0].names

                for i, box in enumerate(detections_primary):
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    label = classes_primary[class_id]

                    cropped_region = image[y1:y2, x1:x2]

                    if label == "RegisterNumber" and confidence > 0.5:
                        save_path = os.path.join(tempfile.gettempdir(), f"register_number_primary_{i}_{int(time.time())}.jpg")
                        cv2.imwrite(save_path, cropped_region)
                        register_regions.append((save_path, confidence))
                    
                    elif label == "SubjectCode" and confidence > 0.5:
                        save_path = os.path.join(tempfile.gettempdir(), f"subject_code_primary_{i}_{int(time.time())}.jpg")
                        cv2.imwrite(save_path, cropped_region)
                        subject_regions.append((save_path, confidence))

            # Try fallback YOLO if subject not found
            if not subject_regions and hasattr(self, 'fallback_yolo_model'):
                results_fallback = self.fallback_yolo_model(image, verbose=False)
                detections_fallback = results_fallback[0].boxes
                classes_fallback = results_fallback[0].names

                for i, box in enumerate(detections_fallback):
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    label = classes_fallback[class_id]

                    cropped_region = image[y1:y2, x1:x2]

                    if label == "SubjectCode" and confidence > 0.5:
                        save_path = os.path.join(tempfile.gettempdir(), f"subject_code_fallback_{i}_{int(time.time())}.jpg")
                        cv2.imwrite(save_path, cropped_region)
                        subject_regions.append((save_path, confidence))

            return register_regions, subject_regions

        except Exception as e:
            debug_print(f"Error in region detection: {e}")
            return [(f"mock_register_{image_path}", 0.95)], [(f"mock_subject_{image_path}", 0.90)]

    def extract_register_number(self, image_path):
            """Extract register number from cropped image"""
            if not self.models_loaded or not hasattr(self, 'register_crnn_model'):
                debug_print("Models not loaded, cannot extract register number")
                return None
                
            if image_path.startswith("mock_register_"):
                debug_print(f"Mock register path detected: {image_path}")
                return "212221"  # Sample register number
            
            try:
                if not os.path.exists(image_path) or os.path.getsize(image_path) < 100:
                    debug_print(f"Register image file not found or too small: {image_path}")
                    return None
                
                image = Image.open(image_path).convert('L')
                image_tensor = self.register_transform(image).unsqueeze(0).to(self.device)
                
                with torch.no_grad():
                    output = self.register_crnn_model(image_tensor).squeeze(1)
                    output = output.softmax(1).argmax(1)
                    seq = output.cpu().numpy()
                    
                    prev = -1
                    result = []
                    for s in seq:
                        if s != 0 and s != prev:
                            result.append(s - 1)
                        prev = s
                    
                    extracted = ''.join(map(str, result))
                    debug_print(f"Extracted register number: {extracted}")
                    
                    if extracted and len(extracted) >= 8 and extracted.isdigit():
                        return extracted
                    else:
                        return None
                        
            except Exception as e:
                debug_print(f"Error extracting register number: {e}")
                return None


    def extract_subject_code(self, image_path):
        """Extract subject code from cropped image"""
        if not self.models_loaded or not hasattr(self, 'subject_crnn_model'):
            return None

        if image_path.startswith("mock_subject_"):
            return "19AI505"

        try:
            if not os.path.exists(image_path):
                return None

            image = Image.open(image_path).convert('L')
            
            # Enhance image
            image_np = np.array(image)
            image_np = cv2.normalize(image_np, None, 0, 255, cv2.NORM_MINMAX)
            image_np = cv2.adaptiveThreshold(image_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY, 11, 2)
            image = Image.fromarray(image_np)
            
            image_tensor = self.subject_transform(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                output = self.subject_crnn_model(image_tensor).squeeze(1)
                output = output.softmax(1).argmax(1)
                seq = output.cpu().numpy()

            prev = 0
            result = []
            for s in seq:
                if s != 0 and s != prev:
                    result.append(self.char_map.get(s, ''))
                    prev = s
                elif s == 0:
                    prev = 0

            extracted = ''.join(result)
            debug_print(f"Extracted subject code: {extracted}")

            if validate_subject_code(extracted):
                return extracted
            else:
                return None

        except Exception as e:
            debug_print(f"Error extracting subject code: {e}")
            return None

    def process_uploaded_pdf(self, pdf_file_path, filename):
        """Main processing function for uploaded PDF"""
        processing_temp_dir = None
        persistent_pdf_path = None
        
        try:
            cleaned_file_path = pdf_file_path.strip('"').strip("'")

            if not cleaned_file_path.lower().endswith('.pdf'):
                return {'success': False, 'error': 'Only PDF files are allowed'}

            if not os.path.exists(cleaned_file_path):
                return {'success': False, 'error': f'PDF file not found: {cleaned_file_path}'}

            with open(cleaned_file_path, 'rb') as f:
                pdf_buffer = f.read()

            persistent_pdf_path = self.save_persistent_pdf_for_lms(pdf_buffer, filename)
            first_page_image_path, processing_temp_dir = self.convert_pdf_to_image_for_processing(pdf_buffer, filename)
            
            register_regions, subject_regions = self.detect_regions(first_page_image_path)
            register_image_path, subject_image_path = self.save_cropped_images(register_regions, subject_regions)

            results = {
                'persistentPdfPath': persistent_pdf_path,
                'registerImagePath': register_image_path,
                'subjectImagePath': subject_image_path,
                'tempDir': processing_temp_dir
            }

            # Extract register number - try multiple regions if needed
            register_number = None
            if register_regions:
                for region_path, confidence in sorted(register_regions, key=lambda x: x[1], reverse=True):
                    extracted = self.extract_register_number(region_path)
                    if extracted and len(extracted) == 12 and extracted.isdigit():
                        register_number = extracted
                        break

            if register_number:
                results['registerNumber'] = register_number
            else:
                if persistent_pdf_path and os.path.exists(persistent_pdf_path):
                    try:
                        os.remove(persistent_pdf_path)
                    except:
                        pass
                return {'success': False, 'error': 'Could not extract a valid 12-digit register number'}

            # Extract subject code
            subject_code = None
            if subject_regions:
                for region_path, confidence in sorted(subject_regions, key=lambda x: x[1], reverse=True):
                    extracted = self.extract_subject_code(region_path)
                    if extracted and validate_subject_code(extracted):
                        subject_code = extracted
                        break

            results['subjectCode'] = subject_code
            results['confidence'] = 0.95

            return {'success': True, 'data': results}

        except Exception as e:
            debug_print(f"❌ Error in process_uploaded_pdf: {e}")
            
            if processing_temp_dir and os.path.exists(processing_temp_dir):
                try:
                    shutil.rmtree(processing_temp_dir)
                except:
                    pass
            
            if persistent_pdf_path and os.path.exists(persistent_pdf_path):
                try:
                    os.remove(persistent_pdf_path)
                except:
                    pass

            return {'success': False, 'error': f'PDF processing failed: {str(e)}'}

        finally:
            if processing_temp_dir and os.path.exists(processing_temp_dir):
                try:
                    shutil.rmtree(processing_temp_dir)
                except:
                    pass
            self.cleanup_temp_files()

    def cleanup_temp_files(self):
        """Clean up temporary processing files"""
        try:
            temp_dir = tempfile.gettempdir()
            for file in os.listdir(temp_dir):
                if file.startswith(("register_number_", "subject_code_")) and file.endswith('.jpg'):
                    file_path = os.path.join(temp_dir, file)
                    try:
                        if os.path.getmtime(file_path) < time.time() - 3600:
                            os.remove(file_path)
                    except:
                        pass
        except:
            pass

def main():
    """Main function"""
    if len(sys.argv) < 2:
        result = {'success': False, 'error': 'Insufficient arguments'}
        print(json.dumps(result))
        sys.exit(1)

    file_path = sys.argv[1].strip('"').strip("'")

    if not os.path.exists(file_path):
        result = {'success': False, 'error': f'File {file_path} does not exist'}
        print(json.dumps(result))
        sys.exit(1)

    if not file_path.lower().endswith('.pdf'):
        result = {'success': False, 'error': 'Only PDF files are allowed'}
        print(json.dumps(result))
        sys.exit(1)

    extractor = AnswerSheetExtractor()
    result = extractor.process_uploaded_pdf(file_path, os.path.basename(file_path))

    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
