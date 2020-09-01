FROM jongsx/hdf5lib:1.12.0

WORKDIR /root

RUN yum update -y \
    && yum -y install libtool \
    && git clone -b v1.5.17 https://github.com/tbeu/matio.git \
    && cd matio \
    && bash autogen.sh \
    && ./configure --with-hdf5=/opt/hdf5 --prefix=/usr/local/matio \
    && make -j 4 \
    && make install

# Exposing 22 port
EXPOSE 22
# Start ssh server
CMD ["/usr/sbin/sshd", "-D"]