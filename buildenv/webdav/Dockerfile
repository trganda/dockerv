FROM httpd:2.4.58

COPY entrypoint.sh /usr/local/apache2/entrypoint.sh
RUN chmod 755 /usr/local/apache2/entrypoint.sh

ARG RUNAS_USER
ARG USER
ARG PASSWORD
ARG WEBDAV_PORT

WORKDIR /usr/local/apache2
RUN sed -i \
		-e 's/^#\(LoadModule .*mod_ssl.so\)/\1/' \
		-e 's/^#\(LoadModule .*mod_socache_shmcb.so\)/\1/' \
        -e 's/^#\(LoadModule .*mod_rewrite.so\)/\1/' \
		conf/httpd.conf

EXPOSE 8888

VOLUME ["/var/webdav"]

ENTRYPOINT ["/usr/local/apache2/entrypoint.sh"]

CMD ["httpd-foreground"]
