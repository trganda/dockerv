FROM registry:2

COPY docker-entrypoint.sh /usr/local/apache2/docker-entrypoint.sh
RUN chmod 755 /usr/local/apache2/docker-entrypoint.sh

ENTRYPOINT [ "/usr/local/apache2/docker-entrypoint.sh" ]

CMD ["serve", "/etc/docker/registry/config.yml"]