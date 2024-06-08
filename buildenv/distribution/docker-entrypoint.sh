#!/bin/sh
set -e

# Add password hash, unless "user.passwd" already exists (ie, bind mounted).
if [ ! -e "/auth/htpasswd" ]; then
    touch "/auth/htpasswd"
    # Only generate a password hash if both username and password given.
    if [ "x$USERNAME" != "x" ] && [ "x$PASSWORD" != "x" ]; then
        htpasswd -B -b -c /auth/htpasswd ${USERNAME} ${PASSWORD}
    fi
fi

# Generate self-signed SSL certificate.
# If SERVER_NAMES is given, use the first domain as the Common Name.
if [ ! -e /certs/cert.key ] || [ ! -e /certs/cert.crt ]; then
    openssl req -x509 -newkey rsa:2048 -days 1000 -nodes \
        -keyout /certs/cert.key -out /certs/cert.crt -subj "/CN=CN"
fi

# Run the command given in the Dockerfile at CMD
exec "$@"
