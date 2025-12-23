// static/js/base.js

/**
 * Toggle user dropdown
 */
function toggleUserDropdown() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('show');
}

/**
 * Close dropdowns when clicking outside
 */
document.addEventListener('click', function(event) {
    const userMenu = document.querySelector('.user-menu');
    const dropdown = document.getElementById('userDropdown');
    
    if (userMenu && dropdown && !userMenu.contains(event.target)) {
        dropdown.classList.remove('show');
    }
});

/**
 * Auto-dismiss alerts after 5 seconds
 */
// Fonction pour auto-fermer les alertes
function autoCloseAlerts() {
    const alerts = document.querySelectorAll('#messages-container .alert');
    
    alerts.forEach(function(alert) {
        if (alert.dataset.autoCloseSet) return;
        alert.dataset.autoCloseSet = 'true';
        
        setTimeout(function() {
            alert.style.animation = 'slideOut 0.3s ease';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    autoCloseAlerts();
    lucide.createIcons();

    // htmx.logAll();
    // document.body.addEventListener("htmx:oobErrorNoTarget", e => {
    //     console.log("OOB FAIL →", e.detail.content.outerHTML);
    // });
});

document.addEventListener('htmx:afterSwap', function(event) {
    autoCloseAlerts();
    lucide.createIcons();
});

// Setup icons: https://lucide.dev/icons/
