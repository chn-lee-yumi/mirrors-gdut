"""
自动缓存预热脚本
由于清华源每天三点多才出log，所以这个脚本由crontab在凌晨4点执行，crontab里面一定要先cd到/home/mirror/tmp/
思路：下载清华镜像站的log，然后统计出热门的URL，预先进行下载
提取后缀名：cat tmp_mirror_log_full_pypi.log | awk '{print $7}' | grep -Po '[^.]*$' | grep -v / | sort | uniq -c | sort -n
TODO: 可能会卡死，需要修复这个问题
"""

import requests
from datetime import date, timedelta
import time
import os
import sys

# SPEED_LIMITED = '600M'  # 回源带宽限速，避免打爆回源带宽，具体速度需要实测（1M=1MB/s=8Mbps）TODO:缓存过的限速没有意义
# MIN_DOWNLOAD_TIMES = 50  # 最小下载次数，达到这个次数的文件将被预热 已禁用，不同源不同热度

date = (date.today() + timedelta(days=-2)).strftime("%Y%m%d")
print("获取的日志日期：%s" % date)
sys.stdout.flush()

log_servers = ['https://mirrors.tuna.tsinghua.edu.cn/logs/nanomirrors/', 'https://mirrors.tuna.tsinghua.edu.cn/logs/neomirrors/']
pypi_gz_name = 'pypi.log-%s.gz' % date
mirrors_gz_name = 'mirrors.log-%s.gz' % date


# 下载文件
def download_gz_file(url, save_path):
    req = requests.get(url)
    if req.status_code == 200:
        with open('tmp_mirror_logfile.gz', "wb")as f:
            f.write(req.content)
        os.system('gunzip tmp_mirror_logfile.gz && mv tmp_mirror_logfile %s' % save_path)
        return True
    else:
        return False


# 下载两台服务器的日志并汇总
start_time = time.time()

print("下载日志……")
sys.stdout.flush()
tmp_log_path = 'tmp_mirror_log.log'
pypi_full_log = 'tmp_mirror_log_full_pypi.log'
mirrors_full_log = 'tmp_mirror_log_full_mirrors.log'
for server in log_servers:
    # pypi
    url = server + pypi_gz_name
    if download_gz_file(url, tmp_log_path):
        os.system('cat %s >> %s' % (tmp_log_path, pypi_full_log))
        os.system('rm %s' % tmp_log_path)
    # mirrors
    url = server + mirrors_gz_name
    if download_gz_file(url, tmp_log_path):
        os.system('cat %s >> %s' % (tmp_log_path, mirrors_full_log))
        os.system('rm %s' % tmp_log_path)

end_time = time.time()
cost_time = int(end_time - start_time)
print("下载用时: %.2f hours" % (cost_time / 60 / 60))
sys.stdout.flush()

# 得到访问量大于MIN_DOWNLOAD_TIMES的url
start_time = time.time()

print("计算访问量……")
sys.stdout.flush()
# pypi
pypi_heat_url = os.popen("cat %s | awk '{print $7}' | grep -E '\.whl$|\.gz$|\.egg$' | sort | uniq -c | awk '{if($1>=%s) print $2}'" % (pypi_full_log, 50)).read()
pypi_heat_url = pypi_heat_url.strip().split('\n')
print("pypi链接数：%d" % len(pypi_heat_url))
# anaconda
anaconda_heat_url = os.popen(
    "cat %s | grep 'GET /anaconda/' | awk '{print $7}' | grep -E '\.json$|\.exe$|\.bz2$|\.conda$|\.sh$|\.pkg$' | sort | uniq -c | awk '{if($1>=%s) print $2}'" % (mirrors_full_log, 100)).read()
anaconda_heat_url = anaconda_heat_url.strip().split('\n')
print("anaconda链接数：%d" % len(anaconda_heat_url))
# kali
kali_heat_url = os.popen(
    "cat %s | grep 'GET /kali/' | awk '{print $7}' | grep -E '\.deb$|\.gz$' | sort | uniq -c | awk '{if($1>=%s) print $2}'" % (mirrors_full_log, 10)).read()
kali_heat_url = kali_heat_url.strip().split('\n')
print("kail链接数：%d" % len(kali_heat_url))
# ubuntu-ports
ubuntu_ports_heat_url = os.popen(
    "cat %s | grep 'GET /ubuntu-ports/' | awk '{print $7}' | grep -E '\.deb$|\.gz$' | sort | uniq -c | awk '{if($1>=%s) print $2}'" % (mirrors_full_log, 10)).read()
ubuntu_ports_heat_url = ubuntu_ports_heat_url.strip().split('\n')
print("ubuntu-ports链接数：%d" % len(ubuntu_ports_heat_url))
# gentoo
gentoo_heat_url = os.popen(
    "cat %s | grep 'GET /gentoo/distfiles/' | awk '{print $7}' | sort | uniq -c | awk '{if($1>=%s) print $2}'" % (mirrors_full_log, 10)).read()
gentoo_heat_url = gentoo_heat_url.strip().split('\n')
print("gentoo链接数：%d" % len(gentoo_heat_url))

end_time = time.time()
cost_time = int(end_time - start_time)
print("计算用时: %.2f hours" % (cost_time / 60 / 60))
sys.stdout.flush()

# 单线程下载
print("正在预热……")
sys.stdout.flush()
# pypi
start_time = time.time()
for url in pypi_heat_url:
    os.system('curl -I http://mirrors.gdut.edu.cn/pypi%s -o/dev/null 2>/dev/null' % url)
end_time = time.time()
cost_time = int(end_time - start_time)
print("pypi预热用时: %.2f hours" % (cost_time / 60 / 60))
sys.stdout.flush()
# anaconda
start_time = time.time()
for url in anaconda_heat_url:
    os.system('curl -I http://mirrors.gdut.edu.cn%s -o/dev/null 2>/dev/null' % url)
end_time = time.time()
cost_time = int(end_time - start_time)
print("anaconda预热用时: %.2f hours" % (cost_time / 60 / 60))
sys.stdout.flush()
# kali
start_time = time.time()
for url in kali_heat_url:
    os.system('curl -I http://mirrors.gdut.edu.cn%s -o/dev/null 2>/dev/null' % url)
end_time = time.time()
cost_time = int(end_time - start_time)
print("kali预热用时: %.2f hours" % (cost_time / 60 / 60))
# ubuntu-ports
start_time = time.time()
for url in ubuntu_ports_heat_url:
    os.system('curl -I http://mirrors.gdut.edu.cn%s -o/dev/null 2>/dev/null' % url)
end_time = time.time()
cost_time = int(end_time - start_time)
print("ubuntu-ports预热用时: %.2f hours" % (cost_time / 60 / 60))
sys.stdout.flush()
# gentoo
start_time = time.time()
for url in gentoo_heat_url:
    os.system('curl -I http://mirrors.gdut.edu.cn%s -o/dev/null 2>/dev/null' % url)
end_time = time.time()
cost_time = int(end_time - start_time)
print("gentoo预热用时: %.2f hours" % (cost_time / 60 / 60))
sys.stdout.flush()

# 删除垃圾
print("清理临时文件……")
sys.stdout.flush()
os.remove(pypi_full_log)
os.remove(mirrors_full_log)


print("预热完毕！")

"""
统计下载次数大于等于5的文件的总大小（GB）：
cat mirrors.log-20191016 | grep 'GET /anaconda/' | awk '{print $7,$10}' | sort | uniq -c | sort -nr | awk '{if($1>=5) sum += $3};END {print sum/1024/1024/1024}'
45.3612GB
cat pypi.log-20191016 | awk '{print $7,$10}' | sort | uniq -c | sort -nr | awk '{if($1>=5) sum += $3};END {print sum/1024/1024/1024}'
30.9936GB
----------
访问大于等于5的文件大小总和：GB
anaconda-neo-20191916 43.7859
anaconda-nano-20191916 45.3612
anaconda-20191916 45.3612
anaconda-nano-20191017 46.1559
pypi-nano-20191016 30.9936
pypi-neo-20191016 28.659
pypi-20191016 46.9584
访问大于等于10的文件大小总和：GB
anaconda-20191916 26.5517
anaconda-20191017 28.2448
pypi-nano-20191016 17.5853
pypi-neo-20191016 16.2109
pypi-20191016 28.4986
"""
