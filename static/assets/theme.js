// Theme management functionality

class ThemeManager {
    constructor() {
        this.init();
        this.bindEvents();
    }
    
    init() {
        // Check for saved theme preference or default to light
        const savedTheme = localStorage.getItem('theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme) {
            this.setTheme(savedTheme);
        } else if (systemPrefersDark) {
            this.setTheme('dark');
        } else {
            this.setTheme('light');
        }
    }
    
    setTheme(theme) {
        const html = document.documentElement;
        console.log(`Setting theme to: ${theme}`);
        
        if (theme === 'dark') {
            html.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            html.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
        
        // Update all theme toggle buttons
        this.updateToggleButtons();
        console.log(`Theme applied. HTML classes: ${html.className}`);
    }
    
    toggleTheme() {
        const html = document.documentElement;
        const currentTheme = html.classList.contains('dark') ? 'dark' : 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        console.log(`Theme toggle: ${currentTheme} -> ${newTheme}`);
        this.setTheme(newTheme);
    }
    
    updateToggleButtons() {
        const isDark = document.documentElement.classList.contains('dark');
        
        // Update main theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            const moonIcon = themeToggle.querySelector('.fa-moon');
            const sunIcon = themeToggle.querySelector('.fa-sun');
            
            if (moonIcon && sunIcon) {
                if (isDark) {
                    moonIcon.classList.add('hidden');
                    sunIcon.classList.remove('hidden');
                } else {
                    moonIcon.classList.remove('hidden');
                    sunIcon.classList.add('hidden');
                }
            }
        }
        
        // Update sidebar theme toggle
        const sidebarToggle = document.getElementById('theme-toggle-sidebar');
        if (sidebarToggle) {
            const moonIcon = sidebarToggle.querySelector('.fa-moon');
            const sunIcon = sidebarToggle.querySelector('.fa-sun');
            const spans = sidebarToggle.querySelectorAll('span');
            
            if (moonIcon && sunIcon) {
                if (isDark) {
                    moonIcon.classList.add('hidden');
                    sunIcon.classList.remove('hidden');
                } else {
                    moonIcon.classList.remove('hidden');
                    sunIcon.classList.add('hidden');
                }
            }
            
            // Update text spans
            spans.forEach(span => {
                if (span.classList.contains('dark:hidden')) {
                    // Light mode text
                    if (isDark) {
                        span.classList.add('hidden');
                    } else {
                        span.classList.remove('hidden');
                    }
                } else if (span.classList.contains('hidden') && span.classList.contains('dark:block')) {
                    // Dark mode text
                    if (isDark) {
                        span.classList.remove('hidden');
                    } else {
                        span.classList.add('hidden');
                    }
                }
            });
        }
        
        // Update settings theme toggle
        const settingsToggle = document.getElementById('theme-toggle-settings');
        if (settingsToggle) {
            const toggleSpan = settingsToggle.querySelector('span:last-child');
            if (toggleSpan) {
                if (isDark) {
                    toggleSpan.classList.add('translate-x-6');
                } else {
                    toggleSpan.classList.remove('translate-x-6');
                }
            }
        }
    }
    
    bindEvents() {
        // Bind all theme toggle buttons
        const toggleButtons = [
            'theme-toggle',
            'theme-toggle-sidebar', 
            'theme-toggle-settings'
        ];
        
        toggleButtons.forEach(id => {
            const button = document.getElementById(id);
            if (button) {
                button.addEventListener('click', () => this.toggleTheme());
            }
        });
        // Also bind to all buttons with class 'theme-toggle' (for multiple toggles per page)
        document.querySelectorAll('.theme-toggle').forEach(button => {
            button.addEventListener('click', () => this.toggleTheme());
        });
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
}

// Initialize theme manager when DOM is loaded or immediately if already loaded
function initializeTheme() {
    if (!window.themeManager) {
        console.log('Initializing ThemeManager...');
        window.themeManager = new ThemeManager();
        console.log('ThemeManager initialized successfully');
    } else {
        console.log('ThemeManager already exists');
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTheme);
} else {
    initializeTheme();
}
