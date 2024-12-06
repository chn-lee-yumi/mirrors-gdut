import glob
import os
from string import Template

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
    <h1><img style="vertical-align: middle;" src="/GDUT_Logo.png" width="40" height="40"/>&nbsp;广东工业大学开源镜像站</h1>
</header>

<div class="container">
    <div class="col-25">
        <ul class="nav">

"""

NAVIGATION_TEMPLATE = Template("""
            <li class="nav-item">
                <a href="/help/${mirror}.html" class="nav-link ${selected}">${mirror}</a>
            </li>
""")

FOOTER = Template("""
        </ul>
    </div>
    <div class="col-75">
        <h2>${mirror}镜像使用帮助</h2>
${html}
    </div>
</div>

<div id="footer">
    🏠<a target="_blank" href="http://www.gdut.edu.cn/">广东工业大学首页</a>
    &nbsp;|&nbsp;
    ❓<a target="_blank" href="about.html">关于我们</a>
    &nbsp;|&nbsp;
    📮<a href="mailto:stunic@gdut.edu.cn">联系我们</a>
    &nbsp;|&nbsp;
    🟢<a target="_blank" href="status.html">当前状态</a>
</div>
<script type="text/javascript" src="mirror.js"></script>
</body>
</html>
""")

mirror_list = sorted(glob.glob('/mnt/mirror/*'))
ignore_dir = ['static', 'font', 'help']

if not os.path.exists('/mnt/mirror/help'):
    os.makedirs('/mnt/mirror/help')  # 创建文件夹

mirror_names = []

for mirror in mirror_list:
    if os.path.isdir(mirror):
        mirror_name = mirror.split('/')[-1]

        # 判断目录是否要忽略
        if mirror_name in ignore_dir:
            continue

        mirror_names.append(mirror_name)

for mirror in mirror_names:
    html = HEADER
    for m in mirror_names:
        if m == mirror:
            selected = "nav-link-selected"
        else:
            selected = ""
        html += NAVIGATION_TEMPLATE.substitute(mirror=m, selected=selected)

    try:
        with open(f'help_pages_template/{mirror}.html', 'r') as f:
            html += FOOTER.substitute(mirror=mirror, html=f.read())
    except FileNotFoundError:
        html += FOOTER.substitute(mirror=mirror, html="<p>该镜像的帮助文档正在编写中……</p>")
    with open(f'/mnt/mirror/help/{mirror}.html', 'w') as f:
        f.write(html)
