import csv
import re
from datetime import datetime
from collections import Counter

# 配置
LOG_FILE = "/home/nginx/logs/access.log.1"
DAILY_CSV = f"/home/mirror/log/daily_{datetime.now().strftime('%Y%m%d')}.csv"
TOTAL_CSV = "/home/mirror/log/total.csv"

# 要过滤的IP
BLOCKED_IPS = {"222.200.96.77", "222.200.118.66", "202.116.132.68", "202.116.132.105"}

stats = Counter()

# 正则提取： GET /xxx/
pattern = re.compile(r'GET /([^/]+)/')


def parse_log():
    with open(LOG_FILE, "r") as f:
        for line in f:
            ip_match = re.match(r"^(\d+\.\d+\.\d+\.\d+)", line)
            if not ip_match:
                continue
            ip = ip_match.group(1)
            if ip in BLOCKED_IPS:
                continue

            m = pattern.search(line)
            if m:
                mirror = m.group(1)
                stats[mirror] += 1


def write_daily_csv():
    with open(DAILY_CSV, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["mirror", "count"])
        for mirror, count in stats.items():
            writer.writerow([mirror, count])


def update_total_csv():
    total = {}

    try:
        with open(TOTAL_CSV, "r") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) != 2:
                    continue
                mirror, count = row
                total[mirror] = int(count)
    except FileNotFoundError:
        pass

    for mirror, count in stats.items():
        total[mirror] = total.get(mirror, 0) + count

    with open(TOTAL_CSV, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["mirror", "count"])
        for mirror, count in sorted(total.items()):
            writer.writerow([mirror, count])


if __name__ == "__main__":
    parse_log()
    write_daily_csv()
    update_total_csv()
    print(f"统计完成：{DAILY_CSV} 和累计文件 {TOTAL_CSV}")
