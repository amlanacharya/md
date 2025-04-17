// Real-time updates for loan application status
document.addEventListener('DOMContentLoaded', function() {
    // Function to check for updates
    function checkForUpdates() {
        // Get the current page's loan IDs
        const loanRows = document.querySelectorAll('.clickable-row');
        if (loanRows.length === 0) return;

        const loanIds = Array.from(loanRows).map(row => row.dataset.loanId);

        // Make an AJAX request to check for updates
        fetch('/api/check-updates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({ loan_ids: loanIds })
        })
        .then(response => response.json())
        .then(data => {
            if (data.updates) {
                // Update the UI with new status information
                data.updates.forEach(update => {
                    const row = document.querySelector(`.clickable-row[data-loan-id="${update.id}"]`);
                    if (row) {
                        // Update status badge
                        const statusCell = row.querySelector('td:nth-child(7)');
                        if (statusCell) {
                            let badgeClass = 'bg-draft';
                            let statusText = 'Draft';
                            let textClass = '';

                            switch (update.status) {
                                case 'pending_checker':
                                    badgeClass = 'bg-pending-checker';
                                    textClass = 'text-dark';
                                    statusText = 'Pending Checker';
                                    break;
                                case 'pending_author':
                                    badgeClass = 'bg-pending-author';
                                    textClass = 'text-dark';
                                    statusText = 'Pending Author';
                                    break;
                                case 'approved':
                                    badgeClass = 'bg-approved';
                                    statusText = 'Approved';
                                    break;
                                case 'rejected':
                                    badgeClass = 'bg-rejected';
                                    statusText = 'Rejected';
                                    break;
                            }

                            statusCell.innerHTML = `<span class="badge ${badgeClass} ${textClass}">${statusText}</span>`;

                            // Highlight the row to indicate an update
                            row.classList.add('bg-light-yellow');
                            setTimeout(() => {
                                row.classList.remove('bg-light-yellow');
                            }, 3000);
                        }
                    }
                });

                // Show notification
                if (data.updates.length > 0) {
                    showNotification(`${data.updates.length} loan application(s) updated`);
                }
            }
        })
        .catch(error => console.error('Error checking for updates:', error));
    }

    // Function to show notification
    function showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'toast align-items-center text-white border-0';
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'assertive');
        notification.setAttribute('aria-atomic', 'true');

        notification.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-info-circle me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
        }

        document.getElementById('toast-container').appendChild(notification);
        const toast = new bootstrap.Toast(notification);
        toast.show();
    }

    // Check for updates every 30 seconds
    setInterval(checkForUpdates, 30000);

    // Initial check for updates when page loads
    setTimeout(checkForUpdates, 1000);
});
