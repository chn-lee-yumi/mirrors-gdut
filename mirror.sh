#!/usr/bin/env bash
PATH=/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/mirror/.local/bin:/home/mirror/bin
LOCK_DIR=/tmp/mirror/lock
SYNC_TIME_DIR=/home/mirror/sync_time
LOG_DIR=/home/mirror/log
LOG_TIME=3

#COMMON_OPTIONS="--recursive \
#       -D \
#       --links \
#       --hard-links \
#       --times \
#       --delay-updates \
#       --delete-after \
#       --verbose --progress \
#       --timeout=10800 \
#       --partial \
#"
COMMON_OPTIONS="-rlptHhv --delete-delay --delay-updates --timeout=1200 --partial --delete-excluded --ignore-errors --bwlimit=10000" # 限速100Mbps

usage() {
  cat <<EOF
Usage: $0 [mirror]
Example: $0 debian
Supported mirrors: archlinux archlinuxcn centos debian debian-cd
                   elpa epel freebsd gentoo kali-images manjaro manjaro-cd
                   raspberrypi raspbian termux ubuntu ubuntu-releases
EOF
  exit 0
}

# 判断有没有参数
if [[ -z $1 ]]; then
  usage
fi

# 判断lock目录是否存在，不存在则创建
if [[ ! -d ${LOCK_DIR} ]]; then
  mkdir -p ${LOCK_DIR}
fi

# 判断对应镜像的lock是否存在，如不存在则创建，否则退出  TODO：kill掉卡死的rsync进程
LOCK_FILE=${LOCK_DIR}/$1.lock
if [[ -f ${LOCK_FILE} ]]; then
  echo "镜像还在同步，请检查rsync进程是否在运行。如没有在运行，请手动删除 ${LOCK_FILE} 文件后重试"
  exit 1
fi
touch ${LOCK_FILE}

# 更新主页同步状态
python3 /home/mirror/mirrors-gdut/mirror_index.py

# 判断log目录是否存在，不存在则创建
if [[ ! -d ${LOG_DIR} ]]; then
  mkdir -p ${LOG_DIR}
fi

# 日志文件路径
LOG_FILE=${LOG_DIR}/$(date "+$1.log.%Y%m%d_%H%M%S")
echo "日志文件："${LOG_FILE}

# 执行同步命令
case $1 in
archlinux)
  # 上游：中科大镜像
  rsync ${COMMON_OPTIONS} rsync.mirrors.ustc.edu.cn::archlinux /mnt/mirror/archlinux | tee ${LOG_FILE}
  ;;
archlinuxcn)
  # 上游：中科大镜像
  rsync ${COMMON_OPTIONS} rsync.mirrors.ustc.edu.cn::archlinuxcn /mnt/mirror/archlinuxcn | tee ${LOG_FILE}
  ;;
centos)
  # 上游：北京外国语镜像
  rsync ${COMMON_OPTIONS} --exclude='6.10/*' --exclude='aarch64/' --exclude='ppc64/' --exclude='ppc64le/' --exclude='s390x/' mirrors.bfsu.edu.cn::centos /mnt/mirror/centos | tee ${LOG_FILE}
  ;;
debian)
  # 上游：清华镜像
  ftpsync # debian官网推荐的同步工具 /home/mirror/bin/ftpsync https://www.debian.org/mirror/ftpmirror
  ;;
debian-cd)
  # 上游：北京外国语镜像
  rsync ${COMMON_OPTIONS} --include='amd64/**.iso' --exclude='*.iso' --exclude='source/tar/**' mirrors.bfsu.edu.cn::debian-cd /mnt/mirror/debian-cd | tee ${LOG_FILE}
  ;;
docker-ce)
  # 上游：清华镜像
  rsync ${COMMON_OPTIONS} --exclude='linux/fedora/' --exclude='linux/raspbian/' --exclude='linux/rhel/' mirrors.tuna.tsinghua.edu.cn::docker-ce /mnt/mirror/docker-ce/ | tee ${LOG_FILE}
  ;;
elpa)
  # 上游：elpa.emacs-china.org
  rsync ${COMMON_OPTIONS} elpa.emacs-china.org::elpa /mnt/mirror/elpa/ | tee ${LOG_FILE}
  ;;
epel)
  # 上游：清华镜像
  rsync ${COMMON_OPTIONS} --exclude='6/*' --exclude='SRPMS/' --exclude='aarch64/' --exclude='ppc64/' --exclude='ppc64le/' --exclude='s390x/' mirrors.tuna.tsinghua.edu.cn::epel /mnt/mirror/epel | tee ${LOG_FILE}
  ;;
freebsd)
  # 上游：ftp2.jp.FreeBSD.org
  # 官方文档 https://www.freebsd.org/doc/en_US.ISO8859-1/articles/hubs/mirror-howto.html
  # 可选源：{ftp,ftp2,ftp6,ftp7}.jp.FreeBSD.org
  rsync ${COMMON_OPTIONS} --exclude='/snapshots' --exclude='/development' --exclude='arm/' --exclude='arm64/' --exclude='aarch64/' --exclude='i386/' --exclude='powerpc/' --exclude='sparc64/' --exclude='**/11.2*/' --exclude='11.3*/' --exclude='11.4*/' --exclude='12.0*/' --exclude='12.1*/' --exclude='*BETA*/' --exclude='**/*arm*' --exclude='**/*i386*' --exclude='**/*powerpc*' --exclude='**/*sparc64*' ftp2.jp.FreeBSD.org::pub/FreeBSD/ /mnt/mirror/freebsd/ | tee ${LOG_FILE}
  ;;
gentoo)
  # 上游：masterdistfiles.gentoo.org
  # 官方文档 https://wiki.gentoo.org/wiki/Project:Infrastructure/Mirrors/Source
  rsync ${COMMON_OPTIONS} --exclude='/releases/historical' --exclude='/distfiles/**' --exclude='**/alpha' --exclude='**/bsd' --exclude='**/hppa' --exclude='**/ia64' --exclude='**/m68k' --exclude='**/mips' --exclude='**/ppc' --exclude='**/prefix' --exclude='**/s390' --exclude='**/sh' --exclude='**/sparc' masterdistfiles.gentoo.org::gentoo /mnt/mirror/gentoo | tee ${LOG_FILE}
  ;;
kali-images)
  # 上游：清华镜像
  rsync ${COMMON_OPTIONS} --include='*amd64.iso' --exclude='*.iso' mirrors.tuna.tsinghua.edu.cn::kali-images /mnt/mirror/kali-images | tee ${LOG_FILE}
  ;;
kubernetes)
  # 上游：清华镜像
  rsync ${COMMON_OPTIONS} mirrors.tuna.tsinghua.edu.cn::kubernetes /mnt/mirror/kubernetes/ | tee ${LOG_FILE}
  ;;
manjaro)
  # 上游：中科大镜像
  rsync ${COMMON_OPTIONS} rsync.mirrors.ustc.edu.cn::repo/manjaro/ /mnt/mirror/manjaro/ | tee ${LOG_FILE}
  ;;
manjaro-cd)
  # 上游：中科大镜像
  rsync ${COMMON_OPTIONS} --exclude='z_release_archive/' rsync.mirrors.ustc.edu.cn::repo/manjaro-cd/ /mnt/mirror/manjaro-cd/ | tee ${LOG_FILE}
  ;;
raspberrypi)
  # 上游：apt-repo.raspberrypi.org
  # 仅支持ipv6，详见 http://archive.raspberrypi.org/README.txt
  rsync ${COMMON_OPTIONS} --exclude='/html' apt-repo.raspberrypi.org::archive /mnt/mirror/raspberrypi | tee ${LOG_FILE}
  ;;
raspbian)
  # 上游：archive.raspbian.org
  # 采用官方脚本，文档见 http://www.raspbian.org/RaspbianMirrors
  # cd /mnt/mirror/raspbian/
  # python3 -u ~/raspbmirror.py --sourcepool /mnt/mirror/debian/pool --cleanup | tee ${LOG_FILE}
  # 官方脚本有bug，改用rsync
  rsync ${COMMON_OPTIONS} archive.raspbian.org::archive /mnt/mirror/raspbian | tee ${LOG_FILE}
  ;;
termux)
  # 上游：清华镜像
  rsync ${COMMON_OPTIONS} mirrors.tuna.tsinghua.edu.cn::termux /mnt/mirror/termux | tee ${LOG_FILE}
  # termux默认是termux-packages-24
  ln -s /mnt/mirror/termux/termux-packages-24/dist /mnt/mirror/termux/dist
  ;;
ubuntu)
  # 上游：北京外国语镜像
  ~/mirrors-gdut/ubuntu/archive.sh | tee ${LOG_FILE}
  ;;
ubuntu-releases)
  # 上游：北京外国语镜像
  ~/mirrors-gdut/ubuntu/release.sh | tee ${LOG_FILE}
  ;;
*)
  usage
  ;;
esac

# 判断rsync_time目录是否存在，不存在则创建
if [[ ! -d ${SYNC_TIME_DIR} ]]; then
  mkdir -p ${SYNC_TIME_DIR}
fi

# 更新同步时间
SYNC_TIME_FILE=${SYNC_TIME_DIR}/$1
date "+%Y-%m-%d %T" >${SYNC_TIME_FILE}

# 同步完成后删除锁
rm -f ${LOCK_FILE}

# 更新主页同步状态
python3 /home/mirror/mirrors-gdut/mirror_index.py

# 清空LOG_TIME*24小时前的日志
find ${LOG_DIR}/* -mtime +${LOG_TIME} -name '*log*' -delete
find ${LOG_DIR}/* -mtime +${LOG_TIME} -name 'rsync-ftpsync.*' -delete