import glob
import os
import csv
from string import Template

"""
生成镜像站主页
HEADER+section+FOOTER
section即中间表格部分
"""

HEADER = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="广东工业大学开源镜像站 - 为校内用户提供稳定快速的开源软件镜像服务">
    <link rel="stylesheet" type="text/css" href="/mirror.css" media="screen" />
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <title>广东工业大学开源镜像站</title>
</head>

<body class="fade-in">

<!-- Glassmorphic Navigation Bar -->
<nav class="navbar">
    <div class="navbar-container">
        <a href="/" class="navbar-brand">
            <img src="/GDUT_Logo.png" alt="GDUT Logo">
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

<!-- Hero Section -->
<section class="hero">
    <div class="hero-content">
        <img src="/GDUT_Logo.png" alt="GDUT Logo" class="hero-logo">
        <h1 class="hero-title">广东工业大学开源镜像站</h1>
        <p class="hero-subtitle">为校内用户提供高速、稳定的开源软件镜像服务</p>
        
        <!-- Search Box -->
        <div class="search-container">
            <div class="search-box">
                <span class="search-icon">
                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
                    </svg>
                </span>
                <input type="text" id="search" class="search-input" placeholder="搜索镜像名称..." aria-label="搜索镜像">
            </div>
        </div>
    </div>
</section>

<!-- Main Content - Bento Grid Layout -->
<main class="main-container">
    <div class="bento-grid">
        <!-- Main Island - Mirror List -->
        <div class="bento-main">
            <div class="island">
                <div class="island-header">
                    <svg class="island-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                        <polyline points="9 22 9 12 15 12 15 22"></polyline>
                    </svg>
                    <h2 class="island-title">镜像列表</h2>
                </div>
                <table id="distro-table" cellpadding="0" cellspacing="0">
                    <thead>
                        <tr>
                            <th>
                                <svg width="18" height="18" style="vertical-align: middle; margin-right: 4px;" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z"/>
                                    <path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z"/>
                                    <path d="M17 5c0 1.657-3.134 3-7 3S3 6.657 3 5s3.134-3 7-3 7 1.343 7 3z"/>
                                </svg>
                                镜像名称
                            </th>
                            <th>
                                <svg width="18" height="18" style="vertical-align: middle; margin-right: 4px;" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/>
                                </svg>
                                同步时间
                            </th>
                            <th>
                                <svg width="18" height="18" style="vertical-align: middle; margin-right: 4px;" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                                </svg>
                                同步状态
                            </th>
                            <th>
                                <svg width="18" height="18" style="vertical-align: middle; margin-right: 4px;" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"/>
                                </svg>
                                下载次数
                            </th>
                            <th>
                                <svg width="18" height="18" style="vertical-align: middle; margin-right: 4px;" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                                </svg>
                                使用帮助
                            </th>
                        </tr>
                    </thead>
                    <tbody>

"""

SECTION_TEMPLATE = Template("""
                    <tr class="${row_class}">
                        <td>
                            <svg width="16" height="16" style="vertical-align: middle; margin-right: 6px;" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z"/>
                                <path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z"/>
                            </svg>
                            ${mirror_link}
                        </td>
                        <td><code>${sync_time}</code></td>
                        <td>${sync_status}</td>
                        <td>${download_count}</td>
                        <td>
                            <a target="_blank" href="help/docs/mirrors/${mirror_name}-help" style="display: inline-flex; align-items: center; gap: 4px;">
                                <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
                                </svg>
                                使用帮助
                            </a>
                        </td>
                    </tr>
""")

FOOTER = """
                    </tbody>
                </table>
            </div>
        </div>
        
        <aside class="bento-sidebar">
            <div class="island island-compact">
                <div class="island-header">
                    <svg class="island-icon" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    <h2 class="island-title">快速下载</h2>
                </div>
                <ul>
                    <li><a href="https://mirrors.gdut.edu.cn/centos-stream/9-stream/BaseOS/x86_64/iso/CentOS-Stream-9-latest-x86_64-dvd1.iso">CentOS 9 安装盘</a></li>
                    <li><a href="https://mirrors.gdut.edu.cn/debian-cd/current/amd64/iso-cd/debian-12.8.0-amd64-netinst.iso">Debian 12 网络安装盘</a></li>
                    <li><a href="https://mirrors.gdut.edu.cn/ubuntu-releases/oracular/ubuntu-24.10-desktop-amd64.iso">Ubuntu 24.10 桌面版</a></li>
                </ul>
            </div>
            
            <div class="island island-compact">
                <div class="island-header">
                    <svg class="island-icon" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="2" y1="12" x2="22" y2="12"></line>
                        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                    </svg>
                    <h2 class="island-title">域名选择</h2>
                </div>
                <ul>
                    <li><a href="https://mirrors.gdut.edu.cn">mirrors.gdut.edu.cn</a> <small style="color: var(--color-text-muted);">自动选择</small></li>
                    <li><a href="https://mirrors4.gdut.edu.cn">mirrors4.gdut.edu.cn</a> <small style="color: var(--color-text-muted);">IPv4 线路</small></li>
                    <li><a href="https://mirrors6.gdut.edu.cn">mirrors6.gdut.edu.cn</a> <small style="color: var(--color-text-muted);">IPv6 线路</small></li>
                </ul>
            </div>
            
            <div class="island island-compact">
                <div class="island-header">
                    <svg class="island-icon" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                        <polyline points="22,6 12,13 2,6"></polyline>
                    </svg>
                    <h2 class="island-title">联系我们</h2>
                </div>
                <ul>
                    <li><strong>发送邮件</strong><br><a href="mailto:stunic@gdut.edu.cn">stunic@gdut.edu.cn</a></li>
                </ul>
            </div>
            
            <div class="island island-compact">
                <div class="island-header">
                    <svg class="island-icon" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                    </svg>
                    <h2 class="island-title">相关链接</h2>
                </div>
                <ul>
                    <li><a target="_blank" href="http://www.gdut.edu.cn/">广东工业大学首页</a></li>
                    <li><a target="_blank" href="about.html">关于我们</a></li>
                    <li><a target="_blank" href="https://docs.stunic.gdut.edu.cn/s/d6a3f671-45f2-4c51-9a51-c651f3a7d6ac/doc/5bm5bel6zwc5yop56uz5l255so5pah5qgj-XtDBSIgjtB">文档中心</a></li>
                    <li><a target="_blank" href="status.html">当前状态</a></li>
                    <li><a target="_blank" rel="noopener noreferrer" href="https://registry.gdut.edu.cn">容器镜像库</a></li>
                    <li><a target="_blank" href="https://speed.gdut.edu.cn">校内测速</a></li>
                </ul>
            </div>
        </aside>
    </div>
</main>

<footer id="footer">
    <div>
        <a target="_blank" href="http://www.gdut.edu.cn/">
            <svg width="16" height="16" style="vertical-align: middle;" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"/>
            </svg>
            广东工业大学首页
        </a>
        &nbsp;|&nbsp;
        <a target="_blank" href="about.html">
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
        <a target="_blank" href="status.html">
            <svg width="16" height="16" style="vertical-align: middle;" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            当前状态
        </a>
        &nbsp;|&nbsp;
        <a target="_blank" rel="noopener noreferrer" href="https://registry.gdut.edu.cn">
            <svg width="16" height="16" style="vertical-align: middle;" fill="currentColor" viewBox="0 0 20 20">
                <path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z"/>
                <path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z"/>
                <path d="M17 5c0 1.657-3.134 3-7 3S3 6.657 3 5s3.134-3 7-3 7 1.343 7 3z"/>
            </svg>
            容器镜像库
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

<script type="text/javascript" src="mirror.js"></script>
</body>
</html>
"""

# 读取下载次数统计
download_stats = {}
try:
    with open('/home/mirror/log/total.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过标题行
        for row in reader:
            if len(row) == 2:
                mirror_name, count = row
                download_stats[mirror_name] = count
except FileNotFoundError:
    pass

html = HEADER
odd_or_even = 'even'

mirror_list = sorted(glob.glob('/mnt/mirror/*'))
cdn_mirror_list = ['pypi', 'centos-vault', 'anaconda', 'anolis', 'crates.io-index', 'maven', 'npm', 'kali', 'ubuntu-ports', 'freebsd-pkg', 'docker', 'go', 'openwrt', 'opensuse']
ignore_dir = ['static', 'font', 'help', 'Nginx-Fancyindex-Theme', 'certs', 'git', 'scripts', 'ubuntu-cloud-images']

for mirror in mirror_list:
    if os.path.isdir(mirror):
        mirror_name = mirror.split('/')[-1]

        # 判断目录是否要忽略
        if mirror_name in ignore_dir:
            continue

        # 获取下载次数
        download_count = download_stats.get(mirror_name, '0')

        # 判断镜像是否缓存镜像
        if mirror_name in cdn_mirror_list:  # 缓存镜像（nginx反向代理）
            sync_time = '⛔️'
            sync_status = '⏩ 缓存加速'
            is_syncing = 'false'
        else:  # 非缓存镜像（保存在服务器硬盘）
            try:
                with open('/home/mirror/sync_time/' + mirror_name, 'r') as f:
                    sync_time = "⏱️ " + f.read().strip()
                if os.path.isfile('/tmp/mirror/lock/' + mirror_name + '.lock'):
                    sync_status = '▶️ 同步中'
                else:
                    sync_status = '✅ 同步完成'
            except FileNotFoundError:
                sync_time = '⛔️'
                sync_status = '❌ 从未同步'

        # 生成镜像链接（缓存镜像除了docker都不显示链接）
        if mirror_name in cdn_mirror_list and mirror_name != "docker":
            mirror_link = mirror_name
        else:
            mirror_link = f'<a href="/{mirror_name}/">{mirror_name}</a>'

        # 修改表格的class，得出黑白相间的表格
        if odd_or_even == 'even':
            row_class = 'even'
            odd_or_even = 'odd'
        else:  # odd
            row_class = 'odd'
            odd_or_even = 'even'
        if sync_status == '▶️ 同步中':
            row_class = 'syncing-row'
        # 组合成一行的HTML
        html += SECTION_TEMPLATE.substitute(row_class=row_class, mirror_link=mirror_link, mirror_name=mirror_name, sync_time=sync_time,
                                            sync_status=sync_status, download_count=download_count)

html += FOOTER

with open('/mnt/mirror/index.html', 'w') as f:
    f.write(html)
