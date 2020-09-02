FROM jongsx/cmakenv:latest

WORKDIR /root

ENV HDFVERSION=1.12.0
ENV HDFPATH=1_12_0
ENV HDF_INSTALL_PATH=/opt/hdf5

RUN apt-get clean \
    && apt-get update \
    && apt-get install tofrodos -y \
    && curl https://hdf-wordpress-1.s3.amazonaws.com/wp-content/uploads/manual/HDF5/HDF5_$HDFPATH/source/hdf5-$HDFVERSION.zip -o hdf5-$HDFVERSION.zip \
    && unzip hdf5-$HDFVERSION.zip \
    && cd hdf5-$HDFVERSION \
    && find ./ -name "*" | xargs fromdos \
    && bash autogen.sh \
    && ./configure --enable-cxx --prefix=$HDF_INSTALL_PATH \
    && make -j 4 \
    && make install \
    && rm -rf /root/hdf5-$HDFVERSION.zip /root/hdf5-$HDFVERSION

# Exposing 22 port
EXPOSE 22
# Start ssh server
CMD ["/usr/sbin/sshd", "-D"]
