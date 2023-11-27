FROM httpd:2.4.58

WORKDIR /usr/local/apache2

COPY conf/webdav.conf conf/extra/webdav.conf

RUN set -ex; \
    mkdir -p /var/lib/webdav; \
    chown www-data:www-data -R /var/lib/webdav; \
    # Enable DAV modules.
    for i in dav dav_fs dav_lock allowmethods; do \
        sed -i -e "/^#LoadModule ${i}_module.*/s/^#//" "conf/httpd.conf"; \
    done; \
    # Make sure authentication modules are enabled.
    for i in authn_core authn_file authz_core authz_user auth_basic auth_digest; do \
        sed -i -e "/^#LoadModule ${i}_module.*/s/^#//" "conf/httpd.conf"; \
    done; \
    # Make ssl modules are enabled.
    for i in ssl socache_shmcb; do \
        sed -i -e "/^#LoadModule ${i}_module.*/s/^#//" "conf/httpd.conf"; \
    done; \
    # Make sure other modules are enabled.
    for i in alias headers mime setenvif; do \
        sed -i -e "/^#LoadModule ${i}_module.*/s/^#//" "conf/httpd.conf"; \
    done; \
    # Run httpd as "www-data" (instead of "daemon").
    for i in User Group; do \
        sed -i -e "s|^$i .*|$i www-data|" "conf/httpd.conf"; \
    done; \
    # Include enabled configs.
    printf '%s\n' "Include conf/extra/webdav.conf" \
        >> "conf/httpd.conf"; \
    # Install openssl if we need to generate a self-signed certificate.
    apt-get update && apt-get install -y openssl

EXPOSE 443

COPY docker-entrypoint.sh /usr/local/apache2/docker-entrypoint.sh
RUN chmod 755 /usr/local/apache2/docker-entrypoint.sh

ENTRYPOINT [ "/usr/local/apache2/docker-entrypoint.sh" ]

CMD [ "httpd-foreground" ]
