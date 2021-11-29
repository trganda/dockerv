FROM --platform=linux/x86_64 archlinux:latest

WORKDIR /opt

RUN pacman -Syyu -y

# Exposing 22 port
EXPOSE 22
# Start ssh server
CMD ["/usr/sbin/sshd", "-D"]