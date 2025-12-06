// Main JavaScript for NYU Study Space Status App

document.addEventListener('DOMContentLoaded', function() {
    console.log('NYU Study Space Status App Loaded');
    
    // Example: Fetch and update study space data via API
    function updateSpaceStatus() {
        fetch('/api/spaces')
            .then(response => response.json())
            .then(data => {
                console.log('Study space data:', data);
                // Update UI with fresh data if needed
            })
            .catch(error => {
                console.error('Error fetching study space data:', error);
            });
    }
    
    // Uncomment to enable periodic API updates
    // setInterval(updateSpaceStatus, 30000);
});
