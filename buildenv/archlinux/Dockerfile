FROM --platform=linux/x86_64 archlinux:latest

WORKDIR /opt

RUN pacman -Syyu --noconfirm
RUN pacman -S openssh --noconfirm
# modified the passwor of root to password
RUN echo 'root:password' | chpasswd \
    && sed -i 's/#*PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config
RUN sed -i 's/AuthorizedKeysFile	.ssh\/authorized_keys/AuthorizedKeysFile	\/root\/.ssh\/authorized_keys/g' /etc/ssh/sshd_config
RUN ssh-keygen -t dsa -f /etc/ssh/ssh_host_dsa_key
RUN ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key
RUN ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key
RUN ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key

ADD ./authorized_keys.pub /root/.ssh/authorized_keys

# Exposing 22 port
EXPOSE 22
# Start ssh server
CMD ["sshd", "-D"]