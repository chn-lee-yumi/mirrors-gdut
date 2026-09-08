# -*- coding: utf-8 -*-
"""
快速下载弹窗条目配置（全部通过 HTTP 解析 Nginx 目录页获取文件列表，
因为部分架构由缓存加速提供，磁盘扫描不完整）。

字段说明:
    name        左侧导航显示名
    base        镜像根路径（URL 相对路径）
    variants    变体列表，每项:
        note    变体说明（副文本，如「桌面版 · x86_64」）
        subdir  URL 子路径，支持 {latest_dir} 占位符（版本号数字开头的子目录按版本排序取最新）
        glob    文件名匹配模式
"""

OS_ITEMS = [
    {
        'name': 'Ubuntu',
        'base': 'ubuntu-releases',
        'variants': [
            {'note': '桌面版 · x86_64', 'subdir': '{latest_dir}', 'glob': '*-desktop-amd64.iso'},
            {'note': '服务器版 · x86_64', 'subdir': '{latest_dir}', 'glob': '*-live-server-amd64.iso'},
        ],
    },
    {
        'name': 'Debian',
        'base': 'debian-cd',
        'variants': [
            {'note': '网络安装 · amd64', 'subdir': 'current/amd64/iso-cd', 'glob': 'debian-[0-9]*-netinst.iso'},
            {'note': 'DVD 完整安装 · amd64', 'subdir': 'current/amd64/iso-dvd', 'glob': 'debian-[0-9]*-DVD-1.iso'},
            {'note': 'Live GNOME · amd64', 'subdir': 'current-live/amd64/iso-hybrid', 'glob': 'debian-live-*-gnome.iso'},
            {'note': 'Live KDE · amd64', 'subdir': 'current-live/amd64/iso-hybrid', 'glob': 'debian-live-*-kde.iso'},
            {'note': 'Live XFCE · amd64', 'subdir': 'current-live/amd64/iso-hybrid', 'glob': 'debian-live-*-xfce.iso'},
            {'note': 'Live Cinnamon · amd64', 'subdir': 'current-live/amd64/iso-hybrid', 'glob': 'debian-live-*-cinnamon.iso'},
        ],
    },
    {
        'name': 'CentOS Stream',
        'base': 'centos-stream',
        'variants': [
            {'note': 'DVD 安装盘 · x86_64', 'subdir': '10-stream/BaseOS/x86_64/iso', 'glob': 'CentOS-Stream-*latest-x86_64-dvd1.iso'},
            {'note': 'DVD 安装盘 · aarch64', 'subdir': '10-stream/BaseOS/aarch64/iso', 'glob': 'CentOS-Stream-*latest-aarch64-dvd1.iso'},
        ],
    },
    {
        'name': 'Kali Linux',
        'base': 'kali-images/current',
        'variants': [
            {'note': '完整安装盘 · amd64', 'subdir': '', 'glob': 'kali-*-installer-amd64.iso'},
            {'note': '网络安装 · amd64', 'subdir': '', 'glob': 'kali-*-installer-netinst-amd64.iso'},
        ],
    },
    {
        'name': 'FreeBSD',
        'base': 'freebsd/releases/ISO-IMAGES',
        'variants': [
            {'note': '安装盘 disc1 · amd64', 'subdir': '{latest_dir}', 'glob': '*-RELEASE-amd64-disc1.iso'},
            {'note': 'DVD dvd1 · amd64', 'subdir': '{latest_dir}', 'glob': '*-RELEASE-amd64-dvd1.iso'},
            {'note': '引导盘 bootonly · amd64', 'subdir': '{latest_dir}', 'glob': '*-RELEASE-amd64-bootonly.iso'},
        ],
    },
    {
        'name': 'Arch Linux',
        'base': 'archlinux/iso/latest',
        'variants': [
            {'note': '安装盘 · x86_64', 'subdir': '', 'glob': 'archlinux-x86_64.iso'},
        ],
    },
    {
        'name': 'Gentoo',
        'base': 'gentoo/releases/amd64/autobuilds/current-install-amd64-minimal',
        'variants': [
            {'note': '最小安装盘 · amd64', 'subdir': '', 'glob': 'install-amd64-minimal-*.iso'},
        ],
    },
]

SOFTWARE_ITEMS = [
    {
        'name': 'Docker CE',
        'base': 'docker-ce',
        'variants': [
            {'note': 'macOS Intel', 'subdir': 'mac/static/stable/x86_64', 'glob': 'docker-*.tgz'},
            {'note': 'macOS Apple Silicon', 'subdir': 'mac/static/stable/aarch64', 'glob': 'docker-*.tgz'},
            {'note': 'Windows x64', 'subdir': 'win/static/stable/x86_64', 'glob': 'docker-*.zip'},
        ],
    },
]
