document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const startCameraBtn = document.getElementById('startCameraBtn');
    const stopCameraBtn = document.getElementById('stopCameraBtn');
    const refreshStreamBtn = document.getElementById('refreshStreamBtn');
    const useDroidcamCheckbox = document.getElementById('useDroidcam');
    const statusText = document.getElementById('statusText');
    const statusIcon = document.getElementById('statusIcon');
    const connectionStatus = document.getElementById('connectionStatus');
    const connectionIcon = document.getElementById('connectionIcon');
    const videoFeed = document.getElementById('videoFeed');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorNotification = document.getElementById('errorNotification');
    const errorMessage = document.getElementById('errorMessage');
    const dismissError = document.getElementById('dismissError');
    
    // Detection elements
    const objectDetections = document.getElementById('objectDetections');
    const faceRecognitions = document.getElementById('faceRecognitions');
    const alertsList = document.getElementById('alertsList');
    const objectCount = document.getElementById('objectCount');
    const faceCount = document.getElementById('faceCount');
    const alertCount = document.getElementById('alertCount');
    
    // Filter elements
    const objectFilterSelect = document.getElementById('objectFilterSelect');
    const faceFilterSelect = document.getElementById('faceFilterSelect');
    
    // Clear buttons
    const clearObjectsBtn = document.getElementById('clearObjectsBtn');
    const clearFacesBtn = document.getElementById('clearFacesBtn');
    const clearAlertsBtn = document.getElementById('clearAlertsBtn');
    
    // Modal elements
    const confirmationModal = document.getElementById('confirmationModal');
    const confirmTitle = document.getElementById('confirmTitle');
    const confirmMessage = document.getElementById('confirmMessage');
    const confirmCancel = document.getElementById('confirmCancel');
    const confirmOk = document.getElementById('confirmOk');
    
    // Variables
    let pollingInterval = null;
    let isRunning = false;
    let streamFailCount = 0;
    let currentObjectData = [];
    let currentFaceData = [];
    let currentAlerts = [];
    
    // Functions
    function updateStatus(status, isError = false) {
        statusText.textContent = status;
        statusIcon.className = 'status-icon';
        if (isError) {
            statusIcon.classList.add('error');
        } else if (status !== 'Idle') {
            statusIcon.classList.add('active');
        }
    }
    
    function updateConnectionStatus(status) {
        connectionStatus.textContent = status;
        connectionIcon.className = 'status-icon';
        
        switch (status) {
            case 'Connected':
                connectionIcon.classList.add('connected');
                break;
            case 'Connecting':
                connectionIcon.classList.add('connecting');
                break;
            case 'Disconnected':
                connectionIcon.classList.add('disconnected');
                break;
            case 'Error':
                connectionIcon.classList.add('error');
                break;
        }
    }
    
    function showError(message, timeout = 0) {
        errorMessage.textContent = message;
        errorNotification.hidden = false;
        
        if (timeout > 0) {
            setTimeout(() => {
                errorNotification.hidden = true;
            }, timeout);
        }
    }
    
    function showConfirmation(title, message, onConfirm) {
        confirmTitle.textContent = title;
        confirmMessage.textContent = message;
        confirmationModal.hidden = false;
        
        // Store the confirm action
        confirmOk.onclick = function() {
            confirmationModal.hidden = true;
            if (onConfirm) onConfirm();
        };
        
        confirmCancel.onclick = function() {
            confirmationModal.hidden = true;
        };
    }
    
    function startCamera() {
        const useDroidcam = useDroidcamCheckbox.checked;
        
        // Show loading indicator
        loadingIndicator.hidden = false;
        updateConnectionStatus('Connecting');
        
        fetch('/start_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ use_droidcam: useDroidcam })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            loadingIndicator.hidden = true;
            
            if (data.status === 'Camera started successfully') {
                isRunning = true;
                streamFailCount = 0;
                updateStatus('Running');
                updateConnectionStatus('Connected');
                startCameraBtn.disabled = true;
                stopCameraBtn.disabled = false;
                refreshStreamBtn.disabled = false;
                
                // Add timestamp to prevent caching
                videoFeed.src = '/video_feed?' + new Date().getTime();
                
                // Start polling for detections
                startPolling();
            } else {
                updateStatus('Error', true);
                updateConnectionStatus('Error');
                showError(`Failed to start camera: ${data.message || 'Unknown error'}`);
            }
        })
        .catch(error => {
            loadingIndicator.hidden = true;
            console.error('Error:', error);
            updateStatus('Error', true);
            updateConnectionStatus('Error');
            showError(`Connection failed: ${error.message}`);
        });
    }
    
    function stopCamera() {
        showConfirmation('Stop Camera', 'Are you sure you want to stop the camera?', function() {
            updateConnectionStatus('Disconnecting');
            
            fetch('/stop_camera', {
                method: 'POST'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'Camera stopped successfully') {
                    isRunning = false;
                    updateStatus('Idle');
                    updateConnectionStatus('Disconnected');
                    startCameraBtn.disabled = false;
                    stopCameraBtn.disabled = true;
                    refreshStreamBtn.disabled = true;
                    videoFeed.src = '/static/img/video-placeholder.jpg';
                    
                    // Stop polling
                    stopPolling();
                } else {
                    updateStatus('Error', true);
                    showError(`Failed to stop camera: ${data.message || 'Unknown error'}`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                updateStatus('Error', true);
                showError(`Connection failed: ${error.message}`);
            });
        });
    }
    
    function refreshStream() {
        if (!isRunning) return;
        
        // Add timestamp to prevent caching
        videoFeed.src = '/video_feed?' + new Date().getTime();
        streamFailCount = 0;
        updateConnectionStatus('Connected');
    }
    
    function startPolling() {
        // Clear any existing interval
        stopPolling();
        
        // Poll for detections every 1 second
        pollingInterval = setInterval(fetchDetections, 1000);
    }
    
    function stopPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }
    
    function fetchDetections() {
        fetch('/get_recent_detections')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Reset error counters on successful fetch
                streamFailCount = 0;
                
                if (!data.camera_running && isRunning) {
                    // Camera stopped unexpectedly
                    isRunning = false;
                    updateStatus('Error', true);
                    updateConnectionStatus('Disconnected');
                    startCameraBtn.disabled = false;
                    stopCameraBtn.disabled = true;
                    refreshStreamBtn.disabled = true;
                    videoFeed.src = '/static/img/video-placeholder.jpg';
                    stopPolling();
                    showError('Camera stopped unexpectedly. Check the connection.');
                    return;
                }
                
                // Update object detections
                if (data.objects && data.objects.length > 0) {
                    currentObjectData = data.objects;
                    updateObjectDetections(currentObjectData);
                }
                
                // Update face recognitions  
                if (data.faces && data.faces.length > 0) {
                    currentFaceData = data.faces;
                    updateFaceRecognitions(currentFaceData);
                }
            })
            .catch(error => {
                console.error('Error fetching detections:', error);
                streamFailCount++;
                
                // After 5 consecutive failures, show error
                if (streamFailCount >= 5) {
                    updateConnectionStatus('Error');
                    showError('Connection to server lost. Try refreshing the stream.');
                }
            });
    }
    
    function updateObjectDetections(objects, filter = 'all') {
        // Sort by timestamp, newest first
        objects.sort((a, b) => b.timestamp - a.timestamp);
        
        // Clear existing list
        objectDetections.innerHTML = '';
        
        // Filter objects if needed
        let filteredObjects = objects;
        if (filter !== 'all') {
            filteredObjects = objects.filter(item => {
                return item.objects.some(obj => {
                    switch(filter) {
                        case 'person': return obj.label === 'person';
                        case 'vehicle': return ['car', 'truck', 'bus', 'motorcycle'].includes(obj.label);
                        case 'animal': return ['dog', 'cat', 'bird', 'horse'].includes(obj.label);
                        default: return true;
                    }
                });
            });
        }
        
        // Update counter
        objectCount.textContent = filteredObjects.reduce((count, item) => count + item.objects.length, 0);
        
        // Group objects by timestamp
        const groupedObjects = {};
        filteredObjects.forEach(item => {
            const timestamp = new Date(item.timestamp * 1000).toLocaleTimeString();
            if (!groupedObjects[timestamp]) {
                groupedObjects[timestamp] = [];
            }
            
            // Add each object detection to the group
            item.objects.forEach(obj => {
                if (filter === 'all' || 
                   (filter === 'person' && obj.label === 'person') ||
                   (filter === 'vehicle' && ['car', 'truck', 'bus', 'motorcycle'].includes(obj.label)) ||
                   (filter === 'animal' && ['dog', 'cat', 'bird', 'horse'].includes(obj.label))) {
                    
                    groupedObjects[timestamp].push(obj);
                    
                    // Add to alerts if it's a person and not already there
                    if (obj.label === 'person') {
                        const alertExists = currentAlerts.some(alert => 
                            alert.title === 'Person Detected' && 
                            alert.time === timestamp
                        );
                        
                        if (!alertExists) {
                            addAlert(
                                'Person Detected', 
                                `Person detected with confidence ${(obj.confidence * 100).toFixed(1)}%`, 
                                timestamp
                            );
                        }
                    }
                }
            });
        });
        
        // Create HTML elements for each group
        for (const [timestamp, detections] of Object.entries(groupedObjects)) {
            const detectionGroup = document.createElement('div');
            detectionGroup.className = 'detection-item';
            
            const timeElement = document.createElement('div');
            timeElement.className = 'detection-time';
            timeElement.textContent = timestamp;
            detectionGroup.appendChild(timeElement);
            
            detections.forEach(obj => {
                const objectElement = document.createElement('div');
                objectElement.className = 'detection-object';
                objectElement.innerHTML = `
                    <span class="detection-name">${obj.label}</span>
                    <span class="detection-confidence">${(obj.confidence * 100).toFixed(1)}%</span>
                `;
                detectionGroup.appendChild(objectElement);
            });
            
            objectDetections.appendChild(detectionGroup);
        }
        
        // Show message if no detections
        if (objectDetections.children.length === 0) {
            const noData = document.createElement('div');
            noData.className = 'no-data';
            noData.textContent = 'No object detections';
            objectDetections.appendChild(noData);
        }
    }
    
    function updateFaceRecognitions(faces, filter = 'all') {
        // Sort by timestamp, newest first
        faces.sort((a, b) => b.timestamp - a.timestamp);
        
        // Clear existing list
        faceRecognitions.innerHTML = '';
        
        // Filter faces if needed
        let filteredFaces = faces;
        if (filter !== 'all') {
            filteredFaces = faces.filter(item => {
                if (filter === 'known') return item.face.name !== 'Unknown';
                if (filter === 'unknown') return item.face.name === 'Unknown';
                return true;
            });
        }
        
        // Update counter
        faceCount.textContent = filteredFaces.length;
        
        // Display faces
        filteredFaces.forEach(item => {
            const face = item.face;
            const timestamp = new Date(item.timestamp * 1000).toLocaleTimeString();
            
            const faceElement = document.createElement('div');
            faceElement.className = 'detection-item';
            
            // Add confidence if available
            const confidenceText = face.confidence ? 
                `<span class="detection-confidence">${(face.confidence * 100).toFixed(1)}%</span>` : '';
            
            faceElement.innerHTML = `
                <div class="detection-time">${timestamp}</div>
                <div class="detection-face">
                    <span class="detection-name ${face.name === 'Unknown' ? 'unknown-face' : 'known-face'}">${face.name}</span>
                    ${confidenceText}
                </div>
            `;
            
            faceRecognitions.appendChild(faceElement);
            
            // Add to alerts if not already there
            const alertExists = currentAlerts.some(alert => 
                (face.name === 'Unknown' ? 
                    alert.title === 'Unknown Face' : 
                    alert.title === 'Face Recognized' && alert.message.includes(face.name)) && 
                alert.time === timestamp
            );
            
            if (!alertExists) {
                if (face.name === 'Unknown') {
                    addAlert('Unknown Face', 'An unknown face was detected', timestamp);
                } else {
                    addAlert('Face Recognized', `${face.name} was recognized`, timestamp);
                }
            }
        });
        
        // Show message if no faces
        if (faceRecognitions.children.length === 0) {
            const noData = document.createElement('div');
            noData.className = 'no-data';
            noData.textContent = 'No face recognitions';
            faceRecognitions.appendChild(noData);
        }
    }
    
    function addAlert(title, message, time) {
        // Create alert object
        const alertObj = { title, message, time };
        currentAlerts.push(alertObj);
        
        // Update counter
        alertCount.textContent = currentAlerts.length;
        
        const alertElement = document.createElement('div');
        alertElement.className = 'alert-item';
        
        // Choose icon based on alert type
        let icon = 'exclamation-triangle';
        if (title.includes('Person')) icon = 'user';
        else if (title.includes('Face')) icon = 'user-circle';
        
        alertElement.innerHTML = `
            <div class="alert-icon">
                <i class="fas fa-${icon}"></i>
            </div>
            <div class="alert-content">
                <div class="alert-title">${title}</div>
                <div class="alert-message">${message}</div>
                <div class="alert-time">${time}</div>
            </div>
        `;
        
        // Add to beginning of list
        if (alertsList.firstChild) {
            alertsList.insertBefore(alertElement, alertsList.firstChild);
        } else {
            alertsList.appendChild(alertElement);
        }
        
        // Limit the number of alerts shown
        while (alertsList.children.length > 15) {
            alertsList.removeChild(alertsList.lastChild);
            currentAlerts.pop();
        }
    }
    
    // Video feed error handling
    videoFeed.addEventListener('error', function(e) {
        console.error('Video feed error:', e);
        if (isRunning) {
            streamFailCount++;
            
            if (streamFailCount > 3) {
                updateConnectionStatus('Error');
                showError('Video stream disconnected. Try refreshing the stream.', 5000);
            }
        }
    });
    
    videoFeed.addEventListener('load', function() {
        if (isRunning) {
            streamFailCount = 0;
            updateConnectionStatus('Connected');
        }
    });
    
    // Event Listeners
    startCameraBtn.addEventListener('click', startCamera);
    stopCameraBtn.addEventListener('click', stopCamera);
    refreshStreamBtn.addEventListener('click', refreshStream);
    dismissError.addEventListener('click', () => errorNotification.hidden = true);
    
    // Filter event listeners
    objectFilterSelect.addEventListener('change', function() {
        updateObjectDetections(currentObjectData, this.value);
    });
    
    faceFilterSelect.addEventListener('change', function() {
        updateFaceRecognitions(currentFaceData, this.value);
    });
    
    // Clear button event listeners
    clearObjectsBtn.addEventListener('click', function() {
        showConfirmation('Clear Objects', 'Are you sure you want to clear all object detections?', function() {
            currentObjectData = [];
            objectDetections.innerHTML = '';
            objectCount.textContent = '0';
        });
    });
    
    clearFacesBtn.addEventListener('click', function() {
        showConfirmation('Clear Faces', 'Are you sure you want to clear all face recognitions?', function() {
            currentFaceData = [];
            faceRecognitions.innerHTML = '';
            faceCount.textContent = '0';
        });
    });
    
    clearAlertsBtn.addEventListener('click', function() {
        showConfirmation('Clear Alerts', 'Are you sure you want to clear all alerts?', function() {
            currentAlerts = [];
            alertsList.innerHTML = '';
            alertCount.textContent = '0';
        });
    });
    
    // Initialize status
    updateStatus('Idle');
    updateConnectionStatus('Disconnected');
});