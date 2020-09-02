FROM centos:latest

WORKDIR /root

ENV HDFVERSION=1.12.0
ENV HDFPATH=1_12_0
ENV HDF_INSTALL_PATH=/opt/hdf5

RUN yum update -y \
    && yum groupinstall "Development Tools" -y \
    && yum install curl unzip cmake openssh-server dos2unix which -y \
    && ssh-keygen -q -t rsa -b 2048 -f /etc/ssh/ssh_host_rsa_key \
    && ssh-keygen -q -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key \
    && ssh-keygen -t dsa -f /etc/ssh/ssh_host_ed25519_key \
    && echo 'root:password' | chpasswd \
    && sed -i 's/#*PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config \
    && sed -i "s/#UsePrivilegeSeparation.*/UsePrivilegeSeparation no/g" /etc/ssh/sshd_config \
    && sed -i "s/UsePAM.*/UsePAM no/g" /etc/ssh/sshd_config

RUN curl https://hdf-wordpress-1.s3.amazonaws.com/wp-content/uploads/manual/HDF5/HDF5_$HDFPATH/source/hdf5-$HDFVERSION.zip -o hdf5-$HDFVERSION.zip \
    && unzip hdf5-$HDFVERSION.zip \
    && cd hdf5-$HDFVERSION \
    && find ./ -name "*" | xargs dos2unix \
    && bash autogen.sh \
    && ./configure --enable-cxx --prefix=$HDF_INSTALL_PATH \
    && make -j 4 \
    && make install \
    && rm -rf /root/hdf5-$HDFVERSION.zip /root/hdf5-$HDFVERSION

# Exposing 22 port
EXPOSE 22
# Start ssh server
CMD ["/usr/sbin/sshd", "-D"]
