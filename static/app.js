// static/app.js
// Handles recording, upload, polling, and rendering results

// DOM elements
const preview        = document.getElementById('preview');
const recordBtn      = document.getElementById('recordBtn');
const spinner        = document.getElementById('spinner');
const resultsPanel   = document.getElementById('results');
const errorMsg       = document.getElementById('errorMsg');
const transcriptEl   = document.getElementById('transcript');
const objectLabelEl  = document.getElementById('objectLabel');
const correctnessEl  = document.getElementById('correctness');
const canvas         = document.getElementById('resultCanvas');
const ctx            = canvas.getContext('2d');

let mediaRecorder;
let recordedBlobs;
let recording = false;
let jobId;

// Initialize video preview
async function initCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    preview.srcObject = stream;
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (event) => {
      if (!recordedBlobs) recordedBlobs = [];
      if (event.data && event.data.size > 0) {
        recordedBlobs.push(event.data);
      }
    };

    mediaRecorder.onstop = handleStop;
  } catch (err) {
    showError('Camera access denied or unavailable.');
  }
}

// Start or stop recording
recordBtn.addEventListener('click', () => {
  if (!recording) {
    recordedBlobs = [];
    mediaRecorder.start();
    recordBtn.textContent = 'Stop & Upload';
    recording = true;
  } else {
    mediaRecorder.stop();
    recordBtn.disabled = true; // prevent double clicks
  }
});

// Handle end of recording
async function handleStop() {
  const blob = new Blob(recordedBlobs, { type: 'video/webm' });
  try {
    jobId = await uploadVideo(blob);
    pollForResult(jobId, blob);
  } catch (err) {
    showError(err);
  }
}

// Upload recorded video to API
async function uploadVideo(blob) {
  spinner.classList.remove('d-none');
  const formData = new FormData();
  formData.append('file', blob, 'recording.webm');

  const response = await fetch('/upload', { method: 'POST', body: formData });
  const data = await response.json();
  if (!response.ok) {
    throw data.error || 'Upload failed';
  }
  return data.job_id;
}

// Poll the API for results
function pollForResult(jobId, blob) {
  const interval = setInterval(async () => {
    const res = await fetch(`/result/${jobId}`);
    const data = await res.json();
    if (data.status === 'completed') {
      clearInterval(interval);
      spinner.classList.add('d-none');
      renderResults(data.result, blob);
    }
  }, 2000);
}

// Render transcript, object label, correctness, and draw boxes
function renderResults(result, blob) {
  // Show results panel
  resultsPanel.classList.remove('d-none');

  // 1) Display transcript (in German)
  transcriptEl.textContent = result.transcript;

  // 2) Use the German label from the back-end
  //    (falls back to 'N/A' if translation was not possible)
  const labelGer = result.label_german || 'N/A';
  objectLabelEl.textContent = labelGer;

  // 3) Normalize & exact‑match the two German strings (strip punctuation)
  const cleanTranscript = result.transcript
      .trim()
      .replace(/[.,!?]$/g, '')      // remove trailing .,!?
      .toLowerCase();
  const cleanLabel = labelGer.toLowerCase();
  const correct = cleanTranscript === cleanLabel;
  correctnessEl.textContent = correct ? 'Correct' : 'Incorrect';

  // 4) Draw middle frame and overlay boxes
  const recordedVideo = document.createElement('video');
  recordedVideo.src = URL.createObjectURL(blob);
  recordedVideo.muted = true;
  recordedVideo.playsInline = true;

  recordedVideo.addEventListener('loadedmetadata', () => {
    recordedVideo.currentTime = recordedVideo.duration / 2;
  });

  recordedVideo.addEventListener('seeked', () => {
    // match canvas to video size
    canvas.width  = recordedVideo.videoWidth;
    canvas.height = recordedVideo.videoHeight;

    // draw frame
    ctx.drawImage(recordedVideo, 0, 0, canvas.width, canvas.height);

    // draw face boxes in red
    ctx.lineWidth   = 2;
    ctx.strokeStyle = 'red';
    result.faces.forEach(f => {
      const [x, y, w, h] = f.box;
      ctx.strokeRect(x, y, w, h);
    });

    // draw object boxes in blue (for context)
    ctx.strokeStyle = 'blue';
    result.objects.forEach(o => {
      const [x, y, x2, y2] = o.box;
      ctx.strokeRect(x, y, x2 - x, y2 - y);
    });
  });
}

// Display error message
function showError(msg) {
  spinner.classList.add('d-none');
  errorMsg.textContent = msg;
  errorMsg.classList.remove('d-none');
}

// Kick off camera init
initCamera();