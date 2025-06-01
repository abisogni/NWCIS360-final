// DOM elements
const preview = document.getElementById('preview');
const recordBtn = document.getElementById('recordBtn');
const newRecordingBtn = document.getElementById('newRecordingBtn');
const spinner = document.getElementById('spinner');
const resultsPanel = document.getElementById('results');
const errorMsg = document.getElementById('errorMsg');
const transcriptEl = document.getElementById('transcript');
const objectLabelEl = document.getElementById('objectLabel');
const correctnessEl = document.getElementById('correctness');

let mediaRecorder;
let recordedBlobs;
let recording = false;
let jobId;
let currentStream;

// Initialize video preview with enhanced error handling
async function initCamera() {
  console.log('Attempting to initialize camera...');

  try {
    // First check if getUserMedia is supported
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('getUserMedia is not supported in this browser');
    }

    console.log('Requesting camera and microphone access...');
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
      audio: true
    });

    console.log('Camera access granted, setting up stream...');
    currentStream = stream;
    preview.srcObject = stream;

    // Wait for video to load
    preview.onloadedmetadata = function() {
      console.log('Video preview loaded successfully');
    };

    mediaRecorder = new MediaRecorder(stream);
    console.log('MediaRecorder created successfully');

    mediaRecorder.ondataavailable = (event) => {
      if (!recordedBlobs) recordedBlobs = [];
      if (event.data && event.data.size > 0) {
        recordedBlobs.push(event.data);
      }
    };

    mediaRecorder.onstop = handleStop;

    console.log('Camera initialization complete!');

  } catch (err) {
    console.error('Camera initialization error:', err);
    let errorMessage = 'Camera access failed: ';

    if (err.name === 'NotAllowedError') {
      errorMessage += 'Please allow camera and microphone access and refresh the page.';
    } else if (err.name === 'NotFoundError') {
      errorMessage += 'No camera found. Please connect a camera and refresh.';
    } else if (err.name === 'NotReadableError') {
      errorMessage += 'Camera is being used by another application.';
    } else {
      errorMessage += err.message;
    }

    showError(errorMessage);
  }
}

// Enhanced record button handling
recordBtn.addEventListener('click', () => {
  if (!recording) {
    startRecording();
  } else {
    stopRecording();
  }
});

// New recording button handling
newRecordingBtn.addEventListener('click', () => {
  resetForNewRecording();
});

// Start recording function
function startRecording() {
  recordedBlobs = [];
  mediaRecorder.start();
  recordBtn.innerHTML = '<i class="fas fa-stop-circle me-2"></i>Stop & Analyze';
  recordBtn.classList.add('recording');
  recording = true;

  // Hide previous results and errors
  hideAllPanels();
}

// Stop recording function
function stopRecording() {
  mediaRecorder.stop();
  recordBtn.disabled = true;
  recordBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
}

// Reset for new recording
function resetForNewRecording() {
  // Hide results and show live preview
  hideAllPanels();

  // Reset button states
  recordBtn.classList.remove('d-none');
  newRecordingBtn.classList.add('d-none');
  resetRecordButton();

  // Clear previous results
  clearResults();

  // Restart camera preview if needed
  if (!currentStream || !currentStream.active) {
    initCamera();
  }
}

// Hide all result/error panels
function hideAllPanels() {
  resultsPanel.classList.add('d-none');
  errorMsg.classList.add('d-none');
  spinner.classList.add('d-none');
}

// Handle end of recording
async function handleStop() {
  const blob = new Blob(recordedBlobs, { type: 'video/webm' });
  try {
    jobId = await uploadVideo(blob);
    pollForResult(jobId, blob);
  } catch (err) {
    showError(err);
    resetRecordButton();
  }
}

// Upload recorded video to API
async function uploadVideo(blob) {
  spinner.classList.remove('d-none');
  hideAllPanels();
  spinner.classList.remove('d-none'); // Show spinner

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
    try {
      const res = await fetch(`/result/${jobId}`);
      const data = await res.json();
      if (data.status === 'completed') {
        clearInterval(interval);
        spinner.classList.add('d-none');
        renderResults(data.result);
        showNewRecordingOption();
      }
    } catch (err) {
      clearInterval(interval);
      showError('Failed to get results');
      resetRecordButton();
    }
  }, 2000);
}

// Simplified results rendering (no canvas)
function renderResults(result) {
  resultsPanel.classList.remove('d-none');

  // Display transcript
  transcriptEl.textContent = result.transcript || 'No speech detected';

  // Display German label
  const labelGer = result.label_german || 'No object detected';
  objectLabelEl.textContent = labelGer;

  // Enhanced correctness display
  const cleanTranscript = (result.transcript || '')
      .trim()
      .replace(/[.,!?]$/g, '')
      .toLowerCase();
  const cleanLabel = labelGer.toLowerCase();
  const correct = cleanTranscript === cleanLabel;

  correctnessEl.innerHTML = correct
    ? '<i class="fas fa-check text-success me-2"></i>Correct! Well done!'
    : '<i class="fas fa-times text-warning me-2"></i>Not quite right';
}

// Show new recording option
function showNewRecordingOption() {
  recordBtn.classList.add('d-none');
  newRecordingBtn.classList.remove('d-none');
}

// Enhanced error handling
function showError(msg) {
  hideAllPanels();
  errorMsg.querySelector('span').textContent = msg;
  errorMsg.classList.remove('d-none');
  resetRecordButton();
}

// Reset record button state
function resetRecordButton() {
  recordBtn.innerHTML = '<i class="fas fa-play-circle me-2"></i>Start Recording';
  recordBtn.classList.remove('recording');
  recordBtn.disabled = false;
  recording = false;
}

// Clear previous results
function clearResults() {
  transcriptEl.textContent = '—';
  objectLabelEl.textContent = '—';
  correctnessEl.textContent = '—';
}

// Initialize camera on load
initCamera();