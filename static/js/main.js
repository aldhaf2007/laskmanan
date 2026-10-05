// Student Attendance Management System Interactivity

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // 2. Client-side Instant Filter for Tables
    const instantSearchInput = document.getElementById('tableInstantSearch');
    if (instantSearchInput) {
        instantSearchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            const rows = document.querySelectorAll('.filterable-table tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // 3. Setup Dialog Modals backdrop click close
    const dialogs = document.querySelectorAll('dialog');
    dialogs.forEach(dialog => {
        dialog.addEventListener('click', (e) => {
            const dialogDimensions = dialog.getBoundingClientRect();
            if (
                e.clientX < dialogDimensions.left ||
                e.clientX > dialogDimensions.right ||
                e.clientY < dialogDimensions.top ||
                e.clientY > dialogDimensions.bottom
            ) {
                dialog.close();
            }
        });
    });
});

// Modal helpers
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal && typeof modal.showModal === 'function') {
        modal.showModal();
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal && typeof modal.close === 'function') {
        modal.close();
    }
}

// Attendance Bulk Actions
function markAllAttendance(status) {
    const radios = document.querySelectorAll('.attendance-toggle-radio');
    radios.forEach(radio => {
        if (radio.value === status) {
            radio.checked = true;
        }
    });
}

// Mobile sidebar toggle
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

// Print Report
function printReport() {
    window.print();
}
