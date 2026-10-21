// Picture Password Authentication System - Main JavaScript
// College Demonstration Project

// Global variables
let isProcessing = false;

// Document ready function
document.addEventListener('DOMContentLoaded', function () {
    console.log('Picture Password Authentication System loaded');

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Add loading states to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!isProcessing) {
                isProcessing = true;
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    const originalText = submitBtn.innerHTML;
                    submitBtn.innerHTML = '<span class="loading"></span> Processing...';
                    submitBtn.disabled = true;

                    // Re-enable after 10 seconds as fallback
                    setTimeout(function () {
                        submitBtn.innerHTML = originalText;
                        submitBtn.disabled = false;
                        isProcessing = false;
                    }, 10000);
                }
            }
        });
    });
});

// Utility Functions

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, error, warning, info)
 */
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Add to page
    document.body.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(function () {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} - True if valid email format
 */
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate form fields
 * @param {HTMLFormElement} form - Form to validate
 * @returns {boolean} - True if all fields are valid
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');

    requiredFields.forEach(function (field) {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }

        // Special validation for email fields
        if (field.type === 'email' && field.value.trim()) {
            if (!validateEmail(field.value.trim())) {
                field.classList.add('is-invalid');
                isValid = false;
            }
        }
    });

    return isValid;
}

/**
 * Format timestamp for display
 * @param {string} timestamp - ISO timestamp string
 * @returns {string} - Formatted date string
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

/**
 * Calculate distance between two points
 * @param {number} x1 - First point X coordinate
 * @param {number} y1 - First point Y coordinate
 * @param {number} x2 - Second point X coordinate
 * @param {number} y2 - Second point Y coordinate
 * @returns {number} - Distance in pixels
 */
function calculateDistance(x1, y1, x2, y2) {
    return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
}

/**
 * Debounce function to limit function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} - Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Picture Password Specific Functions

/**
 * Handle image click events for picture password setup
 * @param {Event} event - Click event
 * @param {HTMLImageElement} image - Image element that was clicked
 */
function handleImageClick(event, image) {
    if (isProcessing) return;

    const rect = image.getBoundingClientRect();
    const x = Math.round(event.clientX - rect.left);
    const y = Math.round(event.clientY - rect.top);

    // Ensure coordinates are within image bounds
    if (x < 0 || y < 0 || x > image.width || y > image.height) {
        showToast('Please click within the image bounds', 'warning');
        return;
    }

    return { x, y };
}

/**
 * Create visual feedback for click location
 * @param {HTMLElement} container - Container element for the marker
 * @param {number} x - X coordinate
 * @param {number} y - Y coordinate
 */
function createClickMarker(container, x, y) {
    // Remove existing marker
    const existingMarker = container.querySelector('.click-marker');
    if (existingMarker) {
        existingMarker.remove();
    }

    // Create new marker
    const marker = document.createElement('div');
    marker.className = 'click-marker';
    marker.style.left = (x - 10) + 'px';
    marker.style.top = (y - 10) + 'px';

    container.appendChild(marker);
}

/**
 * Start countdown timer
 * @param {number} seconds - Initial seconds
 * @param {HTMLElement} display - Element to display countdown
 * @param {Function} onComplete - Callback when timer reaches 0
 * @returns {number} - Interval ID
 */
function startCountdown(seconds, display, onComplete) {
    let timeLeft = seconds;
    display.textContent = timeLeft;

    const interval = setInterval(function () {
        timeLeft--;
        display.textContent = timeLeft;

        // Change color as time runs out
        if (timeLeft <= 3) {
            display.style.color = '#dc3545'; // Red
        } else if (timeLeft <= 5) {
            display.style.color = '#ffc107'; // Yellow
        }

        if (timeLeft <= 0) {
            clearInterval(interval);
            if (onComplete) {
                onComplete();
            }
        }
    }, 1000);

    return interval;
}

/**
 * Handle AJAX requests with error handling
 * @param {string} url - Request URL
 * @param {Object} options - Fetch options
 * @returns {Promise} - Fetch promise with error handling
 */
async function makeRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Request failed:', error);
        showToast('Network error. Please try again.', 'error');
        throw error;
    }
}

// Event Listeners for common elements

// Add click handlers for images with data-clickable attribute
document.addEventListener('click', function (e) {
    if (e.target.hasAttribute('data-clickable')) {
        const coordinates = handleImageClick(e, e.target);
        if (coordinates) {
            console.log('Image clicked at:', coordinates);
        }
    }
});

// Add form validation on submit
document.addEventListener('submit', function (e) {
    const form = e.target;
    if (form.hasAttribute('data-validate')) {
        if (!validateForm(form)) {
            e.preventDefault();
            showToast('Please fill in all required fields correctly', 'error');
        }
    }
});

// Handle escape key to close modals
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(function (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }
});

// Console log for debugging (remove in production)
console.log('Picture Password Authentication System - JavaScript loaded successfully');

