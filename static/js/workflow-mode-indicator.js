/**
 * Workflow Mode Indicator
 * 
 * This script updates the workflow mode indicator in the navigation bar.
 * It polls the server for the current workflow mode and updates the indicator accordingly.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get the workflow mode indicator elements
    const indicator = document.getElementById('workflow-mode-indicator');
    const text = document.getElementById('workflow-mode-text');
    
    if (!indicator || !text) {
        console.error('Workflow mode indicator elements not found');
        return;
    }
    
    // Function to update the indicator
    function updateWorkflowModeIndicator() {
        fetch('/api/workflow-mode')
            .then(response => response.json())
            .then(data => {
                // Update the indicator text
                text.textContent = data.is_auto ? 'Auto Mode' : 'Manual Mode';
                
                // Update the indicator color
                if (data.is_auto) {
                    indicator.classList.remove('bg-primary');
                    indicator.classList.add('bg-success');
                } else {
                    indicator.classList.remove('bg-success');
                    indicator.classList.add('bg-primary');
                }
            })
            .catch(error => {
                console.error('Error fetching workflow mode:', error);
                text.textContent = 'Error';
                indicator.classList.remove('bg-success', 'bg-primary');
                indicator.classList.add('bg-danger');
            });
    }
    
    // Update the indicator immediately
    updateWorkflowModeIndicator();
    
    // Update the indicator every 5 seconds
    setInterval(updateWorkflowModeIndicator, 5000);
    
    // Also update when the page becomes visible again
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            updateWorkflowModeIndicator();
        }
    });
});
