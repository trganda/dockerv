FROM jongsx/cmakenv:latest

MAINTAINER itdream "jongsx1203@gmail.com"
WORKDIR /root

ENV HDFVERSION=1_12_0

RUN apt-get update \
    && apt-get install unzip \
    && curl https://hdf-wordpress-1.s3.amazonaws.com/wp-content/uploads/manual/HDF5/HDF5_$HDFVERSION/source/hdf5-1.12.0.zip -o hdf5-$HDFVERSION.zip \
    && unzip hdf5_$HDFVERSION.zip \
    && cd hdf5_$HDFVERSION \
    && ./autogen.h \
    && ./configure --enable-cxx --prefix=/opt/hdf5 \
    && make -j 4 \
    && make install

# Exposing 22 port
EXPOSE 22
# Start ssh server
CMD ["/usr/sbin/sshd", "-D"]