# crontab
run python script every minute  
clear logs daily
```
40 3 * * * mv /var/log/python/ddns.log /var/log/python/ddns1.log
*/1 * * * * /usr/bin/python3 /usr/local/etc/python/ddns.py >> /var/log/python/ddns.log 2>&1
```
