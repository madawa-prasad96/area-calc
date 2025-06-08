import os
from flask import Flask, request, jsonify
from PIL import Image
from werkzeug.utils import secure_filename
import cv2  # OpenCV
import pytesseract
import re # For parsing numbers from OCR
from .utils import extract_numbers_from_text, estimate_area_from_pixels_and_ocr

# Load environment variables (if any, e.g., for upload folder)
# from dotenv import load_dotenv
# load_dotenv()

app = Flask(__name__)

# Configure upload folder (optional, can be set via .env)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB limit

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def hello():
    return "Backend server is running!"

@app.route('/calculate_area', methods=['POST'])
def calculate_area_endpoint():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    unit = request.form.get('unit')

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not unit:
        return jsonify({'error': 'No unit provided'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(filepath)
            # Basic image validation with Pillow
            img_pil = Image.open(filepath)
            img_pil.verify() # Verify it's an image
            img_pil.close() # Close file handle after verify (important)

            # Re-open with OpenCV for processing
            img_cv = cv2.imread(filepath)
            if img_cv is None: # Check if image loading failed
                if os.path.exists(filepath): os.remove(filepath)
                return jsonify({'error': 'Failed to load image with OpenCV.'}), 500

            # 1. Image Preprocessing
            gray_img = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            _, binary_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # 2. OCR with Pytesseract
            custom_config = r'--oem 3 --psm 6'
            extracted_text = "OCR failed or no text found." # Default message
            try:
                extracted_text_data = pytesseract.image_to_string(binary_img, config=custom_config)
                if extracted_text_data and extracted_text_data.strip():
                    extracted_text = extracted_text_data.strip()
            except pytesseract.TesseractNotFoundError:
                print("Tesseract is not installed or not in your PATH.")
                # Clean up before returning
                if os.path.exists(filepath): os.remove(filepath)
                return jsonify({'error': 'OCR engine (Tesseract) not found on server.'}), 500
            except Exception as ocr_error:
                print(f"OCR error: {ocr_error}")
                # extracted_text remains "OCR failed or no text found." if other error occurs

            # 3. Basic Shape Detection (Example: Find Contours)
            contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            num_contours = len(contours)
            largest_contour_area_pixels = 0.0
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                largest_contour_area_pixels = float(cv2.contourArea(largest_contour))

            # 4. Approximate Area Calculation based on OCR and Contour
            # Ensure extracted_text (which is ocr_output_str for the utility function) is defined
            ocr_output_str = extracted_text
            extracted_numbers = extract_numbers_from_text(ocr_output_str)

            estimated_area, scale_used_for_estimation, calculation_notes = \
                estimate_area_from_pixels_and_ocr(
                    largest_contour_area_pixels,
                    extracted_numbers,
                    unit
                )

            # Clean up the saved image file after processing
            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({
                'message': 'Image processed',
                'filename': filename,
                'input_unit': unit, # The unit selected by user
                'ocr_output': ocr_output_str, # Use the string that was processed
                'extracted_numbers_from_ocr': extracted_numbers,
                'detected_contours_count': num_contours,
                'largest_contour_area_pixels': largest_contour_area_pixels,
                'estimated_area_in_input_units': f"{estimated_area:.2f}" if estimated_area > 0 else "N/A",
                'scale_used_for_estimation': scale_used_for_estimation, # Already "N/A" if not applicable
                'calculation_notes': calculation_notes
            }), 200

        except Exception as e:
            # Clean up saved file if error during processing
            if os.path.exists(filepath):
                os.remove(filepath)
            # Log the full error for server-side debugging
            print(f"Error during image processing pipeline: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Error processing image with OpenCV/Tesseract: {str(e)}'}), 500
    else:
        return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    # It's good practice to make host and port configurable,
    # but for this subtask, defaults are fine.
    # Host '0.0.0.0' makes it accessible on the network.
    app.run(debug=True, host='0.0.0.0', port=5000)
