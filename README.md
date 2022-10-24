# GDUT开源镜像站

http://mirrors.gdut.edu.cn/ 仅校园网可访问

![screenshot](screenshot.png)

交流群：`VVZIbnZxVHZ2Sm80T1RNM09USTVORFVLCg==`

# 架构

Nginx提供web服务。

由于服务器硬盘空间有限，所以把源分为全量镜像源和缓存源。

全量镜像使用Rsync同步。

缓存使用Nginx自带的proxy_cache模块。

# 部署文档

## 环境配置

创建名为`mirror`的用户，将存储盘挂载到`/mnt/mirror`并设置权限。切换到`mirror`用户，在家目录下执行：

```shell
git clone https://github.com/chn-lee-yumi/mirrors-gdut.git
git clone https://salsa.debian.org/mirror-team/archvsync.git  # 用于debian的同步
mkdir /home/mirror/tmp
mkdir /home/mirror/bin
mkdir /home/mirror/etc
mkdir /home/mirror/nginx_cache
cp archvsync/bin/* bin
cp mirrors-gdut/etc/ftpsync.conf etc
cp mirrors-gdut/pages/* /mnt/mirror/

cat /home/mirror/mirrors-gdut/crontab
crontab -e  # 将上面cat的内容复制粘贴进来，然后保存
```

然后坐等一两天等镜像同步完成。

## 安装Nginx

### 编译安装

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

拷贝并加载配置：

```shell
cp /home/mirror/mirrors-gdut/nginx_conf/* /usr/local/nginx/conf/
nginx -t
nginx -s reload
```

现在应该可以访问了。

### Docker镜像

暂时没找到支持nginx-module-vts模块的镜像。

```shell
docker pull nginx:latest
docker run --name nginx -p 80:80 \
  -v /home/mirror/mirrors-gdut/nginx_conf/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v /home/mirror/mirrors-gdut/nginx_conf/cache_2h.conf:/etc/nginx/cache_2h.conf:ro \
  -v /home/mirror/mirrors-gdut/nginx_conf/cache_30d.conf:/etc/nginx/cache_30d.conf:ro \
  -v /home/mirror/mirrors-gdut/nginx_conf/proxy_pass_aliyun.conf:/etc/nginx/proxy_pass_aliyun.conf:ro \
  -v /home/mirror/mirrors-gdut/nginx_conf/proxy_pass_tsinghua.conf:/etc/nginx/proxy_pass_tsinghua.conf:ro \
  -v /home/mirror/mirrors-gdut/nginx_conf/proxy_pass_ustc.conf:/etc/nginx/proxy_pass_ustc.conf:ro \
  -v /mnt/mirror:/mnt/mirror:ro -d nginx:latest
```

# 运维文档

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
|docker|缓存加速|参考 http://mirrors.ustc.edu.cn/help/dockerhub.html |需要子域名，以后发展好再考虑|
|fedora|1.13T|待google||
