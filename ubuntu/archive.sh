#!/bin/bash

fatal() {
  echo "$1"
  exit 1
}

warn() {
  echo "$1"
}

# Find a source mirror near you which supports rsync on
# https://launchpad.net/ubuntu/+archivemirrors
# rsync://<iso-country-code>.rsync.archive.ubuntu.com/ubuntu should always work
RSYNCSOURCE=rsync://mirrors.bfsu.edu.cn/ubuntu/

# Define where you want the mirror-data to be on your mirror
BASEDIR=/mnt/mirror/ubuntu/

if [ ! -d ${BASEDIR} ]; then
  warn "${BASEDIR} does not exist yet, trying to create it..."
  mkdir -p ${BASEDIR} || fatal "Creation of ${BASEDIR} failed."
fi

# 参考debian的ftpsync脚本得到ubuntu需要exclude的路径（TODO：exclude好像有点问题，*_all.deb不会删除）
rsync --bwlimit=10000 --recursive --times --links --safe-links --hard-links \
  --stats \
  --exclude "Packages*" --exclude "Sources*" \
  --exclude "Release*" --exclude "InRelease" \
  --exclude='/dists/**/binary-i386/' --exclude='/dists/**/installer-i386/' --exclude='/dists/**/Contents-i386.gz' --exclude='/pool/**/*_i386.deb' --exclude='/pool/**/*_i386.udeb' --exclude='/pool/**/*_all.deb' --exclude='/dists/**/*-i386.yml.gz' --exclude='/dists/**/*-i386.yml.xz' --exclude='/dists/**/*-i386.json.gz' --exclude='/dists/**/*-i386.xz' \
  ${RSYNCSOURCE} ${BASEDIR} || fatal "First stage of sync failed."

rsync --bwlimit=10000 --recursive --times --links --safe-links --hard-links \
  --stats --delete --delete-after \
  --exclude='/dists/**/binary-i386/' --exclude='/dists/**/installer-i386/' --exclude='/dists/**/Contents-i386.gz' --exclude='/pool/**/*_i386.deb' --exclude='/pool/**/*_i386.udeb' --exclude='/pool/**/*_all.deb' --exclude='/dists/**/*-i386.yml.gz' --exclude='/dists/**/*-i386.yml.xz' --exclude='/dists/**/*-i386.json.gz' --exclude='/dists/**/*-i386.xz' \
  ${RSYNCSOURCE} ${BASEDIR} || fatal "Second stage of sync failed."

date -u > ${BASEDIR}/project/trace/$(hostname -f)
