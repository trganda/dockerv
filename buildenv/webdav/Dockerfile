FROM httpd:2.4.58

COPY entrypoint.sh /usr/local/apache2/entrypoint.sh
RUN chmod 755 /usr/local/apache2/entrypoint.sh

ARG RUNAS_USER
ARG USER
ARG PASSWORD

WORKDIR /usr/local/apache2
RUN echo "Include conf/extra/webdav.conf" >> conf/httpd.conf

EXPOSE 8888

VOLUME ["/var/webdav"]

ENTRYPOINT ["/usr/local/apache2/entrypoint.sh"]

CMD ["httpd-foreground"]
