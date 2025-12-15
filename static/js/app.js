// Global variables
let selectedFiles = [];
let currentJobId = null;
let socket = null;

// Initialize WebSocket connection
function initWebSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
    });

    socket.on('progress_update', (data) => {
        updateProgress(data);
    });

    socket.on('stitch_complete', (data) => {
        handleStitchComplete(data);
    });

    socket.on('stitch_error', (data) => {
        handleStitchError(data);
    });
}

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewSection = document.getElementById('previewSection');
const imagePreview = document.getElementById('imagePreview');
const imageCount = document.getElementById('imageCount');
const optionsSection = document.getElementById('optionsSection');
const startStitchingBtn = document.getElementById('startStitching');
const progressSection = document.getElementById('progressSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');

// Upload area click handler
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// Drag and drop handlers
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');

    const files = Array.from(e.dataTransfer.files);
    handleFileSelection(files);
});

// File input change handler
fileInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    handleFileSelection(files);
});

// Handle file selection
function handleFileSelection(files) {
    // Filter image files
    const imageFiles = files.filter(file => file.type.startsWith('image/'));

    if (imageFiles.length === 0) {
        alert('Please select valid image files');
        return;
    }

    selectedFiles = imageFiles;
    displayImagePreviews();
    updateUI();
}

// Display image previews
function displayImagePreviews() {
    imagePreview.innerHTML = '';

    selectedFiles.forEach((file, index) => {
        const reader = new FileReader();

        reader.onload = (e) => {
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item';
            previewItem.innerHTML = `
                <img src="${e.target.result}" alt="${file.name}">
                <button class="remove-btn" onclick="removeImage(${index})">×</button>
            `;
            imagePreview.appendChild(previewItem);
        };

        reader.readAsDataURL(file);
    });

    imageCount.textContent = selectedFiles.length;
    previewSection.style.display = 'block';
}

// Remove image from selection
function removeImage(index) {
    selectedFiles.splice(index, 1);
    displayImagePreviews();
    updateUI();
}

// Update UI based on state
function updateUI() {
    if (selectedFiles.length >= 2) {
        optionsSection.style.display = 'block';
        startStitchingBtn.style.display = 'block';
    } else {
        optionsSection.style.display = 'none';
        startStitchingBtn.style.display = 'none';
    }

    if (selectedFiles.length === 0) {
        previewSection.style.display = 'none';
    }
}

// Start stitching button handler
startStitchingBtn.addEventListener('click', async () => {
    if (selectedFiles.length < 2) {
        alert('Please select at least 2 images');
        return;
    }

    // Disable button
    startStitchingBtn.disabled = true;
    startStitchingBtn.textContent = '⏳ Uploading...';

    try {
        // Upload files
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        const uploadResponse = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            throw new Error('Upload failed');
        }

        const uploadData = await uploadResponse.json();
        currentJobId = uploadData.job_id;

        // Show progress section
        progressSection.style.display = 'block';
        progressSection.scrollIntoView({ behavior: 'smooth' });

        // Start stitching
        const featureDetector = document.getElementById('featureDetector').value;

        const stitchResponse = await fetch(`/api/stitch/${currentJobId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                feature_detector: featureDetector
            })
        });

        if (!stitchResponse.ok) {
            throw new Error('Failed to start stitching');
        }

        // Reset button
        startStitchingBtn.disabled = false;
        startStitchingBtn.textContent = '🚀 Start Stitching';

    } catch (error) {
        console.error('Error:', error);
        alert('Failed to start stitching: ' + error.message);
        startStitchingBtn.disabled = false;
        startStitchingBtn.textContent = '🚀 Start Stitching';
    }
});

// Update progress display
function updateProgress(data) {
    const { stage, percent, message } = data;

    // Update progress bar
    const progressBar = document.getElementById('progressBar');
    progressBar.style.width = percent + '%';

    // Update progress text
    document.getElementById('progressPercent').textContent = Math.round(percent) + '%';
    document.getElementById('progressMessage').textContent = message;

    // Update current stage
    const stageNames = {
        'loading': '📥 Loading Images',
        'features': '🔍 Detecting Features',
        'stitching': '🔗 Stitching Images',
        'complete': '✅ Complete'
    };

    document.getElementById('currentStage').textContent = stageNames[stage] || stage;

    // Update stage indicators
    updateStageIndicators(stage);

    // Add processing animation
    const progressStage = document.querySelector('.progress-stage');
    progressStage.classList.add('processing');
}

// Update stage indicators
function updateStageIndicators(currentStage) {
    const stages = ['loading', 'features', 'stitching', 'complete'];
    const currentIndex = stages.indexOf(currentStage);

    stages.forEach((stage, index) => {
        const stageElement = document.getElementById(`stage-${stage}`);
        const statusIcon = stageElement.querySelector('.stage-status');

        if (index < currentIndex) {
            // Completed
            stageElement.classList.add('completed');
            stageElement.classList.remove('active');
            statusIcon.textContent = '✅';
        } else if (index === currentIndex) {
            // Active
            stageElement.classList.add('active');
            stageElement.classList.remove('completed');
            statusIcon.textContent = '⏳';
        } else {
            // Pending
            stageElement.classList.remove('active', 'completed');
            statusIcon.textContent = '⏺️';
        }
    });
}

// Handle stitch completion
function handleStitchComplete(data) {
    const { output, stats } = data;

    // Show result section
    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth' });

    // Display panorama
    const panoramaImage = document.getElementById('panoramaImage');
    panoramaImage.src = `/api/result/${output}?t=${Date.now()}`;

    // Display statistics
    displayStats(stats);

    // Setup download button
    const downloadBtn = document.getElementById('downloadBtn');
    downloadBtn.onclick = () => {
        window.open(`/api/result/${output}`, '_blank');
    };

    // Remove processing animation
    const progressStage = document.querySelector('.progress-stage');
    progressStage.classList.remove('processing');
}

// Display statistics
function displayStats(stats) {
    const statsGrid = document.getElementById('statsGrid');
    statsGrid.innerHTML = '';

    const statItems = [
        {
            label: 'Number of Images',
            value: stats.num_images
        },
        {
            label: 'Feature Detector',
            value: stats.feature_detector
        },
        {
            label: 'Total Time',
            value: (stats.total_time || 0).toFixed(2) + 's'
        },
        {
            label: 'Loading Time',
            value: (stats.stages?.loading || 0).toFixed(2) + 's'
        },
        {
            label: 'Feature Detection',
            value: (stats.stages?.feature_detection || 0).toFixed(2) + 's'
        }
    ];

    statItems.forEach(item => {
        const statElement = document.createElement('div');
        statElement.className = 'stat-item';
        statElement.innerHTML = `
            <div class="stat-label">${item.label}</div>
            <div class="stat-value">${item.value}</div>
        `;
        statsGrid.appendChild(statElement);
    });
}

// Handle stitch error
function handleStitchError(data) {
    const { error } = data;

    // Show error section
    errorSection.style.display = 'block';
    errorSection.scrollIntoView({ behavior: 'smooth' });

    // Display error message
    document.getElementById('errorMessage').textContent = error;

    // Hide progress section
    progressSection.style.display = 'none';
}

// New stitch button handler
document.getElementById('newStitchBtn').addEventListener('click', () => {
    // Reset everything
    selectedFiles = [];
    currentJobId = null;

    // Hide sections
    previewSection.style.display = 'none';
    optionsSection.style.display = 'none';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';

    // Clear previews
    imagePreview.innerHTML = '';

    // Reset file input
    fileInput.value = '';

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Retry button handler
document.getElementById('retryBtn').addEventListener('click', () => {
    errorSection.style.display = 'none';
    progressSection.style.display = 'none';

    // Allow user to start again
    startStitchingBtn.disabled = false;
});

// Initialize WebSocket on page load
window.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
});
