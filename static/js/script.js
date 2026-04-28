// Tab Navigation
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.getAttribute('data-tab');
        
        // Remove active class from all tabs and buttons
        tabContents.forEach(content => content.classList.remove('active'));
        tabButtons.forEach(btn => btn.classList.remove('active'));
        
        // Add active class to clicked tab and button
        document.getElementById(tabName).classList.add('active');
        button.classList.add('active');
    });
});

// Drag and Drop
function setupDragDrop(uploadBoxId, inputId) {
    const uploadBox = document.getElementById(uploadBoxId);
    const input = document.getElementById(inputId);
    
    if (!uploadBox || !input) return;
    
    uploadBox.addEventListener('click', () => input.click());
    
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('drag-over');
    });
    
    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('drag-over');
    });
    
    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('drag-over');
        input.files = e.dataTransfer.files;
    });
}

setupDragDrop('imageUploadBox', 'imageInput');
setupDragDrop('videoUploadBox', 'videoInput');
setupDragDrop('batchUploadBox', 'batchInput');

// Image Analysis
document.getElementById('analyzeImageBtn').addEventListener('click', async () => {
    const input = document.getElementById('imageInput');
    const format = document.getElementById('imageFormat').value;
    const resultsArea = document.getElementById('imageResults');
    
    if (!input.files.length) {
        alert('Please select an image');
        return;
    }
    
    await analyzeImage(input.files[0], format, resultsArea);
});

// Video Analysis
document.getElementById('analyzeVideoBtn').addEventListener('click', async () => {
    const input = document.getElementById('videoInput');
    const maxFrames = document.getElementById('maxFrames').value;
    const fps = document.getElementById('videoFps').value;
    const format = document.getElementById('videoFormat').value;
    const resultsArea = document.getElementById('videoResults');
    
    if (!input.files.length) {
        alert('Please select a video');
        return;
    }
    
    await analyzeVideo(input.files[0], maxFrames, fps, format, resultsArea);
});

// Batch Analysis
document.getElementById('analyzeBatchBtn').addEventListener('click', async () => {
    const input = document.getElementById('batchInput');
    const type = document.getElementById('batchType').value;
    const format = document.getElementById('batchFormat').value;
    const resultsArea = document.getElementById('batchResults');
    
    if (!input.files.length) {
        alert('Please select files');
        return;
    }
    
    await batchAnalyze(input.files, type, format, resultsArea);
});

// Analyze Image Function
async function analyzeImage(file, format, resultsArea) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', format);
    
    resultsArea.innerHTML = '<div class="result-item"><div class="spinner"></div> Processing image...</div>';
    resultsArea.style.display = 'block';
    
    try {
        const response = await fetch('/api/analyze/image', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        displayImageResult(result, resultsArea);
    } catch (error) {
        resultsArea.innerHTML = `<div class="result-item error"><div class="result-content">Error: ${error.message}</div></div>`;
    }
}

// Analyze Video Function
async function analyzeVideo(file, maxFrames, fps, format, resultsArea) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('max_frames', maxFrames);
    formData.append('fps', fps);
    formData.append('format', format);
    
    resultsArea.innerHTML = '<div class="result-item"><div class="spinner"></div> Processing video (this may take a while)...</div>';
    resultsArea.style.display = 'block';
    
    try {
        const response = await fetch('/api/analyze/video', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        displayVideoResult(result, resultsArea);
    } catch (error) {
        resultsArea.innerHTML = `<div class="result-item error"><div class="result-content">Error: ${error.message}</div></div>`;
    }
}

// Batch Analyze Function
async function batchAnalyze(files, type, format, resultsArea) {
    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }
    formData.append('type', type);
    formData.append('format', format);
    
    resultsArea.innerHTML = `<div class="result-item"><div class="spinner"></div> Processing ${files.length} files...</div>`;
    resultsArea.style.display = 'block';
    
    try {
        const response = await fetch('/api/batch', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        displayBatchResults(result, resultsArea);
    } catch (error) {
        resultsArea.innerHTML = `<div class="result-item error"><div class="result-content">Error: ${error.message}</div></div>`;
    }
}

// Display Image Result
function displayImageResult(result, resultsArea) {
    if (result.status !== 'success') {
        resultsArea.innerHTML = `<div class="result-item error"><div class="result-title">✗ Error</div><div class="result-content">${result.error}</div></div>`;
        return;
    }
    
    let html = '<div class="result-item success">';
    html += `<div class="result-title">✓ Image Analysis Complete</div>`;
    
    // Caption
    if (result.caption) {
        html += `<div class="result-section">`;
        html += `<div class="result-section-title">📝 Caption</div>`;
        html += `<div class="result-content">${result.caption}</div>`;
        html += `</div>`;
    }
    
    // Objects
    if (result.objects && result.objects.length > 0) {
        html += `<div class="result-section">`;
        html += `<div class="result-section-title">🏷️ Detected Objects</div>`;
        html += `<ul class="object-list">`;
        result.objects.forEach(obj => {
            const confidence = (obj.confidence * 100).toFixed(1);
            html += `<li class="object-item"><span class="object-label">${obj.label}</span><span class="object-confidence">${confidence}%</span></li>`;
        });
        html += `</ul>`;
        html += `</div>`;
    }
    
    // Prompt
    if (result.prompt) {
        html += `<div class="result-section">`;
        html += `<div class="result-section-title">💬 Generated Prompt</div>`;
        html += `<div class="result-content">${result.prompt}</div>`;
        html += `</div>`;
    }
    
    html += '</div>';
    resultsArea.innerHTML = html;
}

// Display Video Result
function displayVideoResult(result, resultsArea) {
    if (result.status !== 'success') {
        resultsArea.innerHTML = `<div class="result-item error"><div class="result-title">✗ Error</div><div class="result-content">${result.error}</div></div>`;
        return;
    }
    
    let html = '<div class="result-item success">';
    html += `<div class="result-title">✓ Video Analysis Complete</div>`;
    
    // Summary
    if (result.summary) {
        html += `<div class="result-section">`;
        html += `<div class="result-section-title">📋 Summary</div>`;
        html += `<div class="result-content">`;
        html += `Frames Analyzed: ${result.summary.total_frames_analyzed}<br>`;
        html += `Most Common Scene: ${result.summary.most_common_caption}<br>`;
        html += `</div>`;
        html += `</div>`;
    }
    
    // Common Objects
    if (result.summary && result.summary.common_objects && result.summary.common_objects.length > 0) {
        html += `<div class="result-section">`;
        html += `<div class="result-section-title">🏷️ Common Objects</div>`;
        html += `<ul class="object-list">`;
        result.summary.common_objects.forEach(obj => {
            const confidence = (obj.avg_confidence * 100).toFixed(1);
            html += `<li class="object-item"><span class="object-label">${obj.label} (x${obj.frequency})</span><span class="object-confidence">${confidence}%</span></li>`;
        });
        html += `</ul>`;
        html += `</div>`;
    }
    
    // Prompt
    if (result.prompt) {
        html += `<div class="result-section">`;
        html += `<div class="result-section-title">💬 Generated Prompt</div>`;
        html += `<div class="result-content">${result.prompt}</div>`;
        html += `</div>`;
    }
    
    html += '</div>';
    resultsArea.innerHTML = html;
}

// Display Batch Results
function displayBatchResults(result, resultsArea) {
    let html = `<div class="result-item success"><div class="result-title">✓ Batch Processing Complete</div>`;
    html += `<div class="result-content">Processed ${result.results.length} files</div></div>`;
    
    result.results.forEach((item, index) => {
        if (item.status === 'success') {
            html += '<div class="result-item success">';
            html += `<div class="result-title">${index + 1}. ${item.file_name || item.video_path}</div>`;
            html += `<div class="result-section">`;
            html += `<div class="result-content">${item.caption || item.summary.most_common_caption}</div>`;
            html += `</div>`;
            html += '</div>';
        } else {
            html += '<div class="result-item error">';
            html += `<div class="result-title">${index + 1}. ${item.file}</div>`;
            html += `<div class="result-content">Error: ${item.error}</div>`;
            html += '</div>';
        }
    });
    
    resultsArea.innerHTML = html;
}
