# ⚠️ 镜像异常反馈

> 反馈前建议先查看[镜像站状态页](https://mirrors.gdut.edu.cn/status.html)确认是否正在同步或已有故障。

## 镜像名称

（如 archlinux / pypi / docker-ce）

## 异常类型

- [ ] 同步失败 / 长期未同步
- [ ] 文件缺失（404）
- [ ] 下载速度慢 / 不稳定
- [ ] 校验失败（SHA256 不符）
- [ ] 证书 / HTTPS 错误
- [ ] 其他

## 问题描述

（发生了什么？预期是什么？请尽量给出具体报错信息）

## 复现方式

```shell
# 命令、配置或操作步骤
# 例如
curl -O https://mirrors.gdut.edu.cn/archlinux/iso/latest/archlinux-x86_64.iso
```

## 访问环境

（校园网 / VPN？访问域名（mirrors / mirrors4 / mirrors6）？你的系统与工具版本，如：校园网，mirrors6，Debian 13 + apt 2.9）

## 确认

- [x] 我已查看状态页，确认该问题未被正在进行的同步任务解释
/label ~"mirror-issue"
