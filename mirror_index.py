import glob
import os
from string import Template

"""
生成镜像站主页
HEADER+section+FOOTER
section即中间表格部分
"""

HEADER = """
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
    <link rel="stylesheet" type="text/css" href="/mirror.css" media="screen" />
    <title>广东工业大学开源镜像站</title>
</head>

<body class="fade-in">

<header>
    <h1><img style="vertical-align: middle;" src="https://dl.gdutnic.com/static/wiki/网管队Logo/学校Logo.png" width="40" height="40"/>&nbsp;广东工业大学开源镜像站</h1>
</header>

<div class="container">
    <div class="col-75">
        <h2>
            <svg xmlns="http://www.w3.org/2000/svg" style="vertical-align: bottom;" x="0px" y="0px" width="28" height="28" viewBox="0 0 26 26">
                <path d="M 12.4375 0.1875 L 0 5.09375 L 0 18.53125 L 15 25.90625 L 26 18.53125 L 26 5.09375 Z M 12.46875 2.34375 L 23.6875 6.375 L 20.53125 8.0625 L 9.15625 3.65625 Z M 7.75 4.1875 L 19.34375 8.6875 L 15.59375 10.65625 L 3.4375 5.90625 Z M 2.0625 6.4375 L 15 11.5 L 15 23.5 L 14.84375 23.59375 L 2 17.28125 L 2 6.46875 Z M 22 9.5 C 22.171875 9.488281 22.273438 9.609375 22.28125 9.84375 C 22.292969 10.15625 22.101563 10.546875 21.84375 10.71875 L 19.84375 12.03125 C 19.53125 12.234375 19.261719 12.105469 19.25 11.75 C 19.238281 11.394531 19.464844 10.9375 19.78125 10.75 L 21.8125 9.5625 C 21.878906 9.523438 21.941406 9.503906 22 9.5 Z"></path>
            </svg>
            镜像列表
        </h2>
        <table id="distro-table" cellpadding="0" cellspacing="0">
            <colgroup>
                <col width="25%"/>
                <col width="25%"/>
                <col width="25%"/>
                <col width="25%"/>
            </colgroup>
            <thead>
            <tr>
                <th>💽 镜像名</th>
                <th>🔄 同步时间</th>
                <th>ℹ️ 同步状态</th>
                <th>💡 使用帮助</th>
            </tr>
            </thead>
            <tbody>

"""

SECTION_TEMPLATE = Template("""
                <tr class="${row_class}">
                    <td>💿 <a href="/${mirror_name}/">${mirror_name}</a></td>
                    <td><code>${sync_time}</code></td>
                    <td>${sync_status}</td>
                    <td>📖 <a href="/${mirror_name}.html">${mirror_name}使用帮助</a></td>
                </tr>
""")

FOOTER = """
            </tbody>
        </table>
    </div>
    <div class="col-25">
        <h2>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADQAAAA0CAYAAADFeBvrAAAACXBIWXMAAAsTAAALEwEAmpwYAAABhUlEQVR4nO2azUoDMRRGjxuLiDDizlrUl+jWF2r7WILgWheiuPKnmxEXQutCfQLFdh8JZKQMI9XJTXIrOfBtykx6D/dC0xCQowOMgDtgDpglmbtnh+5dVXSBh19I/JTSraGCjqfMopSKTo0EZKoMUMC9oNAtCpgJCtm1kmOEkxyThcgdikoeOfLIxSWPHHnk4pJHjjxycckjRx45Oa6B9wBj1TYfwKWP0LECCVPLqY/Qhjs7M0ryCGzhSQGMFchMgF1fGS1SE0mZ1FLTEDKppKYxjohjSUWRiSX1nOLwvggk9QIcxJYJJfWaUkZaSoWMlJSVOUQZRUupN40ybaVUy/xVKpiMqUWC7SW7dPujuR+qfhNAyLIJXDSs/yS8NzOxhKr/UycLa18BO8LfYWIKVfSBI2AtwNomhVBITBZSjvn3HZrVPthjdejVav9sutpy5h7UTg84b7paM/TYJWvLAHelq1RQjG9KYL1qX3fFpcqmMwhrZ1tm51DyhlWo2BpvXM3fnfkCr9lSDY7VKvsAAAAASUVORK5CYII="
                 alt="download" style="vertical-align: bottom;" width="28" height="28">
            快速下载
        </h2>
        <ul>
            <li><a href="https://mirrors.gdut.edu.cn/centos-stream/9-stream/BaseOS/x86_64/iso/CentOS-Stream-9-latest-x86_64-dvd1.iso">CentOS 9
                安装盘</a></li>
            <li><a href="https://mirrors.gdut.edu.cn/debian-cd/current/amd64/iso-cd/debian-12.8.0-amd64-netinst.iso">Debian 12 网络安装盘</a></li>
            <li><a href="https://mirrors.gdut.edu.cn/ubuntu-releases/oracular/ubuntu-24.10-desktop-amd64.iso">Ubuntu 24.10 桌面版安装盘</a></li>
        </ul>

        <h2>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAADCklEQVR4nO2Zy29NURSHP7T1KAlK4jXy+gMoOmBAQlASERETjwEDaaJmjYaYlMYIKTERvZp0RBOphBkRA2aUjqoGQq4WbSQqVZPKTtaVlZVze88+9j1Hk/sle3Jz1mOfs/dav70vVKhQIQQzgQagFegB+oFR4LeMUfntPnAO2CI2mbMKaAc+AZOe4yNwGViZReJ1wC1gIkHidvwCbgKL00r+CPAtIpE8cBs4CmyQSVbLWAJsBI7JM/kI+6/A4XImXiVv3QZ+AuwFZnn4cs82Ak8j/N2QWEGZCzw0gQaAnQF87wbeGd+9EjMIVRHJdwLzQgUAaoGuiEkE+RJ22ZynfFwwsTpCbNi0ki82iUMkpM5Umxzp0aXifgEW/evSGZB1mha1ZmN3JOmwukntIn32mGa3wse4XRm7Wp0Vz1Qel3yajNY2ruFkxT6Vx4e4ArDByIPgXdGDKmBI5bM5jlGrMnC6pRhOSY4HEHPjJZZHp3q2Jc4EepSBE2ZRzAB+BEh+UobzVYzj6rl7cSbQrwycqixGW8Av0DZFnHr17Js4ExhRBq6ZZc1SI7lLout/Ddkz2/SDkuhlMYdpOIHPymAZ03AJ9SkDdwwMXUZLlU3LJt9NrJXgyTKV0anKpuWEbxltVgZ3ylBGS5VNS863ka1XBiNyq5CllBhW+bieEIu3yugA2bE/iZhznFWGL8mO5yoPn2XHAuC7MnZ3mWnTaPaN14HGMagcbCNd5gPvVfzrvg7WmpKXtqToVvGHkxzqm8wFU5pcNGX3YBInvcqBm0xWyV9L4qTGdNk1pLPmu03yDzwvjP+yXTlxdzNRuOa2NVB1ajQbtpB84svdK+aqu8Bq4LQ411/ohTS7as8O65qUrvO64iR68wVeKWdX5VZsIIbGGZED+ClRscvlPFEjf3DUizDLGXkwKWMo6Ya1/IwpygZNs0s6xuWtLyQQj4sEGpPq1CR9otCxm412ijuctmmTLxUU5/CRJPxa9sSOGM1sHXAGuCt2eXm7E7K8+kTPt8gh5b/4m7VCBaY5fwDlENrwg3MbPQAAAABJRU5ErkJggg=="
                 alt="chat-message" style="vertical-align: bottom;" width="28" height="28">
            联系我们
        </h2>
        <ul>
            <li><strong>发送邮件</strong><br>stunic@gdut.edu.cn</li>
        </ul>

        <h2>
            <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" style="vertical-align: bottom;" width="28" height="28" viewBox="0 0 48 48">
                <path d="M 34.919922 5.4296875 C 32.954707 5.4296875 30.989736 6.1743261 29.501953 7.6621094 L 24.40625 12.757812 C 21.931571 15.232492 21.637762 18.971243 23.279297 21.890625 L 21.890625 23.279297 C 18.971116 21.637136 15.230807 21.931303 12.755859 24.40625 L 7.6601562 29.501953 C 4.6845898 32.47752 4.6845898 37.364277 7.6601562 40.339844 C 10.636337 43.314679 15.522694 43.315197 18.498047 40.339844 L 23.59375 35.244141 C 26.068697 32.769193 26.362864 29.028884 24.720703 26.109375 L 26.109375 24.720703 C 29.028937 26.361869 32.767685 26.068251 35.242188 23.59375 L 40.337891 18.498047 C 43.313457 15.52248 43.313457 10.637676 40.337891 7.6621094 C 38.850107 6.1743261 36.885137 5.4296875 34.919922 5.4296875 z M 34.919922 9.40625 C 35.853207 9.40625 36.786549 9.767018 37.509766 10.490234 C 38.956199 11.936668 38.956199 14.223488 37.509766 15.669922 L 32.414062 20.765625 C 31.504563 21.675125 30.273179 21.947057 29.117188 21.712891 L 31.785156 19.044922 A 2.0011673 2.0011673 0 1 0 28.955078 16.214844 L 26.287109 18.882812 C 26.053048 17.726809 26.325009 16.495302 27.234375 15.585938 L 32.330078 10.490234 C 33.053295 9.767018 33.986637 9.40625 34.919922 9.40625 z M 18.175781 26.150391 C 18.415361 26.150391 18.644834 26.241402 18.880859 26.289062 L 16.214844 28.955078 A 2.0011673 2.0011673 0 1 0 19.044922 31.785156 L 21.710938 29.119141 C 21.94425 30.274608 21.674498 31.505192 20.765625 32.414062 L 15.667969 37.511719 C 14.221322 38.958365 11.936101 38.956978 10.488281 37.509766 C 9.0430521 36.063267 9.0422494 33.778063 10.488281 32.332031 L 15.585938 27.234375 C 16.309154 26.511158 17.242496 26.150391 18.175781 26.150391 z"></path>
            </svg>
            相关链接
        </h2>
        <ul>
            <li><a href="http://www.gdut.edu.cn/">🏠 广东工业大学首页</a></li>
            <li><a href="help.html">❓ 使用帮助</a></li>
            <li><a href="status.html">🟢 当前状态</a></li>
        </ul>
    </div>
</div>

<div id="footer">
    🏠<a target="_blank" href="http://www.gdut.edu.cn/">广东工业大学首页</a>
    &nbsp;|&nbsp;
    ❓<a target="_blank" href="help.html">使用帮助</a>
    &nbsp;|&nbsp;
    📮<a href="mailto:stunic@gdut.edu.cn">联系我们</a>
    &nbsp;|&nbsp;
    🟢<a target="_blank" href="status.html">当前状态</a>
</div>
<script type="text/javascript" src="mirror.js"></script>
<script type="text/javascript" src="mirror.js"></script>
</body>
</html>
"""

html = HEADER
odd_or_even = 'even'

mirror_list = sorted(glob.glob('/mnt/mirror/*'))
cdn_mirror_list = ['pypi', 'centos-vault', 'anaconda', 'maven', 'npm', 'kali', 'ubuntu-ports', 'freebsd-pkg', 'docker', 'go']
ignore_dir = ['static', 'font']

for mirror in mirror_list:
    if os.path.isdir(mirror):
        mirror_name = mirror.split('/')[-1]

        # 判断目录是否要忽略
        if mirror_name in ignore_dir:
            continue

        # 判断镜像是否缓存镜像
        if mirror_name in cdn_mirror_list:  # 缓存镜像（nginx反向代理）
            sync_time = '⛔️'
            sync_status = '⏩ 缓存加速'
            is_syncing = 'false'
        else:  # 非缓存镜像（保存在服务器硬盘）
            try:
                with open('/home/mirror/sync_time/' + mirror_name, 'r') as f:
                    sync_time = "⏱️ " + f.read().strip()
            except FileNotFoundError:
                sync_time = '❌ 从未同步'
            if os.path.isfile('/tmp/mirror/lock/' + mirror_name + '.lock'):
                sync_status = '▶️ 同步中'
            else:
                sync_status = '✅ 同步完成'

        # 修改表格的class，得出黑白相间的表格
        if odd_or_even == 'even':
            row_class = 'even'
            odd_or_even = 'odd'
        else:  # odd
            row_class = 'odd'
            odd_or_even = 'even'
        if sync_status == '▶️ 同步中':
            row_class = 'syncing-row'
        # 组合成一行的HTML
        html += SECTION_TEMPLATE.substitute(row_class=row_class, mirror_name=mirror_name, sync_time=sync_time, sync_status=sync_status)

html += FOOTER

with open('/mnt/mirror/index.html', 'w') as f:
    f.write(html)
