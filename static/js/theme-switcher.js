/**
 * Theme Switcher
 * Handles theme switching and persistence
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get saved theme from localStorage or use default
    const savedTheme = localStorage.getItem('theme') || 'default';
    setTheme(savedTheme);

    // Set the selected option in theme selector if it exists
    const themeSelector = document.getElementById('theme-selector');
    if (themeSelector) {
        themeSelector.value = savedTheme;

        // Add event listener for theme changes
        themeSelector.addEventListener('change', function() {
            const selectedTheme = this.value;
            setTheme(selectedTheme);
            localStorage.setItem('theme', selectedTheme);

            // Show toast notification
            showThemeChangeNotification(selectedTheme);
        });
    }

    // Function to set theme
    function setTheme(theme) {
        // Remove all theme classes
        document.body.classList.remove(
            'default-theme',
            'warm-theme',
            'corporate-theme'
        );

        // Add selected theme class
        document.body.classList.add(`${theme}-theme`);

        // Update theme stylesheet
        updateThemeStylesheet(theme);

        // Update active theme in theme selector dropdown
        const themeSelector = document.getElementById('theme-selector');
        if (themeSelector) {
            themeSelector.value = theme;
        }

        // Update active theme in profile page theme selector
        const profileThemeSelector = document.getElementById('profile-theme-selector');
        if (profileThemeSelector) {
            profileThemeSelector.value = theme;
        }

        // Update active theme preview
        const themePreviews = document.querySelectorAll('.theme-preview');
        themePreviews.forEach(preview => {
            preview.classList.remove('active');
            if (preview.dataset.theme === theme) {
                preview.classList.add('active');
            }
        });
    }

    // Function to update theme stylesheet
    function updateThemeStylesheet(theme) {
        const themeLink = document.getElementById('theme-stylesheet');
        if (themeLink) {
            themeLink.href = `/static/css/themes/theme-${theme}.css`;
        } else {
            // If link doesn't exist, create it
            const link = document.createElement('link');
            link.id = 'theme-stylesheet';
            link.rel = 'stylesheet';
            link.href = `/static/css/themes/theme-${theme}.css`;
            document.head.appendChild(link);
        }
    }

    // Function to show theme change notification
    function showThemeChangeNotification(theme) {
        // Get theme name from the theme selector
        const themeOption = document.querySelector(`#theme-selector option[value="${theme}"]`);
        const themeName = themeOption ? themeOption.textContent : theme.charAt(0).toUpperCase() + theme.slice(1);

        // Create toast notification
        const notification = document.createElement('div');
        notification.className = 'toast align-items-center text-white border-0';
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'assertive');
        notification.setAttribute('aria-atomic', 'true');

        notification.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-palette me-2"></i>Theme changed to ${themeName}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        // Add to toast container
        const toastContainer = document.getElementById('toast-container');
        if (toastContainer) {
            toastContainer.appendChild(notification);
            const toast = new bootstrap.Toast(notification);
            toast.show();
        }
    }
});
