document.addEventListener("DOMContentLoaded", function() {
    // Check if the user's system has dark mode preference
    const prefersDarkMode = window.matchMedia("(prefers-color-scheme: dark)").matches;

    // Apply dark theme if user's system preference is for dark mode
    if (prefersDarkMode) {
        document.body.classList.add("dark-theme");
    }
});