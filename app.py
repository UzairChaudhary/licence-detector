from flask import Flask, request, jsonify
import os
import pandas as pd
from ultralytics import YOLO
from PIL import Image, ImageEnhance
import pytesseract

# Initialize Flask app
app = Flask(__name__)

# Set up paths and load the YOLO model
pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
model_path = 'yolov8_license_plate.pt'
model = YOLO(model_path)
output_dir = 'inference_output'
os.makedirs(output_dir, exist_ok=True)

# Load expired and valid license plates with complete information
expired_df = pd.read_csv('Expired_License_Plates.csv')
valid_df = pd.read_csv('Valid_License_Plates.csv')

# Convert the data to dictionaries with Car Plate Number as the key for easy lookup
expired_license_data = expired_df.set_index("Car Plate Number").to_dict(orient="index")
valid_license_data = valid_df.set_index("Car Plate Number").to_dict(orient="index")

# Function to generate OCR text from detected plate images
def detect_and_ocr_plate(image_path):
    results = model.predict(source=image_path)
    ocr_results = []

    for result in results:
        for bbox in result.boxes.xyxy:
            x_min, y_min, x_max, y_max = map(int, bbox)
            cropped_plate = Image.open(image_path).crop((x_min, y_min, x_max, y_max))

            # Enhance the cropped image
            cropped_plate = cropped_plate.convert("L")
            enhancer = ImageEnhance.Contrast(cropped_plate)
            cropped_plate = enhancer.enhance(2.0)
            cropped_plate = cropped_plate.resize((cropped_plate.width * 2, cropped_plate.height * 2), Image.LANCZOS)

            # Run OCR
            text = pytesseract.image_to_string(cropped_plate, config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            ocr_results.append({"box": [x_min, y_min, x_max, y_max], "text": text.strip()})

    return ocr_results


# Route to handle image upload and processing
@app.route('/detect_license_plate', methods=['POST'])
def detect_license_plate():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    # Save uploaded image
    image = request.files['image']
    image_path = os.path.join(output_dir, image.filename)
    image.save(image_path)

    # Detect and OCR
    ocr_results = detect_and_ocr_plate(image_path)

    # Check each detected plate against expired and valid license plates and retrieve full information
    license_check_results = []
    for entry in ocr_results:
        detected_plate = entry["text"]
        if detected_plate in expired_license_data:
            plate_info = expired_license_data[detected_plate]
            plate_info.update({"status": "expired"})
            license_check_results.append(plate_info)
        elif detected_plate in valid_license_data:
            plate_info = valid_license_data[detected_plate]
            plate_info.update({"status": "valid"})
            license_check_results.append(plate_info)
        else:
            license_check_results.append({"plate": detected_plate, "status": "unknown"})

    # Return results as JSON
    response = {
        "ocr_results": ocr_results,
        "license_check_results": license_check_results
    }
    return jsonify(response)


# Main function to run the app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
