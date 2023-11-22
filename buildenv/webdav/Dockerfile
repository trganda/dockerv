FROM httpd:2.4.58

COPY entrypoint.sh /usr/local/apache2/entrypoint.sh
RUN chmod 755 /usr/local/apache2/entrypoint.sh

ARG RUNAS_USER
ARG USER
ARG PASSWORD
ARG WEBDAV_PORT

WORKDIR /usr/local/apache2

ENTRYPOINT ["/usr/local/apache2/entrypoint.sh"]

CMD ["httpd-foreground"]
