FROM ubuntu:latest

MAINTAINER itdream "jongsx1203@gmail.com"
WORKDIR /root

ENV TZ=Europe/Kiev

RUN apt-get clean \
    && apt-get update \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apt-get install cmake gdb gcc g++ autoconf git curl openssh-server -y --fix-missing \
    && mkdir /var/run/sshd \
    && echo 'root:password' | chpasswd \
    && sed -i 's/#*PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config

# Exposing 22 port
EXPOSE 22
# Start ssh server
CMD ["/usr/sbin/sshd", "-D"]