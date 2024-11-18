FROM ubuntu:22.04

WORKDIR /opt

COPY ./entrypoint.sh /opt/entrypoint.sh

ENV GITBACKUP_DIR=/opt/gitbackup

VOLUME ["${GITBACKUP_DIR}"]

RUN chmod +x /opt/entrypoint.sh
RUN apt-get update \
      && apt-get install -y cron jq curl git

CMD ["/opt/entrypoint.sh"]