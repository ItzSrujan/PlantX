import os
import cv2
import re
import numpy as np
import tensorflow.lite as tflite
import time
import base64
import google.generativeai as genai
from flask import Flask, request, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename
from io import BytesIO
from PIL import Image

app = Flask(__name__)
app.secret_key = "plantx_secret_key"

# Configure Gemini API
genai.configure(api_key="AIzaSyBetR0Dt6GoVjicSh0LGipYmo1m6dYw-Kc")

# Load TFLite model
interpreter = tflite.Interpreter(model_path="./model/PlantX_model.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("✅ TFLite Model Loaded Successfully!")

class_names = [
    "Pepper__bell___Bacterial_spot",
    "Pepper__bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Tomato_Bacterial_spot",
    "Tomato_Early_blight",
    "Tomato_Late_blight",
    "Tomato_Leaf_Mold",
    "Tomato_Septoria_leaf_spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite",
    "Tomato__Target_Spot",
    "Tomato__Tomato_YellowLeaf__Curl_Virus",
    "Tomato__Tomato_mosaic_virus",
    "Tomato_healthy"
]

def preprocess_image(image_bytes, target_size=(224, 224)):
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image = image.resize(target_size)
    image = np.array(image, dtype=np.float32) / 255.0
    return image

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# Extract info without asterisks
def extract_info(text, keyword):
    match = re.search(rf"{keyword}:\s*(.+?)(\n[A-Z]|$)", text, re.DOTALL | re.IGNORECASE)
    if match:
        return convert_bullets_to_numbered(match.group(1).strip())
    return f"Error fetching {keyword.lower()}."

def convert_bullets_to_numbered(text):
    lines = text.strip().split('\n')
    numbered_lines = []
    count = 1
    for line in lines:
        if line.strip().startswith('*'):
            line = re.sub(r'^\*\s*', f'{count}. ', line)
            numbered_lines.append(line)
            count += 1
        else:
            numbered_lines.append(line)
    return '\n'.join(numbered_lines)

def get_disease_info(disease_name):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"""
You are an expert plant pathologist. Give the following structured info about "{disease_name}" clearly:

Disease Description: (Short explanation)  
Cause: (Explain what causes it, like bacteria/fungus/etc.)  
Treatment: (Mention common solutions, precautions or remedies)

Return each section starting with the keyword exactly like above (e.g., Cause:). Avoid using ** or * or extra formatting. No intro or closing sentence.
"""
        response = model.generate_content(prompt)

        if not response or not response.text:
            return "Error fetching disease info.", "Error fetching cause.", "Error fetching treatment."

        text = response.text.strip()
        disease_info = extract_info(text, "Disease Description")
        cause = extract_info(text, "Cause")
        treatment = extract_info(text, "Treatment")

        return disease_info, cause, treatment

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Error fetching disease info.", "Error fetching cause.", "Error fetching treatment."

def predict_single_image(image_bytes):
    image = preprocess_image(image_bytes)
    if image is None:
        return None, None, None, None, None, None

    image_expanded = np.expand_dims(image, axis=0).astype(np.float32)
    interpreter.set_tensor(input_details[0]['index'], image_expanded)
    
    start_time = time.time()
    interpreter.invoke()
    end_time = time.time()

    output_data = interpreter.get_tensor(output_details[0]['index'])
    predicted_index = np.argmax(output_data)
    predicted_class = class_names[predicted_index]
    confidence_score = output_data[0][predicted_index] * 100
    prediction_time = end_time - start_time

    disease_info, cause, treatment = get_disease_info(predicted_class)

    return predicted_class, confidence_score, prediction_time, disease_info, cause, treatment

app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "files" not in request.files:
            return render_template("upload.html", error="No file uploaded!")

        files = request.files.getlist("files")
        if not files or all(file.filename == "" for file in files):
            return render_template("upload.html", error="No selected files!")

        if len(files) > 6:
            return render_template("upload.html", error="⚠️ You can only upload up to 6 images!")

        new_results = []

        for file in files:
            if len(file.read()) > 2 * 1024 * 1024:
                return render_template("upload.html", error="⚠️ Each image must be under 2MB!")
            file.seek(0)

            image_bytes = file.read()
            encoded_image = encode_image(image_bytes)

            predicted_class, confidence, time_taken, disease_info, cause, treatment = predict_single_image(image_bytes)

            if predicted_class:
                new_results.append({
                    "image": encoded_image,
                    "disease": predicted_class,
                    "confidence": f"{float(confidence):.2f}%",
                    "time_taken": f"{float(time_taken):.4f} sec",
                    "disease_info": disease_info,
                    "cause": cause,
                    "treatment": treatment
                })

        if "results" not in session:
            session["results"] = []
        session["results"].extend(new_results)
        session.modified = True

        return render_template("result.html", results=session["results"])

    return render_template("upload.html")

@app.route("/results")
def show_results():
    return render_template("result.html", results=session.get("results", []))

if __name__ == "__main__":
    app.run(debug=True)