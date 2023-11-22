#!/bin/sh

# init passwd
htpasswd -bc /usr/local/apache2/webdav.password ${USER} ${PASSWORD}

chown root:www-data /usr/local/apache2/webdav.password
chmod 640 /usr/local/apache2/webdav.password

# create webdav folder
mkdir -p /var/webdav
chown www-data:www-data -R /var/webdav

# Run the command given in the Dockerfile at CMD
exec "$@"
