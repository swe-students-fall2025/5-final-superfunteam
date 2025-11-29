// Admin Panel JavaScript

const API_BASE = '/api';

// Load all printers on page load
document.addEventListener('DOMContentLoaded', () => {
    loadPrinters();
});

// Add new printer
document.getElementById('addPrinterForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const printerData = {
        name: document.getElementById('printerName').value,
        location: document.getElementById('printerLocation').value,
        building: document.getElementById('printerBuilding').value,
        floor: document.getElementById('printerFloor').value
    };
    
    try {
        const response = await fetch(`${API_BASE}/printers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(printerData)
        });
        
        if (response.ok) {
            showMessage('Printer added successfully!', 'success');
            document.getElementById('addPrinterForm').reset();
            loadPrinters();
        } else {
            const error = await response.json();
            showMessage(`Error: ${error.error || 'Failed to add printer'}`, 'error');
        }
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    }
});

// Load printers list
async function loadPrinters() {
    const container = document.getElementById('printersList');
    container.innerHTML = '<p class="loading">Loading printers...</p>';
    
    try {
        const response = await fetch(`${API_BASE}/printers`);
        const data = await response.json();
        
        if (data.entries && data.entries.length > 0) {
            container.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Location</th>
                            <th>Building</th>
                            <th>Floor</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.entries.map(printer => `
                            <tr>
                                <td>${printer.name}</td>
                                <td>${printer.location}</td>
                                <td>${printer.building}</td>
                                <td>${printer.floor}</td>
                                <td class="action-buttons">
                                    <button class="btn-edit" onclick="editPrinter('${printer._id}')">Edit</button>
                                    <button class="btn-delete" onclick="deletePrinter('${printer._id}', '${printer.name}')">Delete</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            container.innerHTML = '<p>No printers found. Add one above!</p>';
        }
    } catch (error) {
        container.innerHTML = `<p class="error">Error loading printers: ${error.message}</p>`;
    }
}

// Delete printer
async function deletePrinter(id, name) {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/printers/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showMessage('Printer deleted successfully!', 'success');
            loadPrinters();
        } else {
            const error = await response.json();
            showMessage(`Error: ${error.error || 'Failed to delete printer'}`, 'error');
        }
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    }
}

// Edit printer (simplified - just shows alert for now)
function editPrinter(id) {
    alert('Edit functionality coming soon! For now, delete and re-add the printer.');
    // TODO: Implement edit modal
}

// Bulk CSV import
document.getElementById('bulkImportForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showMessage('Please select a CSV file', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/printers/import`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            showMessage(`Successfully imported ${result.count || 0} printers!`, 'success');
            fileInput.value = '';
            loadPrinters();
        } else {
            const error = await response.json();
            showMessage(`Error: ${error.error || 'Failed to import CSV'}`, 'error');
        }
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    }
});

// Show message helper
function showMessage(text, type) {
    const existingMessage = document.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.textContent = text;
    
    const firstCard = document.querySelector('.admin-card');
    firstCard.parentNode.insertBefore(message, firstCard);
    
    setTimeout(() => message.remove(), 5000);
}
