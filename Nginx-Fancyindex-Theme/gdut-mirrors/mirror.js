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
    const THEME_MODES = ['light', 'dark', 'auto'];
    var systemDarkMedia = window.matchMedia('(prefers-color-scheme: dark)');
    var systemThemeHandler = null;

    function applyTheme(mode) {
        var isDark = mode === 'dark' || (mode === 'auto' && systemDarkMedia.matches);
        document.body.classList.toggle('dark-theme', isDark);
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(function () { document.body.style.transition = ''; }, 300);
        updateThemeToggleIcon(document.querySelector('.theme-toggle'), mode);
    }

    function initTheme() {
        var stored = localStorage.getItem(THEME_STORAGE_KEY);
        var mode = THEME_MODES.indexOf(stored) >= 0 ? stored : 'auto';

        applyTheme(mode);

        var themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', toggleTheme);
        }

        systemThemeHandler = function () {
            var current = localStorage.getItem(THEME_STORAGE_KEY);
            if (current === 'auto' || !current) applyTheme('auto');
        };
        systemDarkMedia.addEventListener('change', systemThemeHandler);
    }

    function toggleTheme() {
        var current = localStorage.getItem(THEME_STORAGE_KEY);
        var idx = THEME_MODES.indexOf(current);
        if (idx < 0) idx = 2;
        var next = THEME_MODES[(idx + 1) % THEME_MODES.length];
        localStorage.setItem(THEME_STORAGE_KEY, next);
        applyTheme(next);
    }

    function updateThemeToggleIcon(button, mode) {
        if (!button) return;
        var icons = {
            light: '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"/></svg>',
            dark: '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/></svg>',
            auto: '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a8 8 0 100 16 8 8 0 000-16zm0 2a6 6 0 010 12V4z"/></svg>'
        };
        var labels = { light: '浅色模式（点击切换到深色）', dark: '深色模式（点击切换到自动）', auto: '跟随系统（点击切换到浅色）' };
        button.innerHTML = icons[mode] || icons.auto;
        button.title = labels[mode] || labels.auto;
    }

    // ==========================================
    // Search Functionality
    // ==========================================
    
    // 列表动画参数：退场 150ms、FLIP 位移 220ms、入场 180ms
    const MOTION = {
        exit: 150,
        move: 220,
        enter: 180,
        easeExit: 'cubic-bezier(0.4, 0, 0.2, 1)',
        easeMove: 'cubic-bezier(0.22, 1, 0.36, 1)'
    };

    const reducedMotionQuery = window.matchMedia
        ? window.matchMedia('(prefers-reduced-motion: reduce)')
        : null;

    // 行 -> 正在播放的 Animation 列表，下一次过滤时统一打断
    const rowAnimations = new Map();
    // 过滤轮次：丢弃被新一轮取代的旧动画回调
    let searchGeneration = 0;

    function prefersReducedMotion() {
        return !!(reducedMotionQuery && reducedMotionQuery.matches);
    }

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
    
    function trackAnimation(row, animation) {
        let list = rowAnimations.get(row);
        if (!list) {
            list = [];
            rowAnimations.set(row, list);
        }
        list.push(animation);
        // cancel 会让 finished reject，这里吞掉避免未处理的拒绝。
        // 注意不要在这里把已完成的动画移出列表：fill: forwards 的动画
        // 演完后仍会持续施加效果，必须留在列表里等下一轮统一 cancel。
        animation.finished.catch(function() {});
    }

    function cancelRowAnimations() {
        rowAnimations.forEach(function(list) {
            list.forEach(function(animation) {
                animation.cancel();
            });
        });
        rowAnimations.clear();
    }

    // 把当前视觉状态固化成内联样式，之后再取消动画，
    // 这样打断时行不会从半路位置/半透明状态突然跳回。
    function freezeRowVisual(row) {
        const computed = window.getComputedStyle(row);
        const frozen = { opacity: 1, scale: 1 };

        const opacity = parseFloat(computed.opacity);
        if (!isNaN(opacity) && opacity < 1) {
            frozen.opacity = opacity;
            row.style.opacity = String(opacity);
        }

        const scale = parseFloat(computed.scale);
        if (!isNaN(scale) && scale < 1) {
            frozen.scale = scale;
            row.style.scale = String(scale);
        }

        if (computed.translate && computed.translate !== 'none') {
            row.style.translate = computed.translate;
        }

        return frozen;
    }

    function clearRowVisual(row) {
        row.style.opacity = '';
        row.style.scale = '';
        row.style.translate = '';
    }

    function applyRowVisibility(toHide, toShow) {
        toHide.forEach(function(row) {
            row.setAttribute('hidden', '');
        });
        toShow.forEach(function(row) {
            row.removeAttribute('hidden');
        });
    }
    
    function performSearch(query, rows) {
        const generation = ++searchGeneration;
        const termText = query.trim().toLowerCase();
        const searchTerms = termText === '' ? [] : termText.split(/\s+/);

        // 旧的无结果提示先撤掉，等本轮退场结束再按需重新插入
        const staleMessage = document.querySelector('.no-results');
        if (staleMessage) staleMessage.remove();

        // 1. 先冻结视觉状态，再打断上一轮动画
        const frozen = new Map();
        rows.forEach(function(row) {
            frozen.set(row, freezeRowVisual(row));
        });
        cancelRowAnimations();

        // 2. 计算新的可见集合
        const wasVisible = new Map();
        const toHide = [];
        const toShow = [];

        rows.forEach(function(row) {
            const text = row.textContent.toLowerCase().replace(/\s+/g, ' ');
            const matches = searchTerms.every(function(term) {
                return text.indexOf(term) !== -1;
            });
            const visible = !row.hasAttribute('hidden');
            wasVisible.set(row, visible);

            if (visible && !matches) toHide.push(row);
            if (!visible && matches) toShow.push(row);
        });

        // 3. 记录过滤前的位置（文档坐标，页面滚动后仍可比）
        const scrollBefore = window.scrollY || window.pageYOffset || 0;
        const beforeTop = new Map();
        rows.forEach(function(row) {
            beforeTop.set(row, wasVisible.get(row)
                ? row.getBoundingClientRect().top + scrollBefore
                : null);
        });

        // 减少动态偏好的用户直接瞬时切换
        if (prefersReducedMotion()) {
            applyRowVisibility(toHide, toShow);
            rows.forEach(clearRowVisual);
            updateSearchResults(rows);
            return;
        }

        // 4. 退场：被过滤的行原地淡出收拢，演完才让出空间
        if (toHide.length === 0) {
            finishSearch(generation, rows, toHide, toShow, frozen, beforeTop);
            return;
        }

        const exits = toHide.map(function(row) {
            const state = frozen.get(row) || { opacity: 1, scale: 1 };
            const animation = row.animate(
                [
                    { opacity: state.opacity, scale: state.scale },
                    { opacity: 0, scale: 0.96 }
                ],
                { duration: MOTION.exit, easing: MOTION.easeExit, fill: 'forwards' }
            );
            trackAnimation(row, animation);
            return animation.finished.catch(function() {});
        });

        Promise.all(exits).then(function() {
            if (generation !== searchGeneration) return;
            finishSearch(generation, rows, toHide, toShow, frozen, beforeTop);
        });
    }

    // 退场结束后：切换显隐、测量新位置，并对剩余行做 FLIP
    function finishSearch(generation, rows, toHide, toShow, frozen, beforeTop) {
        if (generation !== searchGeneration) return;

        // 先清掉退场动画（fill: forwards 会残留 opacity: 0，
        // 行再次显示时会被这个残留值压住），再切显隐
        cancelRowAnimations();
        applyRowVisibility(toHide, toShow);
        // 冻结态已记录进 beforeTop，统一清掉，避免残留内联位移
        rows.forEach(clearRowVisual);

        const scrollAfter = window.scrollY || window.pageYOffset || 0;

        rows.forEach(function(row) {
            if (row.hasAttribute('hidden')) return;

            const state = frozen.get(row) || { opacity: 1, scale: 1 };
            const visibleBefore = beforeTop.get(row) !== null;
            const from = {};
            const to = {};
            let duration = MOTION.move;

            if (!visibleBefore) {
                // 新出现的行没有历史位置，做淡入 + 小幅上移
                from.opacity = 0;
                from.translate = '8px';
                to.opacity = 1;
                to.translate = '0px';
                duration = MOTION.enter;
            } else {
                const afterTop = row.getBoundingClientRect().top + scrollAfter;
                const delta = beforeTop.get(row) - afterTop;
                if (Math.abs(delta) > 0.5) {
                    from.translate = delta + 'px';
                    to.translate = '0px';
                }
                // 上一轮被打断在淡出途中，这里平滑恢复
                if (state.opacity < 1) {
                    from.opacity = state.opacity;
                    to.opacity = 1;
                }
                if (state.scale < 1) {
                    from.scale = state.scale;
                    to.scale = 1;
                }
            }

            if (Object.keys(from).length === 0) return;
            trackAnimation(row, row.animate([from, to], {
                duration: duration,
                easing: MOTION.easeMove
            }));
        });

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
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    entry.target.addEventListener('transitionend', function handler() {
                        entry.target.style.transform = '';
                        entry.target.style.transition = '';
                        entry.target.removeEventListener('transitionend', handler);
                    });
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0,
            rootMargin: '0px'
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
            const html = cell.innerHTML.trim();
            const text = cell.textContent.trim();
            let badgeClass = '';
            
            if (text.includes('同步完成')) {
                badgeClass = 'status-success';
            } else if (text.includes('同步中')) {
                badgeClass = 'status-syncing';
            } else if (text.includes('缓存')) {
                badgeClass = 'status-cache';
            } else if (text.includes('从未')) {
                badgeClass = 'status-error';
            }
            
            if (badgeClass) {
                const badge = document.createElement('span');
                badge.className = `status-badge ${badgeClass}`;
                badge.innerHTML = html;
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
    // Navbar Brand Visibility
    // ==========================================

    function initNavbarBrandVisibility() {
        const heroTitle = document.querySelector('.hero-title');
        const navbar = document.querySelector('.navbar');
        const navbarBrand = document.querySelector('.navbar-brand.autohide');
        if (!heroTitle || !navbarBrand || !navbar) return;

        const navbarHeight = navbar.offsetHeight;
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    navbarBrand.classList.remove('is-visible');
                } else {
                    navbarBrand.classList.add('is-visible');
                }
            });
        }, {
            rootMargin: `-${navbarHeight}px 0px 0px 0px`,
            threshold: 0,
        });

        observer.observe(heroTitle);
    }

    // ==========================================
    // Spotlight Effect (光斑跟随鼠标)
    // ==========================================

    function initSpotlight() {
        function onMouseMove(e) {
            const el = e.target.closest('.navbar, .island, #footer');
            if (!el) return;
            const rect = el.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width * 100;
            const y = (e.clientY - rect.top) / rect.height * 100;
            el.style.setProperty('--mouse-x', x + '%');
            el.style.setProperty('--mouse-y', y + '%');
        }

        document.addEventListener('mousemove', onMouseMove);
    }

    // ==========================================
    // News Feed (RSS)
    // ==========================================

    function initNews() {
        var RSS_URL = '/help/news/rss.xml';
        var CACHE_KEY = 'gdut-mirror-news-rss';
        var CACHE_TTL = 30 * 60 * 1000;
        var FETCH_TIMEOUT = 5000;
        var NEWS_BASE_URL = '/help/news/';
        var MAX_ITEMS = 3;

        var container = document.getElementById('news-content');
        if (!container) return;

        function escapeHtml(text) {
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function renderEmpty() {
            container.innerHTML = '<p class="news-placeholder">暂无公告</p>';
        }

        function renderItems(items) {
            if (!items || items.length === 0) {
                renderEmpty();
                return;
            }
            var html = '';
            for (var i = 0; i < Math.min(items.length, MAX_ITEMS); i++) {
                var item = items[i];
                var dateStr = '';
                if (item.date) {
                    var d = new Date(item.date);
                    if (!isNaN(d.getTime())) {
                        var yr = d.getFullYear();
                        var mo = String(d.getMonth() + 1).padStart(2, '0');
                        var dy = String(d.getDate()).padStart(2, '0');
                        dateStr = yr + '-' + mo + '-' + dy;
                    }
                }
                html += '<div class="news-item">';
                html += '<a href="' + item.link + '" target="_blank" rel="noopener" class="news-title">' + escapeHtml(item.title) + '</a>';
                if (dateStr) {
                    html += '<span class="news-date">' + dateStr + '</span>';
                }
                html += '</div>';
            }
            html += '<a href="' + NEWS_BASE_URL + '" target="_blank" rel="noopener" class="news-more">查看全部公告 →</a>';
            container.innerHTML = html;
        }

        function getCachedData(freshOnly) {
            try {
                var cached = localStorage.getItem(CACHE_KEY);
                if (!cached) return null;
                var data = JSON.parse(cached);
                if (freshOnly && Date.now() - data.timestamp > CACHE_TTL) return null;
                return data.items;
            } catch (e) {
                return null;
            }
        }

        function setCachedData(items) {
            try {
                localStorage.setItem(CACHE_KEY, JSON.stringify({
                    timestamp: Date.now(),
                    items: items
                }));
            } catch (e) { /* ignore quota errors */ }
        }

        function parseRssXml(xmlText) {
            var parser = new DOMParser();
            var doc = parser.parseFromString(xmlText, 'text/xml');
            if (doc.querySelector('parsererror')) return null;

            var items = [];
            var itemNodes = doc.querySelectorAll('item');
            for (var i = 0; i < itemNodes.length; i++) {
                var node = itemNodes[i];
                var titleEl = node.querySelector('title');
                var linkEl = node.querySelector('link');
                var pubDateEl = node.querySelector('pubDate');

                var title = titleEl ? titleEl.textContent.trim() : '';
                var link = linkEl ? linkEl.textContent.trim() : '';
                var date = pubDateEl ? pubDateEl.textContent.trim() : '';

                if (title && link) {
                    items.push({title: title, link: link, date: date});
                }
            }
            return items;
        }

        var freshCache = getCachedData(true);
        if (freshCache) {
            renderItems(freshCache);
            return;
        }

        var controller = new AbortController();
        var timeoutId = setTimeout(function () {
            controller.abort();
        }, FETCH_TIMEOUT);

        fetch(RSS_URL, {signal: controller.signal})
            .then(function (response) {
                if (!response.ok) throw new Error('HTTP ' + response.status);
                return response.text();
            })
            .then(function (xmlText) {
                clearTimeout(timeoutId);
                var items = parseRssXml(xmlText);
                if (items === null) throw new Error('RSS parse failed');
                setCachedData(items);
                renderItems(items);
            })
            .catch(function () {
                clearTimeout(timeoutId);
                var staleCache = getCachedData(false);
                if (staleCache) {
                    renderItems(staleCache);
                } else {
                    renderEmpty();
                }
            });
    }

    // ==========================================
    // Domain Selector (域名滑块 + IPv4/IPv6 检测)
    // ==========================================

    var DOMAIN_PROBE_TIMEOUT = 6000;

    function initDomainSelector() {
        var slider = document.getElementById('domain-slider');
        var list = document.getElementById('domain-list');
        if (!slider || !list) return;

        var host = window.location.hostname;
        var activeSeg = host.indexOf('mirrors4') !== -1 ? 'ipv4'
                      : host.indexOf('mirrors6') !== -1 ? 'ipv6'
                      : 'auto';

        slider.setAttribute('data-active', activeSeg);

        slider.querySelectorAll('.seg-item').forEach(function (item) {
            if (item.getAttribute('data-seg') === activeSeg) {
                item.addEventListener('click', function (e) { e.preventDefault(); });
            }
        });

        slider.classList.add('detecting');

        var onIPv4 = activeSeg === 'ipv4';
        var onIPv6 = activeSeg === 'ipv6';
        var probes = [];

        function probeProtocol(version) {
            var hostBySeg = { ipv4: 'mirrors4.gdut.edu.cn', ipv6: 'mirrors6.gdut.edu.cn' };
            var url = 'https://' + hostBySeg[version] + '/favicon.ico?r=' + Math.random();
            var controller = new AbortController();
            var timeoutId = setTimeout(function () { controller.abort(); }, DOMAIN_PROBE_TIMEOUT);
            return fetch(url, { mode: 'no-cors', signal: controller.signal })
                .then(function () { clearTimeout(timeoutId); return true; })
                .catch(function () { clearTimeout(timeoutId); return false; });
        }

        function disableSeg(version) {
            var seg = slider.querySelector('.seg-item[data-seg="' + version + '"]');
            if (seg) {
                seg.classList.add('seg-disabled');
                seg.setAttribute('data-unsupported', '当前网络不支持 ' + version.toUpperCase());
            }
        }

        function setBadge(version, supported) {
            var li = list.querySelector('li[data-domain="' + version + '"]');
            if (!li) return;
            var badge = li.querySelector('.domain-badge');
            if (!badge) return;
            var checkSvg = '<svg class="status-icon" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>';
            var crossSvg = '<svg class="status-icon" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
            badge.classList.remove('status-detecting');
            if (supported) {
                badge.classList.add('status-success');
                badge.innerHTML = checkSvg + '支持';
            } else {
                badge.classList.add('status-error');
                badge.innerHTML = crossSvg + '不支持';
                li.classList.add('domain-list-disabled');
            }
        }

        if (onIPv4) setBadge('ipv4', true);
        if (onIPv6) setBadge('ipv6', true);
        if (!onIPv6) probes.push(probeProtocol('ipv6').then(function (ok) { setBadge('ipv6', ok); if (!ok) disableSeg('ipv6'); }));
        if (!onIPv4) probes.push(probeProtocol('ipv4').then(function (ok) { setBadge('ipv4', ok); if (!ok) disableSeg('ipv4'); }));

        Promise.all(probes).then(function () {
            slider.classList.remove('detecting');
        });
    }

    // ==========================================
    // Download Modal (快速下载弹窗)
    // ==========================================

    function initDownloadModal() {
        var modals = document.querySelectorAll('.download-modal');
        if (modals.length === 0) return;

        var openModal = null;

        function focusablesIn(modal) {
            return modal.querySelectorAll('button, a[href], [tabindex]:not([tabindex="-1"])');
        }

        function open(modal) {
            if (openModal) close();
            openModal = modal;
            modal.hidden = false;
            document.body.style.overflow = 'hidden';
            var first = modal.querySelector('.download-modal-close');
            if (first) first.focus();
        }

        function close() {
            if (!openModal) return;
            openModal.hidden = true;
            openModal = null;
            document.body.style.overflow = '';
        }

        modals.forEach(function (modal) {
            modal.addEventListener('click', function (e) {
                if (e.target.closest('[data-close]')) {
                    close();
                    return;
                }
                var navBtn = e.target.closest('.download-nav-item');
                if (navBtn) {
                    var targetId = navBtn.getAttribute('data-target');
                    modal.querySelectorAll('.download-nav-item').forEach(function (b) {
                        b.classList.toggle('active', b === navBtn);
                    });
                    modal.querySelectorAll('.download-variant-panel').forEach(function (p) {
                        p.classList.toggle('active', p.getAttribute('data-panel') === targetId);
                    });
                }
            });

            modal.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') {
                    close();
                    return;
                }
                if (e.key === 'Tab') {
                    var focusables = Array.prototype.slice.call(focusablesIn(modal));
                    if (focusables.length === 0) return;
                    var first = focusables[0];
                    var last = focusables[focusables.length - 1];
                    if (e.shiftKey && document.activeElement === first) {
                        e.preventDefault();
                        last.focus();
                    } else if (!e.shiftKey && document.activeElement === last) {
                        e.preventDefault();
                        first.focus();
                    }
                }
            });
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && openModal) close();
        });

        document.querySelectorAll('.download-entry-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var modal = document.getElementById('download-modal-' + btn.getAttribute('data-modal'));
                if (modal) open(modal);
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
        initNavbarBrandVisibility();
        initSpotlight();
        initNews();
        initDomainSelector();
        initDownloadModal();

        const yearSpan = document.getElementById('copyright-year');
        if (yearSpan) yearSpan.textContent = new Date().getFullYear();

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