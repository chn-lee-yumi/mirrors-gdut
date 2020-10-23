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

## Nginx编译

为了监控流量，我们加入了nginx-module-vts模块，因此需要手动编译Nginx。如果不需要此模块，可以注释`nginx.conf`中的对应配置（配置文件中写明需要nginx-module-vts的部分）。

以 CentOS 7 为例：

```shell
yum -y install gperftools pcre pcre-devel openssl openssl-devel gcc-c++ autoconf automake gd-devel libxml2 libxslt-devel perl-devel perl-ExtUtils-Embed GeoIP GeoIP-devel GeoIP-data
wget http://nginx.org/download/nginx-1.18.0.tar.gz
tar xzf nginx-1.18.0.tar.gz
cd nginx-1.18.0.tar.gz
git clone https://github.com/vozlt/nginx-module-vts.git
./configure --prefix=/usr/share/nginx --sbin-path=/usr/sbin/nginx --modules-path=/usr/lib64/nginx/modules --conf-path=/etc/nginx/nginx.conf --error-log-path=/var/log/nginx/error.log --http-log-path=/var/log/nginx/access.log --http-client-body-temp-path=/var/lib/nginx/tmp/client_body --http-proxy-temp-path=/var/lib/nginx/tmp/proxy --http-fastcgi-temp-path=/var/lib/nginx/tmp/fastcgi --http-uwsgi-temp-path=/var/lib/nginx/tmp/uwsgi --http-scgi-temp-path=/var/lib/nginx/tmp/scgi --pid-path=/run/nginx.pid --lock-path=/run/lock/subsys/nginx --user=nginx --group=nginx --with-file-aio --with-ipv6 --with-http_ssl_module --with-http_v2_module --with-http_realip_module --with-stream_ssl_preread_module --with-http_addition_module --with-http_xslt_module=dynamic --with-http_image_filter_module=dynamic --with-http_geoip_module=dynamic --with-http_sub_module --with-http_dav_module --with-http_flv_module --with-http_mp4_module --with-http_gunzip_module --with-http_gzip_static_module --with-http_auth_request_module --with-http_random_index_module --with-http_secure_link_module --with-http_degradation_module --with-http_slice_module --with-http_stub_status_module --with-http_perl_module=dynamic --with-mail=dynamic --with-mail_ssl_module --with-stream=dynamic --with-stream_ssl_module --with-stream_realip_module --with-stream_geoip_module=dynamic --with-stream_ssl_preread_module --with-google_perftools_module --add-module=nginx-module-vts --with-cc-opt='-O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector-strong --param=ssp-buffer-size=4 -grecord-gcc-switches -m64 -mtune=generic' --with-ld-opt='-Wl,-z,relro -Wl,-E' --with-pcre --with-pcre-jit --with-debug
make
make install
```

## 新增一个源的步骤

### 全量镜像源

1. 调研目标源的镜像方法（一般去官网的wiki上找），如果国外源速度太慢，可以考虑从清华镜像或中科大镜像Rysnc
2. 修改镜像脚本`mirror.sh`，新增一行同步命令
3. 新增一个以镜像源命名的html文件，即帮助页面
4. 服务器上执行脚本进行首次同步
5. 修改`crontab`，设置同步时间
6. 修改`nginx_maintenance.conf`，设置合适的备用镜像
7. 模拟用户使用，检查是否正常

### 缓存源

under construction

# New Mirror List

|镜像|预估大小|文档|备注|
|---|---|---|---|
|freebsd|600G|https://www.freebsd.org/doc/en_US.ISO8859-1/articles/hubs/mirror-howto.html ||
|freebsd-ports|534G|https://www.freebsd.org/doc/en_US.ISO8859-1/articles/hubs/mirror-howto.html ||
|lxc-images|待google|待google|如果上LXD集群，就考虑使用|
|docker|缓存加速|参考 http://mirrors.ustc.edu.cn/help/dockerhub.html |需要子域名，以后发展好再考虑|
|ros|431GB|http://wiki.ros.org/Mirrors||
|fedora|1.13T|待google||
