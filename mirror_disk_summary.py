import os
from mod_weixin import *

msg = "[磁盘统计]\n"

space_used = os.popen('cd /mnt/mirror/ && du -BG -d 1 ./ | sort -k2 | grep -v -E "^0G"').read()
msg += '===镜像占用===\n'
msg += space_used

space_used = os.popen('cd /home/mirror/nginx_cache/ && du -BM -d 1 ./ | sort -k2').read()
msg += '===缓存占用===\n'
msg += space_used

df = os.popen('df -h | grep -E "home|mirror"').read()
msg += '===磁盘使用===\n'
msg += df

msg = msg.strip()
print(msg)
refresh_token()
send_msg(msg)
