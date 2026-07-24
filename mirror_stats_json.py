#!/usr/bin/env python3
"""聚合镜像站统计数据，输出 JSON 供 status.html 前端消费。"""

import csv
import glob
import json
import os
import subprocess
import sys
import time
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


def log(msg):
    print('[%s] %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg), flush=True)


def du_dir_map(path, timeout=120):
    result = {}
    log('du_dir_map: 开始批量扫描 %s' % path)
    start = time.time()
    try:
        proc = subprocess.run(
            ['du', '-b', '--max-depth=1', path],
            capture_output=True, text=True, timeout=timeout
        )
        elapsed = time.time() - start
        lines = [l for l in proc.stdout.strip().split('\n') if l]
        log('du_dir_map: %s 完成，耗时 %.1fs，returncode=%d，stdout %d 行，stderr %d 行' %
            (path, elapsed, proc.returncode, len(lines), len(proc.stderr.strip().split('\n'))))
        if proc.stderr.strip():
            for line in proc.stderr.strip().split('\n')[:5]:
                log('du_dir_map: stderr: %s' % line)
        for line in lines:
            parts = line.split('\t')
            if len(parts) == 2:
                name = os.path.basename(parts[1])
                if name and name != os.path.basename(path):
                    try:
                        result[name] = int(parts[0])
                    except ValueError:
                        log('du_dir_map: 跳过无法解析的行: %s' % line)
        log('du_dir_map: %s 解析出 %d 个子目录' % (path, len(result)))
    except subprocess.TimeoutExpired:
        log('du_dir_map: %s 超时（%ds）' % (path, timeout))
    return result


def du_single(path, timeout=600):
    start = time.time()
    try:
        proc = subprocess.run(
            ['du', '-sbL', path],
            capture_output=True, text=True, timeout=timeout
        )
        elapsed = time.time() - start
        if proc.stdout.strip():
            bytes_size = int(proc.stdout.split()[0])
            gb = round(bytes_size / (1024 ** 3), 1)
            log('  du %s: %.1f GB (%.1fs)' % (os.path.basename(path), gb, elapsed))
            return gb
        log('  du %s: 无输出 (%.1fs)' % (os.path.basename(path), elapsed))
    except subprocess.TimeoutExpired:
        log('  du %s: 超时（%ds）' % (os.path.basename(path), timeout))
    except (ValueError, IndexError):
        log('  du %s: 解析失败' % os.path.basename(path))
    return None


def read_csv_stats():
    total = {}
    daily = {}

    total_path = os.path.join(LOG_DIR, 'total.csv')
    try:
        with open(total_path, 'r') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) == 2:
                    try:
                        total[row[0]] = int(row[1])
                    except ValueError:
                        pass
        log('read_csv_stats: 读取 %s，%d 条记录' % (total_path, len(total)))
    except (FileNotFoundError, StopIteration):
        log('read_csv_stats: %s 不存在或为空' % total_path)

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
        log('read_csv_stats: 读取 %s，%d 条记录' % (daily_csv, len(daily)))
    except (FileNotFoundError, StopIteration):
        log('read_csv_stats: %s 不存在或为空' % daily_csv)

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
    log('==== 镜像统计开始 ====')
    overall_start = time.time()

    total_stats, daily_stats = read_csv_stats()
    cache_disk = du_dir_map(CACHE_DIR)

    log('开始逐个扫描全量镜像目录（-L 跟随符号链接）')
    mirrors = []
    skipped = 0
    for mirror_path in sorted(glob.glob(os.path.join(MIRROR_DIR, '*'))):
        if not os.path.isdir(mirror_path):
            continue

        mirror_name = os.path.basename(mirror_path)
        if mirror_name in IGNORE_DIR:
            skipped += 1
            continue

        is_cache = mirror_name in CDN_MIRROR_LIST
        is_proxy = mirror_name in PROXY_MIRRORS

        if is_proxy:
            disk_usage = None
        elif is_cache:
            cache_name = CACHE_DIR_MAP.get(mirror_name, mirror_name)
            disk_bytes = cache_disk.get(cache_name)
            disk_usage = round(disk_bytes / (1024 ** 3), 1) if disk_bytes else None
        else:
            disk_usage = du_single(mirror_path)

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

    elapsed = time.time() - overall_start
    log('==== 统计完成：%d 个镜像（跳过 %d），总耗时 %.1fs，输出到 %s ====' %
        (len(mirrors), skipped, elapsed, OUTPUT_FILE))


if __name__ == '__main__':
    main()
