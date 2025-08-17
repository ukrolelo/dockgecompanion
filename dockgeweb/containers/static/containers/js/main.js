// Main JavaScript for Dockge Companion Web

document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const html = document.documentElement;
    
    // Load saved theme or default to dark
    const savedTheme = localStorage.getItem('theme') || 'dark';
    html.setAttribute('data-bs-theme', savedTheme);
    updateThemeIcon(savedTheme);
    
    themeToggle.addEventListener('click', function() {
        const currentTheme = html.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        html.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
    
    function updateThemeIcon(theme) {
        themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
    
    // Auto-refresh functionality
    let autoRefreshInterval;
    const autoRefreshButton = document.getElementById('auto-refresh-toggle');
    
    if (autoRefreshButton) {
        autoRefreshButton.addEventListener('click', function() {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
                this.innerHTML = '<i class="fas fa-play me-1"></i>Start Auto-refresh';
                this.classList.remove('btn-success');
                this.classList.add('btn-outline-success');
            } else {
                startAutoRefresh();
                this.innerHTML = '<i class="fas fa-pause me-1"></i>Stop Auto-refresh';
                this.classList.remove('btn-outline-success');
                this.classList.add('btn-success');
            }
        });
    }
    
    function startAutoRefresh() {
        autoRefreshInterval = setInterval(function() {
            if (typeof refreshContainerStatus === 'function') {
                refreshContainerStatus();
            }
        }, 30000); // Refresh every 30 seconds
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Utility functions
function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alert-container');
    const alertId = 'alert-' + Date.now();
    
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert" id="${alertId}">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    alertContainer.insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, duration);
    }
}

function showLoading(text = 'Loading...') {
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    document.getElementById('loading-text').textContent = text;
    loadingModal.show();
}

function hideLoading() {
    const loadingModal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
    if (loadingModal) {
        loadingModal.hide();
    }
}

// AJAX helper function
async function makeRequest(url, options = {}) {
    console.log('makeRequest called:', url, options);

    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };

    // Add CSRF token for POST requests (if available)
    if (options.method === 'POST') {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken && csrfToken.value) {
            defaultOptions.headers['X-CSRFToken'] = csrfToken.value;
            console.log('CSRF token found and added');
        } else {
            console.log('No CSRF token found (this is OK for @csrf_exempt endpoints)');
        }
    }

    const finalOptions = { ...defaultOptions, ...options };
    console.log('Final request options:', finalOptions);

    try {
        console.log('Making fetch request...');
        const response = await fetch(url, finalOptions);
        console.log('Response received:', response.status, response.statusText);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        console.log('Parsing JSON...');
        const data = await response.json();
        console.log('JSON data parsed successfully:', data);
        return data;

    } catch (error) {
        console.error('Request failed:', error);
        throw error;
    }
}

// Container management functions
async function scanContainers() {
    console.log('scanContainers() called');
    showLoading('Scanning containers...');

    try {
        console.log('About to make request to /api/scan/');
        const data = await makeRequest('/api/scan/', { method: 'POST' });
        console.log('Scan response received:', data);

        hideLoading();

        if (data && data.success) {
            showAlert(`Scan completed! ${data.containers_scanned} containers scanned, ${data.changes_detected} changes detected.`, 'success');
            // Refresh the page data
            if (typeof refreshContainerStatus === 'function') {
                refreshContainerStatus();
            }
        } else {
            showAlert('Scan failed: ' + (data ? data.error : 'Unknown error'), 'danger');
        }
    } catch (error) {
        console.error('Scan request failed:', error);
        hideLoading();
        showAlert('Scan request failed: ' + error.message, 'danger');
    }
}

function checkUpdates() {
    showLoading('Checking for updates...');
    
    makeRequest('/api/check-updates/', { method: 'POST' })
        .then(data => {
            hideLoading();
            if (data.success) {
                const message = `Update check completed! ${data.updates_available} of ${data.total_containers} containers have updates available.`;
                showAlert(message, data.updates_available > 0 ? 'warning' : 'success');
                // Refresh the page data
                if (typeof refreshContainerStatus === 'function') {
                    refreshContainerStatus();
                }
            } else {
                showAlert('Update check failed: ' + data.error, 'danger');
            }
        })
        .catch(() => {
            hideLoading();
        });
}

// Format date/time according to user preference (DD.MM.YYYY HH:MM)
function formatDateTime(dateString) {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${day}.${month}.${year} ${hours}:${minutes}`;
}

// Copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showAlert('Copied to clipboard!', 'success', 2000);
    }, function(err) {
        console.error('Could not copy text: ', err);
        showAlert('Failed to copy to clipboard', 'danger', 3000);
    });
}

// Generate Docker Hub URL for a specific digest
function getDockerHubUrl(imageName, digest) {
    if (!imageName || !digest) {
        return `https://hub.docker.com/search?q=${encodeURIComponent(imageName || '')}`;
    }

    // Handle different image name formats
    let namespace, repo;

    if (!imageName.includes('/')) {
        // Official images (e.g., 'python' -> 'library/python')
        namespace = 'library';
        repo = imageName;
    } else if (imageName.split('/').length === 2) {
        // User/org images (e.g., 'louislam/dockge')
        [namespace, repo] = imageName.split('/');
    } else {
        // Registry images or complex paths - use search instead
        return `https://hub.docker.com/search?q=${encodeURIComponent(imageName)}`;
    }

    // Clean the digest (remove sha256: prefix if present)
    const cleanDigest = digest.startsWith('sha256:') ? digest.substring(7) : digest;

    // Try the layers URL format first
    return `https://hub.docker.com/layers/${namespace}/${repo}/latest/images/sha256-${cleanDigest}`;
}

// Open Docker Hub page for a specific digest
function openDockerHub(imageName, digest) {
    const url = getDockerHubUrl(imageName, digest);
    window.open(url, '_blank');
}
