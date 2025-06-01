from pathlib import Path
import os
import uuid
import json
import sys
from flask import Flask, request, jsonify, render_template

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent  # Goes from /app to /Project
sys.path.append(str(project_root))

from processing import process_job  # pipeline orchestrator

# Base directories - pointing to correct locations
BASE_DIR    = Path(__file__).resolve().parent.parent  # /Project folder
UPLOAD_DIR  = BASE_DIR / "tmp" / "uploads"
RESULTS_DIR = BASE_DIR / "tmp" / "results"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR    = BASE_DIR / "static"

# Ensure tmp folders exist
for d in (UPLOAD_DIR, RESULTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Flask setup: serve templates and static from correct locations
app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR)
)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_DIR)

@app.route('/', methods=['GET'])
def home():
    """
    Render the main UI for recording and displaying results.
    """
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    # Validate request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the upload
    job_id = str(uuid.uuid4())
    job_folder = UPLOAD_DIR / job_id
    job_folder.mkdir(exist_ok=True)
    save_path = job_folder / file.filename
    file.save(str(save_path))

    # Process synchronously
    try:
        process_job(job_id, file.filename)
    except Exception as e:
        return jsonify({'error': f'Processing failed: {e}'}), 500

    return jsonify({'job_id': job_id}), 200

@app.route('/result/<job_id>', methods=['GET'])
def get_result(job_id):
    """
    Return processing status and result JSON when available.
    """
    result_file = RESULTS_DIR / f"{job_id}.json"
    if result_file.exists():
        payload = json.loads(result_file.read_text())
        return jsonify({'status': 'completed', 'result': payload}), 200
    else:
        return jsonify({'status': 'pending'}), 200

if __name__ == '__main__':
    # Run from project root: cd /Users/alex_at_home/NW/CIS-360/Final/Project
    # Then: python app/app.py
    print(f"Templates directory: {TEMPLATES_DIR}")
    print(f"Static directory: {STATIC_DIR}")
    print(f"Upload directory: {UPLOAD_DIR}")
    print(f"Results directory: {RESULTS_DIR}")
    app.run(debug=True)