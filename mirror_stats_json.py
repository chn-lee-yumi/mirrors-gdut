#!/usr/bin/env python3
"""聚合镜像站统计数据，输出 JSON 供 status.html 前端消费。"""

import csv
import glob
import json
import os
import subprocess
from datetime import datetime

MIRROR_DIR = '/mnt/mirror'
CACHE_DIR = '/home/mirror/nginx_cache'
SYNC_TIME_DIR = '/home/mirror/sync_time'
LOCK_DIR = '/tmp/mirror/lock'
LOG_DIR = '/home/mirror/log'
OUTPUT_FILE = '/mnt/mirror/mirror_stats.json'

CDN_MIRROR_LIST = {
    'pypi', 'centos-stream', 'centos-vault', 'anaconda', 'anolis',
    'crates.io-index', 'maven', 'npm', 'kali', 'ubuntu-ports',
    'freebsd-pkg', 'docker', 'go', 'openwrt', 'opensuse', 'fedora',
    'rubygems'
}

PROXY_MIRRORS = {'docker', 'maven', 'npm', 'go', 'crates.io-index'}

IGNORE_DIR = {
    'static', 'font', 'help', 'Nginx-Fancyindex-Theme',
    'certs', 'git', 'scripts', 'ubuntu-cloud-images'
}

CACHE_DIR_MAP = {
    'homebrew-bottles': 'homebrew_bottles',
}


def get_disk_usage_gb(path):
    try:
        result = subprocess.run(
            ['du', '-sb', path],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            bytes_size = int(result.stdout.split()[0])
            return round(bytes_size / (1024 ** 3), 1)
    except (subprocess.TimeoutExpired, ValueError, IndexError):
        pass
    return None


def read_csv_stats():
    total = {}
    daily = {}

    try:
        with open(os.path.join(LOG_DIR, 'total.csv'), 'r') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) == 2:
                    try:
                        total[row[0]] = int(row[1])
                    except ValueError:
                        pass
    except (FileNotFoundError, StopIteration):
        pass

    daily_csv = os.path.join(LOG_DIR, 'daily_%s.csv' % datetime.now().strftime('%Y%m%d'))
    try:
        with open(daily_csv, 'r') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) == 2:
                    try:
                        daily[row[0]] = int(row[1])
                    except ValueError:
                        pass
    except (FileNotFoundError, StopIteration):
        pass

    return total, daily


def get_sync_info(mirror_name, is_cache):
    if is_cache:
        return None, 'cache'

    sync_time_file = os.path.join(SYNC_TIME_DIR, mirror_name)
    lock_file = os.path.join(LOCK_DIR, mirror_name + '.lock')

    try:
        with open(sync_time_file, 'r') as f:
            sync_time = f.read().strip()
    except FileNotFoundError:
        return None, 'never'

    if os.path.isfile(lock_file):
        return sync_time, 'syncing'

    return sync_time, 'completed'


def main():
    total_stats, daily_stats = read_csv_stats()

    mirrors = []
    for mirror_path in sorted(glob.glob(os.path.join(MIRROR_DIR, '*'))):
        if not os.path.isdir(mirror_path):
            continue

        mirror_name = os.path.basename(mirror_path)
        if mirror_name in IGNORE_DIR:
            continue

        is_cache = mirror_name in CDN_MIRROR_LIST
        is_proxy = mirror_name in PROXY_MIRRORS

        if is_proxy:
            disk_usage = None
        elif is_cache:
            cache_name = CACHE_DIR_MAP.get(mirror_name, mirror_name)
            disk_usage = get_disk_usage_gb(os.path.join(CACHE_DIR, cache_name))
        else:
            disk_usage = get_disk_usage_gb(mirror_path)

        sync_time, sync_status = get_sync_info(mirror_name, is_cache)

        if is_proxy:
            mirror_type = 'proxy'
        elif is_cache:
            mirror_type = 'cache'
        else:
            mirror_type = 'full'

        mirrors.append({
            'name': mirror_name,
            'disk_usage_gb': disk_usage,
            'total_requests': total_stats.get(mirror_name, 0),
            'daily_requests': daily_stats.get(mirror_name, 0),
            'type': mirror_type,
            'sync_time': sync_time,
            'sync_status': sync_status,
        })

    output = {
        'generated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'mirrors': mirrors,
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print('统计完成：%d 个镜像，输出到 %s' % (len(mirrors), OUTPUT_FILE))


if __name__ == '__main__':
    main()
