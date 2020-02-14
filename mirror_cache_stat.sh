cat /tmp/mirror_auto_cache.log
echo
cd /home/mirror/nginx_cache/
du -d 1 -m
echo
pypi=$(ls -lR pypi/ | grep 'nginx nginx' | grep -v 'drw' | wc -l)
anaconda=$(ls -lR anaconda/ | grep 'nginx nginx' | grep -v 'drw' | wc -l)
kali=$(ls -lR kali/ | grep 'nginx nginx' | grep -v 'drw' | wc -l)
echo pypi: $pypi
echo anaconda: $anaconda
echo kali: $kali
echo
echo ===
echo
