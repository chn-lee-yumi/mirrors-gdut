import glob
import os
import re
from mod_weixin import *

location_info = [
    ('数据中心(97段)', '222.200.97.'),
    ('数据中心(98段)', '222.200.98.'),
    ('数据中心(118段)', '222.200.118.'),
    ('数据中心(132段)', '202.116.132.'),
    ('值班室(99段)', '222.200.99.'),
    ('大学城教工宿舍', '10.11.'),
    ('工一', '10.21.23.'),  # 掩码具体不知,10.21
    ('大学城学生宿舍', '10.30.'),
    ('龙洞学生宿舍', '10.31.'),
    ('龙洞无线', '10.34.'),
    ('大学城无线', '10.37.'),
]

ACCESS_LOG = '/home/nginx/logs/access.log'


def is_ip(str):
    p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    if p.match(str):
        return True
    else:
        return False


def check_ip_location(ip):
    for location in location_info:
        if ip.find(location[1]) == 0:
            return location[0]
    print('[INFO] 未知ip：%s' % ip)
    return '未知'


summary = {}
mirror_list = sorted(glob.glob('/mnt/mirror/*'))
msg = "[每日统计]\n"

# 计算发行版热度
msg += '===热度统计===\n'
for mirror in mirror_list:
    if os.path.isdir(mirror):
        mirror_name = mirror.split('/')[-1]
        summary[mirror_name] = {}

        # 流量计算
        # traffic = os.popen("cat /var/log/nginx/access.log | grep " + mirror_name + "/ | awk '{sum+=$10} END {print sum}'").read().strip()
        traffic = 0
        with open(ACCESS_LOG, 'r')as f:
            for line in f.readlines():
                if line.find(mirror_name + "/") > 0:
                    line_tmp = line.split()
                    if line_tmp[0] == '222.200.97.228':
                        continue
                    traffic += int(line_tmp[9])
        summary[mirror_name]['traffic'] = traffic / 1024 / 1024

        # 用户量计算
        # users = os.popen("cat /var/log/nginx/access.log | grep  " + mirror_name + "/ | awk '{print $1}' | sort -u | wc -l").read().strip()
        user_list = set()
        with open(ACCESS_LOG, 'r')as f:
            for line in f.readlines():
                if line.find(mirror_name + "/") > 0:
                    line_tmp = line.split()
                    if line_tmp[-1] == '"-"':  # 没有使用代理
                        if line_tmp[0] == '222.200.97.228':
                            continue
                        user_list.add(line_tmp[0])
                    else:  # 使用了代理
                        user_ip = line_tmp[-1].strip('"').split(',')[-1].strip()
                        if is_ip(user_ip):
                            user_list.add(user_ip)
        summary[mirror_name]['users'] = len(user_list)

        # 总结文字
        msg += mirror_name + ': %s人 %.2fMB\n' % (summary[mirror_name]['users'], summary[mirror_name]['traffic'])

# 计算总人数（ip）
msg += '===用户分布===\n'
# user_ip_list = os.popen("cat /var/log/nginx/access.log | awk '{print $1}' | sort -u").read().strip().split()
user_ip_list = set()
with open(ACCESS_LOG, 'r') as f:
    for line in f.readlines():
        line_tmp = line.split()
        if line_tmp[-1] == '"-"':  # 没有使用代理
            if line_tmp[0] == '222.200.97.228':
                continue
            user_ip_list.add(line_tmp[0])
        else:  # 使用了代理
            user_ip = line_tmp[-1].strip('"').split(',')[-1]
            if is_ip(user_ip):
                user_list.add(user_ip)
user_total = len(user_ip_list)
msg += '总人数：%d\n' % user_total

# 统计用户（ip）分布
location_count = {}
for user_ip in user_ip_list:
    if user_ip == '222.200.97.228':
        continue
    # 统计一个ip属于哪个区域
    location = check_ip_location(user_ip)
    if location not in location_count:
        location_count[location] = 0
    location_count[location] += 1
for location in location_count:
    msg += '%s：%d人\n' % (location, location_count[location])

# # 计算目录空间
# space_used = os.popen('cd /mnt/mirror/ && du -BG -d 1 ./ | sort -k2').read()
# msg += '===磁盘占用===\n'
# msg += space_used
#
# # 计算缓存空间
# space_used = os.popen('cd /home/mirror/nginx_cache/ && du -BM -d 1 ./ | sort -k2').read()
# msg += '===缓存占用===\n'
# msg += space_used

msg = msg.strip()
print(msg)
refresh_token()
send_msg(msg)
