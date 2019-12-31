# GDUT开源镜像站

http://mirrors.gdut.edu.cn/ 仅校园网可访问

![screenshot](screenshot.png)

# 架构

Nginx提供web服务。

由于服务器硬盘空间有限，所以把源分为全量镜像源和缓存源。

全量镜像使用Rsync同步。

缓存使用Nginx自带的proxy_cache模块。

# 文件目录说明

under construction

# 脚本说明

under construction

# 运维文档

under construction

# New Mirror List

|镜像|预估大小|文档|备注|
|---|---|---|---|
|kali|675GB|https://www.kali.org/docs/community/kali-linux-mirrors/ |目前采用缓存的方式，硬盘扩容后，根据热度考虑是否全量镜像|
|kali-images|172GB|https://www.kali.org/docs/community/kali-linux-mirrors/ ||
|gentoo|426G|待google||
|freebsd|600G|https://www.freebsd.org/doc/en_US.ISO8859-1/articles/hubs/mirror-howto.html ||
|freebsd-ports|534G|https://www.freebsd.org/doc/en_US.ISO8859-1/articles/hubs/mirror-howto.html ||
|raspiberry|64G|待google||
|raspbian|391G|待google||
|openwrt|74G|待google||
|lxc-images|待google|待google|如果上LXD集群，就考虑使用|
|docker|缓存加速|参考 http://mirrors.ustc.edu.cn/help/dockerhub.html |需要子域名，以后发展好再考虑|
