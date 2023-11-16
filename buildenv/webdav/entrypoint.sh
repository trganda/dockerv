#!/bin/sh

# init passwd
htpasswd -bc /usr/local/apache2/webdav.password ${USER} ${PASSWORD}

chown root:www-data /usr/local/apache2/webdav.password
chmod 640 /usr/local/apache2/webdav.password

# create webdav folder
mkdir -p /var/webdav
chown www-data:www-data -R /var/webdav

# Add our dav location to the httpd config
cat <<EOF > /usr/local/apache2/conf/extra/webdav.conf
LoadModule	dav_module           modules/mod_dav.so
LoadModule  dav_fs_module        modules/mod_dav_fs.so
LoadModule  allowmethods_module  modules/mod_allowmethods.so

Listen 8888
# rewriting Destination because we're behind an SSL terminating reverse proxy
# see http://www.dscentral.in/2013/04/04/502-bad-gateway-svn-copy-reverse-proxy/
RequestHeader edit Destination ^https: http: early
<VirtualHost *:8888>
    DocumentRoot "/var/webdav/"
    ErrorLog /usr/local/apache2/logs/error.log
    CustomLog /usr/local/apache2/logs/access.log combined
    DavLockDB "/usr/local/apache2/DavLock.db"
    <Directory "/var/webdav/">
        Options +Indexes
        IndexOptions Charset=UTF-8 FancyIndexing FoldersFirst
        IndexIgnore .??* :2*
        AllowOverride None
        Order allow,deny
        allow from all
    </Directory>

    Alias / /var/webdav/
    <Location />
       DAV On
       AllowMethods HEAD GET POST CONNECT PUT DELETE OPTIONS PROPFIND PROPPATCH MKCOL COPY MOVE LOCK UNLOCK TRACE
       AuthType Basic
       AuthName ${USER}
       AuthUserFile /usr/local/apache2/webdav.password
       Require valid-user
    </Location>
</VirtualHost>
EOF

# Set the user running httpd
# if parameter $RUNAS_USER is set.
# Otherwise defaults to user daemon
if [ -n "$RUNAS_USER" ]; then
    sed -i -e "s@User daemon@User $RUNAS_USER@" ${HTTPD_PREFIX}/conf/httpd.conf
fi

# Run the command given in the Dockerfile at CMD
exec "$@"
