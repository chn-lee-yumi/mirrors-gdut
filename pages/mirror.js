/**
 * Island UI - Enhanced Interactions
 * Guangdong University of Technology Open Source Mirror
 */

(function() {
    'use strict';

    // ==========================================
    // Theme Management
    // ==========================================
    
    const THEME_STORAGE_KEY = 'gdut-mirror-theme';
    
    function initTheme() {
        // Check stored preference or system preference
        const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        const isDark = storedTheme === 'dark' || (!storedTheme && prefersDark);
        
        if (isDark) {
            document.body.classList.add('dark-theme');
        }
        
        // Create theme toggle button if it exists
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            updateThemeToggleIcon(themeToggle, isDark);
            themeToggle.addEventListener('click', toggleTheme);
        }
    }
    
    function toggleTheme() {
        const body = document.body;
        const isDark = body.classList.toggle('dark-theme');
        
        localStorage.setItem(THEME_STORAGE_KEY, isDark ? 'dark' : 'light');
        
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            updateThemeToggleIcon(themeToggle, isDark);
        }
        
        // Add smooth transition
        body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            body.style.transition = '';
        }, 300);
    }
    
    function updateThemeToggleIcon(button, isDark) {
        button.innerHTML = isDark 
            ? '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"/></svg>'
            : '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/></svg>';
    }

    // ==========================================
    // Search Functionality
    // ==========================================
    
    function initSearch() {
        const searchInput = document.getElementById('search');
        if (!searchInput) return;
        
        // Cache table rows for better performance
        const tableRows = Array.from(document.querySelectorAll('#distro-table tbody tr'));
        
        // Debounce search for better performance
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value, tableRows);
            }, 150);
        });
        
        // Add search icon
        const searchIcon = document.querySelector('.search-icon');
        if (searchIcon) {
            searchIcon.innerHTML = '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/></svg>';
        }
    }
    
    function performSearch(query, rows) {
        const searchTerms = query.trim().toLowerCase().split(/\s+/);
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase().replace(/\s+/g, ' ');
            const matches = searchTerms.every(term => text.includes(term));
            
            if (matches || query.trim() === '') {
                row.removeAttribute('hidden');
                row.style.animation = 'fadeIn 0.3s ease';
            } else {
                row.setAttribute('hidden', '');
            }
        });
        
        // Show "no results" message if needed
        updateSearchResults(rows);
    }
    
    function updateSearchResults(rows) {
        const visibleRows = rows.filter(row => !row.hasAttribute('hidden'));
        const table = document.querySelector('#distro-table');
        
        // Remove existing no-results message
        const existingMsg = document.querySelector('.no-results');
        if (existingMsg) {
            existingMsg.remove();
        }
        
        // Add no-results message if needed
        if (visibleRows.length === 0 && table) {
            const noResults = document.createElement('div');
            noResults.className = 'no-results';
            noResults.style.cssText = 'text-align: center; padding: 2rem; color: var(--color-text-muted);';
            noResults.innerHTML = '<p>未找到匹配的镜像</p>';
            table.parentNode.appendChild(noResults);
        }
    }

    // ==========================================
    // Island Animations
    // ==========================================
    
    function initIslandAnimations() {
        const islands = document.querySelectorAll('.island');
        
        // Intersection Observer for scroll animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        islands.forEach((island, index) => {
            island.style.opacity = '0';
            island.style.transform = 'translateY(20px)';
            island.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
            observer.observe(island);
        });
    }

    // ==========================================
    // Table Enhancements
    // ==========================================
    
    function enhanceTable() {
        const table = document.querySelector('#distro-table');
        if (!table) return;
        
        // Add row click handlers
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const link = row.querySelector('a');
            if (link) {
                row.style.cursor = 'pointer';
                row.addEventListener('click', (e) => {
                    // Don't trigger if clicking on the link itself
                    if (e.target.tagName !== 'A') {
                        link.click();
                    }
                });
            }
        });
        
        // Enhance status indicators
        enhanceStatusBadges();
    }
    
    function enhanceStatusBadges() {
        const statusCells = document.querySelectorAll('#distro-table td:nth-child(3)');
        statusCells.forEach(cell => {
            const text = cell.textContent.trim();
            let badgeClass = '';
            
            if (text.includes('同步完成') || text.includes('✅')) {
                badgeClass = 'status-success';
            } else if (text.includes('同步中') || text.includes('▶️')) {
                badgeClass = 'status-syncing';
            } else if (text.includes('缓存') || text.includes('⏩')) {
                badgeClass = 'status-cache';
            } else if (text.includes('从未') || text.includes('❌')) {
                badgeClass = 'status-error';
            }
            
            if (badgeClass) {
                const badge = document.createElement('span');
                badge.className = `status-badge ${badgeClass}`;
                badge.textContent = text;
                cell.textContent = '';
                cell.appendChild(badge);
            }
        });
    }

    // ==========================================
    // Smooth Scroll
    // ==========================================
    
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href === '#') return;
                
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // ==========================================
    // Initialize Everything
    // ==========================================
    
    function init() {
        initTheme();
        initSearch();
        initIslandAnimations();
        enhanceTable();
        initSmoothScroll();
        
        // Add fade-in class to body
        document.body.classList.add('fade-in');
    }
    
    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem(THEME_STORAGE_KEY)) {
            document.body.classList.toggle('dark-theme', e.matches);
            const themeToggle = document.querySelector('.theme-toggle');
            if (themeToggle) {
                updateThemeToggleIcon(themeToggle, e.matches);
            }
        }
    });

})();