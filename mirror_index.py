import glob
from string import Template
import os

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

<body>

<!--<h1>广东工业大学开源镜像站</h1> -->
<header>
    <!--<h1 class="fade-in">广东工业大学开源镜像站</h1>-->
    <h1 class="fade-in"><img src="https://dl.gdutnic.com/static/wiki/网管队Logo/学校Logo.png" width="35" height="35"/>&nbsp;广东工业大学开源镜像站</h1>
</header>

<table id="distro-table" cellpadding="0" cellspacing="0" class="fade-in">
    <colgroup>
        <col width="25%"/>
        <col width="25%"/>
        <col width="25%"/>
        <col width="25%"/>
    </colgroup>
    <thead>
        <tr>
            <th>💽镜像名</th>
            <th>🔄同步时间</th>
            <th>ℹ️同步状态</th>
            <th>💡使用帮助</th>
        </tr>
    </thead>
    <tbody>
"""

SECTION_TEMPLATE = Template("""
        <tr class="${odd_or_even}">
            <td>💿 <a href="/${mirror_name}/">${mirror_name}/</a></td>
            <td><code>${sync_time}</code></td>
            <td>${sync_status}</td>
            <td>📖 <a href="/${mirror_name}.html">${mirror_name}使用帮助</a></td>
        </tr>
""")

FOOTER = """
    </tbody>
</table>
<!--<p>根据相关法律法规，本站不对欧盟用户提供服务。<p>-->
<div id="footer" class="fade-in" >
    🏠<a target="_blank" href="http://www.gdut.edu.cn/">广东工业大学首页</a>
    &nbsp;|&nbsp;
    ❓<a target="_blank" href="help.html">使用帮助</a>
    &nbsp;|&nbsp;
    📮<a href="mailto:stunic@gdut.edu.cn">联系我们</a>
    &nbsp;|&nbsp;
    🟢<a target="_blank" href="status.html">当前状态</a>
</div>
<script type="text/javascript" src="mirror.js"></script>
</body>
</html>
"""

html = HEADER
odd_or_even = 'odd'
is_syncing = 'false'

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
            sync_status = '⏩️缓存加速'
            is_syncing = 'false'
        else:  # 非缓存镜像（保存在服务器硬盘）
            try:
                with open('/home/mirror/sync_time/' + mirror_name, 'r') as f:
                    sync_time = "⏱️ " + f.read().strip()
            except FileNotFoundError:
                sync_time = '❌ 从未同步'
                is_syncing = 'false'
            if os.path.isfile('/tmp/mirror/lock/' + mirror_name + '.lock'):
                sync_status = '▶️同步中'
                is_syncing = 'true'
            else:
                sync_status = '✅同步完成'
                is_syncing = 'true'

        if sync_status == '▶️同步中':
            odd_or_even = 'syncing-row'

        # 组合成一行的HTML
        html += SECTION_TEMPLATE.substitute(odd_or_even=odd_or_even, mirror_name=mirror_name, sync_time=sync_time, sync_status=sync_status)
        # 修改表格的class，得出黑白相间的表格
        if odd_or_even == 'odd':
            odd_or_even = 'even'
        else:
            odd_or_even = 'odd'

html += FOOTER

with open('/mnt/mirror/index.html', 'w') as f:
    f.write(html)
