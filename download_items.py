# -*- coding: utf-8 -*-
"""
快速下载弹窗条目配置。

字段说明:
    name        左侧导航显示名
    category    'os' 或 'software'
    source      'disk'（全量镜像，扫 /mnt/mirror）或 'http'（缓存镜像，解析 Nginx 目录页）
    base        目录基准（disk: /mnt/mirror 下的相对路径; http: URL 路径，host 由生成脚本拼接）
    variants    变体列表，每项:
        label   变体显示名
        tag     架构/变体小标签
        glob    文件名匹配模式（支持 * 通配符）
        subdir  disk 源: 在 base 下的子目录（可含 {latest_dir} 占位符，取 sort -V 最新子目录）
                http 源: URL 子路径（可含 {latest_dir}）
"""

OS_ITEMS = [
    {
        'name': 'Ubuntu',
        'source': 'disk',
        'base': 'ubuntu-releases',
        'variants': [
            {'label': '桌面版', 'tag': 'x86_64', 'subdir': '{latest_dir}', 'glob': '*-desktop-amd64.iso'},
            {'label': '服务器版', 'tag': 'x86_64', 'subdir': '{latest_dir}', 'glob': '*-live-server-amd64.iso'},
        ],
    },
    {
        'name': 'Debian',
        'source': 'disk',
        'base': 'debian-cd/current/amd64',
        'variants': [
            {'label': '网络安装盘', 'tag': 'amd64', 'subdir': 'iso-cd', 'glob': 'debian-[0-9]*-netinst.iso'},
            {'label': 'DVD 完整盘', 'tag': 'amd64', 'subdir': 'iso-dvd', 'glob': 'debian-[0-9]*-DVD-1.iso'},
        ],
    },
    {
        'name': 'CentOS Stream',
        'source': 'http',
        'base': 'centos-stream',
        'variants': [
            {'label': 'DVD 安装盘', 'tag': 'x86_64', 'subdir': '10-stream/BaseOS/x86_64/iso', 'glob': 'CentOS-Stream-*latest-x86_64-dvd1.iso'},
            {'label': 'DVD 安装盘', 'tag': 'aarch64', 'subdir': '10-stream/BaseOS/aarch64/iso', 'glob': 'CentOS-Stream-*latest-aarch64-dvd1.iso'},
        ],
    },
    {
        'name': 'Kali Linux',
        'source': 'disk',
        'base': 'kali-images/current',
        'variants': [
            {'label': '安装盘', 'tag': 'amd64', 'subdir': '', 'glob': 'kali-*-installer-amd64.iso'},
        ],
    },
    {
        'name': 'FreeBSD',
        'source': 'disk',
        'base': 'freebsd/releases/ISO-IMAGES',
        'variants': [
            {'label': '安装盘', 'tag': 'amd64', 'subdir': '{latest_dir}', 'glob': '*-RELEASE-amd64-disc1.iso'},
        ],
    },
    {
        'name': 'Arch Linux',
        'source': 'disk',
        'base': 'archlinux/iso/latest',
        'variants': [
            {'label': '安装盘', 'tag': 'x86_64', 'subdir': '', 'glob': 'archlinux-x86_64.iso'},
        ],
    },
    {
        'name': 'Gentoo',
        'source': 'disk',
        'base': 'gentoo/releases/amd64/autobuilds/current-install-amd64-minimal',
        'variants': [
            {'label': '最小安装盘', 'tag': 'amd64', 'subdir': '', 'glob': 'install-amd64-minimal-*.iso'},
        ],
    },
]

SOFTWARE_ITEMS = [
    {
        'name': 'Docker CE',
        'source': 'http',
        'base': 'docker-ce',
        'variants': [
            {'label': 'Docker CLI', 'tag': 'macOS Intel', 'subdir': 'mac/static/stable/x86_64', 'glob': 'docker-*.tgz'},
            {'label': 'Docker CLI', 'tag': 'macOS Apple Silicon', 'subdir': 'mac/static/stable/aarch64', 'glob': 'docker-*.tgz'},
            {'label': 'Docker CLI', 'tag': 'Windows x64', 'subdir': 'win/static/stable/x86_64', 'glob': 'docker-*.zip'},
        ],
    },
]
