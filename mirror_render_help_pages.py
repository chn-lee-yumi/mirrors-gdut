import glob
import os
from string import Template

HEADER = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="广东工业大学开源镜像站 - 使用帮助">
    <link rel="stylesheet" type="text/css" href="/mirror.css" media="screen" />
    <link rel="icon" type="image/x-icon" href="/pages/favicon.ico">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.6.0/styles/atom-one-dark.min.css">
    <title>广东工业大学开源镜像站</title>
</head>

<body class="fade-in">

<!-- Glassmorphic Navigation Bar -->
<nav class="navbar">
    <div class="navbar-container">
        <a href="/" class="navbar-brand">
            <img src="/pages/GDUT_Logo.png" alt="GDUT Logo">
            <span>GDUT 开源镜像站</span>
        </a>
        <div class="navbar-actions">
            <button class="theme-toggle" aria-label="切换主题" title="切换深色/浅色主题">
                <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/>
                </svg>
            </button>
        </div>
    </div>
</nav>

<!-- Main Content -->
<main class="main-container">
    <div class="bento-grid">
        <!-- Sidebar Navigation -->
        <div class="bento-sidebar">
            <div class="island">
                <div class="island-header">
                    <svg class="island-icon" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                    </svg>
                    <h2 class="island-title">镜像列表</h2>
                </div>
                <ul class="nav">

"""

NAVIGATION_TEMPLATE = Template("""
                    <li class="nav-item">
                        <a href="/help/${mirror}.html" class="nav-link ${selected}">${mirror}</a>
                    </li>
""")

FOOTER = Template("""
                </ul>
            </div>
        </div>
        
        <!-- Main Content Area -->
        <div class="bento-main">
            <div class="island">
                <div class="island-header">
                    <svg class="island-icon" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <h2 class="island-title">${mirror} 镜像使用帮助</h2>
                </div>
                <div class="help-content">
${html}
                </div>
            </div>
        </div>
    </div>
</main>

<!-- Footer -->
<footer id="footer">
    <div>
        <a target="_blank" href="http://www.gdut.edu.cn/">
            <svg width="16" height="16" style="vertical-align: middle;" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"/>
            </svg>
            广东工业大学首页
        </a>
        &nbsp;|&nbsp;
        <a target="_blank" href="/pages/about.html">
            <svg width="16" height="16" style="vertical-align: middle;" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
            </svg>
            关于我们
        </a>
        &nbsp;|&nbsp;
        <a href="mailto:stunic@gdut.edu.cn">
            <svg width="16" height="16" style="vertical-align: middle;" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
            </svg>
            联系我们
        </a>
        &nbsp;|&nbsp;
        <a target="_blank" href="https://docs.stunic.gdut.edu.cn/s/d6a3f671-45f2-4c51-9a51-c651f3a7d6ac/doc/5bm5bel6zwc5yop56uz5l255so5pah5qgj-XtDBSIgjtB">
            <svg width="16" height="16" style="vertical-align: middle;" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z"/>
            </svg>
            文档中心
        </a>
        &nbsp;|&nbsp;
        <a target="_blank" href="/pages/status.html">
            <svg width="16" height="16" style="vertical-align: middle;" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            当前状态
        </a>
        &nbsp;|&nbsp;
        <a target="_blank" href="https://speed.gdut.edu.cn">
            <svg width="16" height="16" style="vertical-align: middle;" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"/>
            </svg>
            校内测速
        </a>
    </div>
    <div style="margin-top: 12px; font-size: 0.875rem; color: var(--color-text-muted);">
        © 2024 广东工业大学学生网管队 | Powered by Island UI
    </div>
</footer>

<script type="text/javascript" src="/mirror.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.6.0/highlight.min.js"></script>
<script>hljs.highlightAll();</script>
</body>
</html>
""")

mirror_list = sorted(glob.glob('/mnt/mirror/*'))
ignore_dir = ['static', 'font', 'help']

if not os.path.exists('/mnt/mirror/help'):
    os.makedirs('/mnt/mirror/help')  # 创建文件夹

mirror_names = []

for mirror in mirror_list:
    if os.path.isdir(mirror):
        mirror_name = mirror.split('/')[-1]

        # 判断目录是否要忽略
        if mirror_name in ignore_dir:
            continue

        mirror_names.append(mirror_name)

for mirror in mirror_names:
    html = HEADER
    for m in mirror_names:
        if m == mirror:
            selected = "nav-link-selected"
        else:
            selected = ""
        html += NAVIGATION_TEMPLATE.substitute(mirror=m, selected=selected)

    try:
        with open(f'help_pages_template/{mirror}.html', 'r') as f:
            html += FOOTER.substitute(mirror=mirror, html=f.read())
    except FileNotFoundError:
        html += FOOTER.substitute(mirror=mirror, html="<p>该镜像的帮助文档正在编写中……</p>")
    with open(f'/mnt/mirror/help/{mirror}.html', 'w') as f:
        f.write(html)
