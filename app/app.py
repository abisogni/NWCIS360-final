from pathlib import Path
import os
import uuid
import json
from flask import Flask, request, jsonify

from app.processing import process_job  # the pipeline orchestrator

# Base directories
BASE_DIR    = Path(__file__).resolve().parent.parent
UPLOAD_DIR  = BASE_DIR / "tmp" / "uploads"
RESULTS_DIR = BASE_DIR / "tmp" / "results"

# Ensure the tmp folders exist
for d in (UPLOAD_DIR, RESULTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Flask setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_DIR)

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'API is running'}), 200

@app.route('/upload', methods=['POST'])
def upload_video():
    # 1) Validate request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # 2) Save the upload
    job_id = str(uuid.uuid4())
    job_folder = UPLOAD_DIR / job_id
    job_folder.mkdir(exist_ok=True)
    save_path = job_folder / file.filename
    file.save(str(save_path))

    # 3) Process synchronously (for demo purposes)
    try:
        process_job(job_id, file.filename)
    except Exception as e:
        return jsonify({'error': f'Processing failed: {e}'}), 500

    # 4) Return the job ID
    return jsonify({'job_id': job_id}), 200

@app.route('/result/<job_id>', methods=['GET'])
def get_result(job_id):
    result_file = RESULTS_DIR / f"{job_id}.json"
    if result_file.exists():
        payload = json.loads(result_file.read_text())
        return jsonify({'status': 'completed', 'result': payload}), 200
    else:
        return jsonify({'status': 'pending'}), 200

if __name__ == '__main__':
    # When running directly: `python app.py`
    app.run(debug=True)