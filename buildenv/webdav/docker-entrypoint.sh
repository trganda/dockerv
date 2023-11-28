#!/bin/sh
set -e

# Add password hash, unless "user.passwd" already exists (ie, bind mounted).
if [ ! -e "/usr/local/apache2/webdav.password" ]; then
    touch "/usr/local/apache2/webdav.password"
    # Only generate a password hash if both username and password given.
    if [ "x$USERNAME" != "x" ] && [ "x$PASSWORD" != "x" ]; then
        htpasswd -B -b -c /usr/local/apache2/webdav.password ${USERNAME} ${PASSWORD}
    fi
fi

# Generate self-signed SSL certificate.
# If SERVER_NAMES is given, use the first domain as the Common Name.
if [ ! -e /usr/local/apache2/conf/privkey.key ] || [ ! -e /usr/local/apache2/conf/cert.crt ]; then
    openssl req -x509 -newkey rsa:2048 -days 1000 -nodes \
        -keyout /usr/local/apache2/conf/privkey.key -out /usr/local/apache2/conf/cert.crt -subj "/CN=CN"
fi

# Create directories for Dav data and lock database.
[ ! -d "/var/lib/webdav/data" ] && mkdir -p "/var/lib/webdav/data"
chown www-data:www-data "/var/lib/webdav"

# Run the command given in the Dockerfile at CMD
exec "$@"
