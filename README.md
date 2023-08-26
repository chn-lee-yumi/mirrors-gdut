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
mkdir /home/mirror/nexus
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
docker run --name nginx -p 80:80 --restart always \
  -v /home/mirror/mirrors-gdut/nginx_conf/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v /home/mirror/mirrors-gdut/nginx_conf/cache_2h.conf:/etc/nginx/cache_2h.conf:ro \
  -v /home/mirror/mirrors-gdut/nginx_conf/cache_30d.conf:/etc/nginx/cache_30d.conf:ro \
  -v /home/mirror/mirrors-gdut/nginx_conf/proxy_pass_aliyun.conf:/etc/nginx/proxy_pass_aliyun.conf:ro \
  -v /home/mirror/mirrors-gdut/nginx_conf/proxy_pass_tsinghua.conf:/etc/nginx/proxy_pass_tsinghua.conf:ro \
  -v /home/mirror/mirrors-gdut/nginx_conf/proxy_pass_ustc.conf:/etc/nginx/proxy_pass_ustc.conf:ro \
  -v /mnt/mirror:/mnt/mirror:ro -d nginx:latest
```

## Nexus安装

**使用docker：**

```bash
docker pull sonatype/nexus3
docker run -d -p 8081:8081 --restart always -v /home/mirror/nexus:/nexus-data --name nexus sonatype/nexus3
```

**使用Kubernetes：**

可以参考如下文件：

[nexus_k8s_deploy_chart.yaml](nexus_k8s_deploy_chart.yaml)

## Harbor安装

> 由于 Harbor 需要使用一个独立的域名，因此我们申请了一个新的域名 `registry.gdut.edu.cn` 专门用于 Harbor 镜像缓存

**使用docker：**

### 0. 预先准备

Docker，DockerCompose，wget，curl 需要先自行安装

### 1. 下载安装包并配置

下载harbor 安装包

```bash
wget -c https://github.com/goharbor/harbor/releases/download/v2.8.0/harbor-offline-installer-v2.8.0.tgz
tar xvf harbor-offline-installer-v2.7.0.tgz  -C /harbor && cd /harbor
cp harbor.yml.tmpl harbor.yml && gedit harbor.yml
```

配置 `harbor.yml` 文件

```yaml
...
#配置harbor服务节点的域名(注意域名要符合规范，否则在docker中会无法解析为地址)
hostname: registry.gdut.edu.cn
#配置http访问的端口，可以自定义配置。
http
  port: 80 　　
https
  port: 443　
  #https访问时的证书路径
  certificate: ...
  #访问时证书私钥路径
  private_key: ...
...
#通过http访问web页面的密码，用户名默认 admin。
harbor_admin_password: Harbor12345 　　
#harbor 数据库的密码。
database
  password: Harbor12345
...
#harbor 数据存放的路径。
data_volume: /home/harbor
...　
```

### 2. 生成证书（如果是通过http访问，则不需要生成证书，但是配置文件harbor.yml中需要把https的相关配置注释掉，当然你也可以直接使用公共证书）

生成 CA 证书秘钥：`ca.key`

```bash
mkdir cert && cd cert
openssl genrsa -out ca.key 4096
```

生成 CA 证书：`ca.crt`

```bash
openssl req -x509 -new -nodes -sha512 -days 3650 \
 -subj "/C=CN/ST=Beijing/L=Beijing/O=example/OU=Personal/CN=registry.gdut.edu.cn" \
 -key ca.key \
 -out ca.crt
```
生成服务器证书秘钥：`registry.gdut.edu.cn.key`

```bash
openssl genrsa -out registry.gdut.edu.cn.key 4096
```

生成服务器证书签名：`registry.gdut.edu.cn.csr`

```bash
openssl req -sha512 -new \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=example/OU=Personal/CN=registry.gdut.edu.cn" \
    -key registry.gdut.edu.cn.key \
    -out registry.gdut.edu.cn.csr
```

生成　x509 v3 扩展文件：`v3.ext`

> 进行ssl验证的主机地址和域名必须在下面的alt_names中设置，否则主机无法通过认证

```bash
cat > v3.ext <<-EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1=registry.gdut
DNS.2=registry.gdut.edu.cn
DNS.3=registry.gdut.edu.cn
EOF
```

使用 `v3.ext` 文件为Harbor主机生成证书：`registry.gdut.edu.cn.crt`

```bash
openssl x509 -req -sha512 -days 3650 \
    -extfile v3.ext \
    -CA ca.crt -CAkey ca.key -CAcreateserial \
    -in registry.gdut.edu.cn.csr \
    -out registry.gdut.edu.cn.crt
```

### 3. 进行安装

在解压目录 `/harbor` 下执行命令进行安装

```bash
./install.sh 
```

如果使用公共证书则不需要执行以下步骤

生成docker的认证文件：将证书文件 `.crt` 转换为docker的 `.cert` 文件

```bash
openssl x509 -inform PEM -in registry.gdut.edu.cn.crt -out registry.gdut.edu.cn.cert
```

将ca证书和服务器证书文件复制到docker证书文件夹中。如果其他主机上docker需要访问harbor服务，也需要将证书文件复制到其他节点对应的docker证书文件夹中,并重新配置docker。

```bash
mkdir -p /etc/docker/certs.d
mkdir -p /etc/docker/certs.d/registry.gdut.edu.cn
cp registry.gdut.edu.cn.cert /etc/docker/certs.d/registry.gdut.edu.cn/
cp registry.gdut.edu.cn.key /etc/docker/certs.d/registry.gdut.edu.cn/
cp ca.crt /etc/docker/certs.d/registry.gdut.edu.cn/
```
 在docker的配置文件 `/etc/docker/daemon.json` 添加如下配置，然后重启docker：`systemctl restart docker`。

```json
"insecure-registries": ["registry.gdut.edu.cn"]
```

### 4. 创建harbor服务，使开机时随docker服务一起启动（可选）

在 `/etc/systemd/system/` 下创建 `harbor.service` 文件

```bash
vim /etc/systemd/system/harbor.service
```

添加下面内容

```bash
[Unit]
Description=Harbor
After=docker.service systemd-networkd.service systemd-resolved.service
Requires=docker.service
Documentation=https://github.com/goharbor/harbor

[Service]
Type=simple
Restart=on-failure
RestartSec=5
ExecStart=/usr/local/bin/docker-compose -f /harbor/docker-compose.yml up
ExecStop=/usr/local/bin/docker-compose -f /harbor/docker-compose.yml down

[Install]
WantedBy=multi-user.target
```

设置为开机启动：

```bash
chmod +x harbor.service
systemctl enable harbor.service
systemctl start harbor.service
systemctl status harbor.service
```

**使用Kubernetes：**

可以参考如下文件：

[harbor_k8s_deploy_chart.yaml](harbor_k8s_deploy_chart.yaml)

## Harbor 镜像代理配置

|名称|目标URL|提供者|配额|备注|
|---|---|---|---|---|
|docker|https://hub.docker.com|Docker Hub|20G|DockerHub镜像源|
|aliyun|https://3mk4y2c6.mirror.aliyuncs.com|Docker Registry|20G|阿里云 Docker 镜像加速|
|ghcr.io|https://ghcr.io|Docker Registry|20G|GitHub Container Registry|
|quay.io|https://quay.io|Quay|20G|RedHat Quay.io|
|mcr.microsoft.com|https://mcr.dockerproxy.com|Docker Registry|20G|Microsoft Artifact Registry|
|gcr.io|https://gcr.dockerproxy.com|Docker Registry|20G|Google Container Registry|
|k8s.gcr.io|https://k8s.dockerproxy.com|Docker Registry|20G|Google Container Registry for Kubernetes|

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
|docker|缓存加速|参考 https://github.com/goharbor/harbor |已经拿到新的域名，可以开始部署|
|fedora|1.13T|待google||

