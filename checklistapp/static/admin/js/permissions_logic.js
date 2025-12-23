// Gère la logique des dépendances entre les checkboxes

(function() {
    'use strict';
    
    function setupPermissionsLogic() {
        const isAdminCheckbox = document.querySelector('#id_is_admin');
        const canEditCheckbox = document.querySelector('#id_can_edit');
        const canViewCheckbox = document.querySelector('#id_can_view');
        
        if (!isAdminCheckbox || !canEditCheckbox || !canViewCheckbox) {
            return; // Pas sur la bonne page
        }
        
        // Quand is_admin est coché
        isAdminCheckbox.addEventListener('change', function() {
            if (this.checked) {
                canEditCheckbox.checked = true;
                canViewCheckbox.checked = true;
            }
        });
        
        // Quand can_edit est coché
        canEditCheckbox.addEventListener('change', function() {
            if (this.checked) {
                canViewCheckbox.checked = true;
            }
        });
        
        // Empêcher de décocher can_view si can_edit est coché
        canViewCheckbox.addEventListener('change', function() {
            if (!this.checked && canEditCheckbox.checked) {
                this.checked = true;
                alert('Cannot remove read access without removing edit access');
            }
        });
        
        // Empêcher de décocher can_edit ou can_view si is_admin est coché
        canEditCheckbox.addEventListener('change', function() {
            if (!this.checked && isAdminCheckbox.checked) {
                this.checked = true;
                alert('Cannot remove edit access to admin');
            }
        });
    }
    
    // Exécuter au chargement de la page
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupPermissionsLogic);
    } else {
        setupPermissionsLogic();
    }
})();