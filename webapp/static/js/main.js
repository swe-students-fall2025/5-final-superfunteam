// Main JavaScript for NYU Printer Status App

document.addEventListener('DOMContentLoaded', function() {
    console.log('NYU Printer Status App Loaded');
    
    // Add any additional interactive features here
    
    // Example: Fetch and update printer data via API
    function updatePrinterStatus() {
        fetch('/api/printers')
            .then(response => response.json())
            .then(data => {
                console.log('Printer data:', data);
                // Update UI with fresh data if needed
            })
            .catch(error => {
                console.error('Error fetching printer data:', error);
            });
    }
    
    // Uncomment to enable periodic API updates
    // setInterval(updatePrinterStatus, 30000);
});
