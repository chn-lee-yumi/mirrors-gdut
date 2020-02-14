import os

file_cache = 0
xfs_inode_cache = 0
dentry_cache = 0

with open('/proc/meminfo', 'r') as f:
    for line in f.readlines():
        if line.find('(file)') > 0:
            file_cache += int(line.split()[1])  # kB

slap_info = os.popen("slabtop -o | grep -E 'xfs_inode|dentry'").read().split('\n')
for line in slap_info:
    if line.find('xfs_inode') > 0:
        xfs_inode_cache = int(line.split()[-2][:-1])  # KB
    elif line.find('dentry') > 0:
        dentry_cache = int(line.split()[-2][:-1])  # KB

print("文件缓存： %.1fMB" % (file_cache / 1024))
print("inode缓存： %.1fMB" % (xfs_inode_cache / 1024))
print("目录项缓存： %.1fMB" % (dentry_cache / 1024))
