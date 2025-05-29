from app.processing import process_job
import shutil
import uuid
import os

# 1) Prepare the test job
JOB_ID   = uuid.uuid4().hex
FNAME    = "test_qt.mov"
SRC_PATH = os.path.join(os.getcwd(), FNAME)
DST_DIR  = os.path.join("tmp", "uploads", JOB_ID)
os.makedirs(DST_DIR, exist_ok=True)
shutil.copy(SRC_PATH, os.path.join(DST_DIR, FNAME))

# 2) Run the pipeline
result_path = process_job(JOB_ID, FNAME)
print("Result written to:", result_path)

# 3) Load and print a summary
import json
with open(result_path) as f:
    data = json.load(f)
print("Faces detected:", len(data["faces"]))
print("Objects detected:", len(data["objects"]))
print("Transcript:", data["transcript"])