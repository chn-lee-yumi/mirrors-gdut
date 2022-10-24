#!/bin/bash

fatal() {
  echo "$1"
  exit 1
}

warn() {
  echo "$1"
}

# Find a source mirror near you which supports rsync on
# https://launchpad.net/ubuntu/+cdmirrors
# rsync://<iso-country-code>.rsync.releases.ubuntu.com/releases should always work
RSYNCSOURCE=rsync://mirrors.bfsu.edu.cn/ubuntu-releases/

# Define where you want the mirror-data to be on your mirror
BASEDIR=/mnt/mirror/ubuntu-releases/

if [ ! -d ${BASEDIR} ]; then
  warn "${BASEDIR} does not exist yet, trying to create it..."
  mkdir -p ${BASEDIR} || fatal "Creation of ${BASEDIR} failed."
fi

rsync --bwlimit=10000 --verbose --recursive --times --links --safe-links --hard-links \
  --stats --delete-after --delete-excluded \
  --exclude='*-i386.iso' --exclude='12.04*' --exclude='14.0*' --exclude='precise/' --exclude='trusty/' \
  ${RSYNCSOURCE} ${BASEDIR} || fatal "Failed to rsync from ${RSYNCSOURCE}."

date -u > ${BASEDIR}/.trace/$(hostname -f)
