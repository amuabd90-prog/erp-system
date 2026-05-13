// Comprehensive Alert System for Business Management System

class AlertSystem {
    constructor() {
        this.init();
    }

    init() {
        this.setupFormValidation();
        this.setupDuplicatePrevention();
        this.setupBankAccountValidation();
        this.setupNumericValidation();
        this.setupDeleteConfirmations();
        this.setupSuccessMessages();
    }

    // Show alert message
    showAlert(message, type = 'info', duration = 5000) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 500px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        `;
        
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    }

    // Show error with field highlighting
    showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.add('is-invalid');
            field.style.borderColor = '#dc3545';
            field.style.boxShadow = '0 0 0 0.2rem rgba(220, 53, 69, 0.25)';
            
            // Show error message
            let feedback = field.parentNode.querySelector('.invalid-feedback');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                field.parentNode.appendChild(feedback);
            }
            feedback.textContent = message;
            
            // Remove error on input
            field.addEventListener('input', () => {
                field.classList.remove('is-invalid');
                field.style.borderColor = '';
                field.style.boxShadow = '';
                if (feedback) {
                    feedback.textContent = '';
                }
            }, { once: true });
        }
        
        this.showAlert(message, 'danger');
    }

    // Setup form validation
    setupFormValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const requiredFields = form.querySelectorAll('[required]');
                let hasErrors = false;

                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        this.showFieldError(field.id || field.name, `${field.name || field.id} is required`);
                        hasErrors = true;
                    }
                });

                if (hasErrors) {
                    e.preventDefault();
                    this.showAlert('Please fill in all required fields', 'warning');
                }
            });
        });
    }

    // Setup duplicate prevention
    setupDuplicatePrevention() {
        // Stock In duplicate check
        const stockInInvNo = document.getElementById('inventory_no');
        if (stockInInvNo) {
            stockInInvNo.addEventListener('blur', async () => {
                const value = stockInInvNo.value.trim();
                if (value) {
                    try {
                        const response = await fetch(`/api/check-duplicate/stock-in/${value}`);
                        const isDuplicate = await response.json();
                        
                        if (isDuplicate) {
                            this.showFieldError('inventory_no', 'Inventory No already exists in Stock In');
                            stockInInvNo.focus();
                        }
                    } catch (error) {
                        console.error('Duplicate check failed:', error);
                    }
                }
            });
        }

        // Sales duplicate check
        const salesProductId = document.getElementById('product_id');
        if (salesProductId) {
            salesProductId.addEventListener('blur', async () => {
                const value = salesProductId.value.trim();
                if (value) {
                    try {
                        const response = await fetch(`/api/check-duplicate/sales/${value}`);
                        const isDuplicate = await response.json();
                        
                        if (isDuplicate) {
                            this.showFieldError('product_id', 'Product ID already exists in Sales');
                            salesProductId.focus();
                        }
                    } catch (error) {
                        console.error('Duplicate check failed:', error);
                    }
                }
            });
        }
    }

    // Setup bank account validation
    setupBankAccountValidation() {
        const bankAccountFields = document.querySelectorAll('input[name*="account"], input[id*="account"]');
        
        bankAccountFields.forEach(field => {
            field.addEventListener('blur', () => {
                const accountNumber = field.value.trim();
                if (accountNumber) {
                    const nonReceiptAccounts = [
                        '1000084206087', '57861258', '1014657935101', '08804884936001',
                        '0001883620101', '1000564090001', '5038523396011', '01320927866200',
                        '01320927862269', '0911190064'
                    ];
                    
                    if (nonReceiptAccounts.includes(accountNumber)) {
                        this.showAlert(`Warning: Account ${accountNumber} is marked as non-receipt account`, 'warning', 8000);
                        field.style.borderColor = '#ffc107';
                        field.style.boxShadow = '0 0 0 0.2rem rgba(255, 193, 7, 0.25)';
                    }
                }
            });
        });
    }

    // Setup numeric validation
    setupNumericValidation() {
        const numericFields = document.querySelectorAll('input[type="number"], input[name*="price"], input[name*="amount"], input[name*="pieces"], input[name*="quantity"]');
        
        numericFields.forEach(field => {
            field.addEventListener('input', () => {
                const value = parseFloat(field.value);
                const fieldName = field.name || field.id;
                
                if (isNaN(value)) {
                    this.showFieldError(field.id || field.name, `${fieldName} must be a valid number`);
                    return;
                }
                
                if (value < 0) {
                    this.showFieldError(field.id || field.name, `${fieldName} cannot be negative`);
                    return;
                }
                
                // Format to 2 decimal places for price/amount fields
                if (fieldName.includes('price') || fieldName.includes('amount')) {
                    field.value = value.toFixed(2);
                }
                
                // Ensure positive for quantity/pieces
                if ((fieldName.includes('quantity') || fieldName.includes('pieces')) && value <= 0) {
                    this.showFieldError(field.id || field.name, `${fieldName} must be positive`);
                }
            });
        });
    }

    // Setup delete confirmations
    setupDeleteConfirmations() {
        const deleteButtons = document.querySelectorAll('button[type="submit"][formmethod="post"]');
        
        deleteButtons.forEach(button => {
            const form = button.closest('form');
            if (form && (form.action.includes('/delete') || button.textContent.includes('Delete'))) {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    
                    const itemName = button.getAttribute('data-item-name') || 'this item';
                    const confirmMessage = `Are you sure you want to delete ${itemName}? This action cannot be undone.`;
                    
                    if (confirm(confirmMessage)) {
                        // Check for dependencies
                        this.checkDependencies(form.action).then(hasDependencies => {
                            if (hasDependencies) {
                                const proceed = confirm('Warning: This item has dependent records. Deleting it may affect other data. Proceed anyway?');
                                if (proceed) {
                                    form.submit();
                                }
                            } else {
                                form.submit();
                            }
                        });
                    }
                });
            }
        });
    }

    // Check for dependencies before deletion
    async checkDependencies(deleteUrl) {
        try {
            const response = await fetch(`/api/check-dependencies?url=${encodeURIComponent(deleteUrl)}`);
            return await response.json();
        } catch (error) {
            console.error('Dependency check failed:', error);
            return false;
        }
    }

    // Setup success messages
    setupSuccessMessages() {
        // Auto-hide success messages after 3 seconds
        const successAlerts = document.querySelectorAll('.alert-success');
        successAlerts.forEach(alert => {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }, 3000);
        });
    }

    // Show status mismatch alerts
    checkStatusMismatch(status1, status2, fieldName1, fieldName2) {
        if (status1 !== status2) {
            this.showAlert(
                `Status mismatch detected: ${fieldName1} (${status1}) != ${fieldName2} (${status2})`,
                'warning',
                8000
            );
            return true;
        }
        return false;
    }

    // Validate date range
    validateDateRange(startDateField, endDateField) {
        const start = new Date(startDateField.value);
        const end = new Date(endDateField.value);
        
        if (start > end) {
            this.showFieldError(endDateField.id, 'End date cannot be before start date');
            this.showAlert('End date cannot be before start date', 'warning');
            return false;
        }
        return true;
    }
}

// Initialize alert system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.alertSystem = new AlertSystem();
    
    // Show flash messages as alerts
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        const type = msg.classList.contains('error') ? 'danger' : 
                    msg.classList.contains('warning') ? 'warning' :
                    msg.classList.contains('success') ? 'success' : 'info';
        
        window.alertSystem.showAlert(msg.textContent, type);
        msg.remove();
    });
});

// Export for use in other scripts
window.AlertSystem = AlertSystem;
