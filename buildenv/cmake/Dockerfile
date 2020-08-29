FROM ubuntu:latest

MAINTAINER itdream "jongsx1203@gmail.com"
WORKDIR /root

ENV TZ=Europe/Kiev
# Modified source to aliyun
RUN sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list \
    && apt-get clean \
    && apt-get update \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apt-get install cmake gcc g++ autoconf git curl openssh-server -y --fix-missing \
    && mkdir /var/run/sshd \
    && echo 'root:password' | chpasswd \
    && sed -i 's/#*PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config

# Exposing 8443 port
EXPOSE 22
# Start ssh server
CMD ["/usr/sbin/sshd", "-D"]