#!/bin/bash
# 
# setup http://go

if [ `id -u` -ne 0 ]; then
  echo 'you need root'
  exit 1
fi

# install software, use a virutalenv
sudo aptitude install apache2 sqlite3 python-pip python
pip install bottle bottle-sqlite

read -p "
The paths are important. There are a number of changes you will need
make manually should you NOT wish to install GO into /home/go. To proceed with
install to /home/go hit 'y' now. " user_answer
if [ "$user_answer" != 'y' ]; then
  exit 1
fi

# setup
cd /home/go
sqlite3 db/go.db < sql/init_db.sql
sqlite3 db/go.db < sql/redirects_trigger
sqlite3 db/go.db < sql/update_insert_trigger
chmod -R 755 db/
chown -R www-data:www-data db/

read -p "Go will be hosted at http://go.YOURDOMAIN.COM. What is your domain? " user_domain
cat > /etc/apache2/sites-available/go <<EOF
<VirtualHost *:80>
        ServerName go.$user_domain
        ServerAlias go

        WSGIDaemonProcess go user=www-data group=www-data processes=1 threads=5
        WSGIScriptAlias / /home/go/app.wsgi

    <Directory /home/go>
        WSGIProcessGroup go
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Allow from all
    </Directory>
</VirtualHost>
EOF

a2ensite go
