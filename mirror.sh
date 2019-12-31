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
# 我的多了--perms，网易的多了--timeout=10800 --partial
COMMON_OPTIONS="-rlptHhv --delete-after --delay-updates --timeout=1200 --partial --delete-excluded --ignore-errors"


usage(){
    echo Usage: $0 [mirror]
    echo Example: $0 debian
    echo Supported mirrors: archlinux archlinuxcn centos debian debian-cd elpa epel manjaro manjaro-cd ubuntu ubuntu-releases
    exit 0
}

# 判断有没有参数
if [[ -z $1 ]] ; then
    usage
fi

# 判断lock目录是否存在，不存在则创建
if [[ ! -d ${LOCK_DIR} ]]; then
    mkdir -p ${LOCK_DIR}
fi

# 判断对应镜像的lock是否存在，如不存在则创建，否则退出
LOCK_FILE=${LOCK_DIR}/$1.lock
if [[ -f ${LOCK_FILE} ]]; then
    echo "镜像还在同步，请检查rsync进程是否在运行。如没有在运行，请手动删除 ${LOCK_FILE} 文件后重试"
    exit 1
fi
touch ${LOCK_FILE}

# 更新主页同步状态
python3 /home/mirror/mirror_index.py

# 判断log目录是否存在，不存在则创建
if [[ ! -d ${LOG_DIR} ]]; then
    mkdir -p ${LOG_DIR}
fi

# 日志文件路径
LOG_FILE=${LOG_DIR}/`date "+$1.log.%Y%m%d_%H%M%S"`
echo "日志文件："${LOG_FILE}

# 执行同步命令
case $1 in
    archlinux)
        rsync ${COMMON_OPTIONS} --exclude='iso/archboot/2016.08/' --exclude='iso/archboot/2016.12/' mirrors.neusoft.edu.cn::archlinux/ /mnt/mirror/archlinux | tee ${LOG_FILE}
        ;;
    archlinuxcn)
        rsync ${COMMON_OPTIONS} mirrors.tuna.tsinghua.edu.cn::archlinuxcn/ /mnt/mirror/archlinuxcn | tee ${LOG_FILE}
        ;;
    centos)
        rsync ${COMMON_OPTIONS} --exclude='6.10/*' --exclude='aarch64/' --exclude='ppc64/' --exclude='ppc64le/' --exclude='s390x/' mirrors.tuna.tsinghua.edu.cn::centos/ /mnt/mirror/centos | tee ${LOG_FILE}
        ;;
    debian)
        ftpsync  # debian官网推荐的同步工具 /home/mirror/bin/ftpsync https://www.debian.org/mirror/ftpmirror
        ;;
    debian-cd)
        rsync ${COMMON_OPTIONS} --include='amd64/**.iso' --exclude='*.iso' mirrors.tuna.tsinghua.edu.cn::debian-cd/ /mnt/mirror/debian-cd | tee ${LOG_FILE}
        ;;
    elpa)
        rsync ${COMMON_OPTIONS} elpa.emacs-china.org::elpa/ /mnt/mirror/elpa/ | tee ${LOG_FILE}
        ;;
    epel)
        rsync ${COMMON_OPTIONS} --exclude='6/*' --exclude='aarch64/' --exclude='ppc64/' --exclude='ppc64le/' --exclude='s390x/' mirrors.tuna.tsinghua.edu.cn::epel/ /mnt/mirror/epel | tee ${LOG_FILE}
        ;;
    manjaro)
        rsync ${COMMON_OPTIONS} mirrors.ustc.edu.cn::repo/manjaro/ /mnt/mirror/manjaro/ | tee ${LOG_FILE}
        ;;
    manjaro-cd)
        rsync ${COMMON_OPTIONS} --exclude='18.1.0*/' --exclude='18.1.1*/' --exclude='18.1.2*/' --exclude='z_release_archive/' mirrors.ustc.edu.cn::repo/manjaro-cd/ /mnt/mirror/manjaro-cd/ | tee ${LOG_FILE}
        ;;
    ubuntu)
        ~/ubuntu/archive.sh | tee ${LOG_FILE}
        ;;
    ubuntu-releases)
        ~/ubuntu/release.sh | tee ${LOG_FILE}
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
date "+%Y-%m-%d %T" > ${SYNC_TIME_FILE}

# 同步完成后删除锁
rm -f ${LOCK_FILE}

# 更新主页同步状态
python3 /home/mirror/mirror_index.py

# 清空LOG_TIME*24小时前的日志
find ${LOG_DIR}/* -mtime ${LOG_TIME} -name '*log*' -delete
find ${LOG_DIR}/* -mtime ${LOG_TIME} -name 'rsync-ftpsync.*' -delete
