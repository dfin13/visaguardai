// Dark mode always enabled - no toggle functionality

// Force dark mode on page load
function initializeDarkMode() {
    const html = document.documentElement;
    html.classList.add('dark');
    // Set in localStorage for consistency
    localStorage.setItem('theme', 'dark');
    console.log('Dark mode enabled permanently');
}

// Initialize immediately or on DOM load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDarkMode);
} else {
    initializeDarkMode();
}
