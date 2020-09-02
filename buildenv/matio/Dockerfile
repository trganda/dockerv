FROM jongsx/hdf5lib:1.12.0

WORKDIR /root

RUN yum update -y \
    && yum -y install libtool \
    && git clone -b v1.5.17 https://github.com/tbeu/matio.git \
    && cd matio \
    && bash autogen.sh \
    && ./configure --with-hdf5=/usr/local/hdf5 --prefix=/usr/local/matio \
    && make -j 4 \
    && make install \
    && rm -rf /root/matio
    && ssh-keygen -q -t rsa -b 2048 -f /etc/ssh/ssh_host_rsa_key -y \
    && ssh-keygen -q -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -y \
    && ssh-keygen -t dsa -f /etc/ssh/ssh_host_ed25519_key -y \
    && echo 'root:password' | chpasswd \
    && sed -i 's/#*PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config \
    && sed -i "s/#UsePrivilegeSeparation.*/UsePrivilegeSeparation no/g" /etc/ssh/sshd_config \
    && sed -i "s/UsePAM.*/UsePAM no/g" /etc/ssh/sshd_config

# Exposing 22 port
EXPOSE 22
# Start ssh server
CMD ["/usr/sbin/sshd", "-D"]
