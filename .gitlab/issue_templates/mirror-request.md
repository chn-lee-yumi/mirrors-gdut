# 🪞 新增镜像请求

> 提交前请先在 <https://mirrors.gdut.edu.cn/> 与历史 Issue 中确认该镜像未被收录。

## 镜像名称

（如 Ubuntu Kylin）

## 上游地址

（rsync / http(s)，如 rsync://rsync.archive.ubuntu.com/ubuntu/）

## 收录理由与预期用途

（为什么需要它？哪些场景 / 课程 / 人群使用？）

## 期望的镜像方式

- [ ] 全量镜像（rsync 同步到本地盘）
- [ ] 缓存镜像（Nginx proxy_cache 按需回源）
- [ ] 不确定 / 由维护者评估

## 预估体积

（全量同步大约占多少磁盘空间？不确定可留空，如约 800GB）

## 确认

- [x] 我已确认该镜像目前未被收录，且没有重复的 Issue
/label ~"mirror-request"
